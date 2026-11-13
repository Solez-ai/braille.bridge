"""BrailleBridge desktop relay — owns the ESP32 Bluetooth Low Energy (BLE)
and USB Serial connections and streams their data into the native Python UI.

Bluetooth is the PRIMARY transport: the relay scans for multiple BrailleBridge
devices advertising the Nordic UART Service (NUS) as well as paired/connected
Windows BLE devices, and can connect to multiple student devices simultaneously.
Serial COM ports are fully supported as a secondary/hardware transport.

Every character typed on any device is forwarded once; multiple consumers
(student view, teacher mode, learner mode) can subscribe without fighting over
the physical connection.
"""
import asyncio
import codecs
import json
import os
import re
import threading
import time
from datetime import datetime

import serial
from serial.tools import list_ports

try:
    from bleak import BleakScanner, BleakClient
    from bleak.exc import BleakBluetoothNotAvailableError
    BLEAK_AVAILABLE = True
except ImportError:
    BLEAK_AVAILABLE = False
    BleakBluetoothNotAvailableError = Exception

try:
    from winrt.windows.devices.bluetooth import BluetoothLEDevice, BluetoothConnectionStatus
    from winrt.windows.devices.enumeration import DeviceInformation
    WINRT_BLE_AVAILABLE = True
except ImportError:
    WINRT_BLE_AVAILABLE = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
DATA_DIR = os.path.join(BASE_DIR, 'data')
ASSIGN_FILE = os.path.join(DATA_DIR, 'assignments.json')
STUDENT_LOGS_FILE = os.path.join(DATA_DIR, 'student_logs.json')
ROSTER_FILE = os.path.join(DATA_DIR, 'roster.json')

SCAN_INTERVAL = 3.0   # seconds between device re-scan / reconnect attempts
READ_SIZE = 256
CONTROL_PREFIXES = ('SYSTEM:', 'LANG:', 'Invalid', 'SHIFT')

# ESP32 ROM boot preamble — printed to serial on every reset BEFORE the
# firmware runs. Not user text; drop it so it never pollutes output or logs.
BOOT_PREFIXES = ('ets ', 'rst:0x', 'boot:0x', 'configSPIWP', 'clk_drv:',
                 'q_drv:', 'd_drv:', 'cs0_drv:', 'hd_drv:', 'wp_drv:',
                 'mode:DIO', 'load:0x', 'entry 0x')

# Nordic UART Service (NUS) UUIDs used by BrailleBridge firmware
NUS_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
NUS_TX_UUID      = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"  # ESP32 -> Host (notify)
NUS_RX_UUID      = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # Host -> ESP32 (write)


class SmartFormatter:
    """Organizes raw character streams into words, sentences, and conditionally
    formatted document blocks (Title, Section Heading, Question, Answer, Math,
    Callout, Bullet/Numbered List, and Prose Paragraphs)."""

    @staticmethod
    def extract_text_and_time(chars):
        """Convert raw char stream (strings, (ts, ch) tuples, or {'char', 'time'} dicts)
        into clean logical lines without breaking on single-char packet newlines."""
        if not chars:
            return [], None

        first_time = None
        raw_items = []
        for entry in chars:
            if isinstance(entry, tuple) and len(entry) >= 2:
                ts, ch = entry[0], entry[1]
            elif isinstance(entry, dict):
                ch = entry.get('char', '')
                ts = entry.get('time')
            else:
                ch = str(entry)
                ts = None

            if ts is not None and first_time is None:
                first_time = ts
            if ch is None:
                continue
            raw_items.append((ts, str(ch)))

        # Reconstruct continuous text: treat single \n between single letters as empty/space
        # unless there is an explicit double newline \n\n.
        buf = []
        n = len(raw_items)
        i = 0
        while i < n:
            ts, ch = raw_items[i]
            if ch == '\r':
                i += 1
                continue
            if ch == '\n':
                # Check if consecutive newlines -> paragraph break
                if i + 1 < n and raw_items[i + 1][1] in ('\n', '\r'):
                    buf.append('\n')
                    while i + 1 < n and raw_items[i + 1][1] in ('\n', '\r'):
                        i += 1
                else:
                    # Single newline from println() firmware: ignore if surrounded by single chars,
                    # otherwise treat as space if preceded by multi-char line
                    prev_ch = buf[-1] if buf else ''
                    if prev_ch and prev_ch not in (' ', '\n'):
                        # Look behind: if the user never typed spaces at all, don't insert spaces between every letter;
                        # only preserve explicit '\n' if the stream contains multi-char chunks.
                        pass
                i += 1
                continue
            buf.append(ch)
            i += 1

        full_text = ''.join(buf).replace('\u00a0', ' ')
        lines = [ln.strip() for ln in full_text.split('\n') if ln.strip()]
        return lines, first_time

    @staticmethod
    def fix_punctuation(text: str) -> str:
        t = text.replace('\u00a0', ' ')
        t = re.sub(r' +([.,;:!?।])', r'\1', t)
        t = re.sub(r'([.,;:!?।])(?=[^\s\d.,;:!?।])', r'\1 ', t)
        t = re.sub(r'\.{4,}', '...', t)
        t = re.sub(r' {2,}', ' ', t)
        return t.strip()

    @staticmethod
    def heading_level(text: str) -> int:
        t = text.strip()
        if re.match(r'^(chapter|অধ্যায়|unit|part)\b', t, re.I):
            return 1
        if re.match(r'^(section|অনুচ্ছেদ|topic)\b', t, re.I):
            return 2
        if re.match(r'^(lesson|পাঠ)\b', t, re.I):
            return 3
        if re.match(r'^(exercise|অনুশীলন)\b', t, re.I):
            return 4
        return 0

    @staticmethod
    def classify_sentence(s: str) -> str:
        t = s.strip()
        if not t:
            return 'para'
        if re.match(r'^(q:|question\b|প্রশ্ন\b)', t, re.I) or t.endswith('?'):
            return 'question'
        if re.match(r'^(a:|ans:|answer\b|উত্তর\b)', t, re.I):
            return 'answer'
        if re.search(r'\d+\s*[+\-×÷=]\s*\d+', t) or (
            any(op in t for op in ('+', '×', '÷', '=')) and re.search(r'\d', t)
        ):
            return 'math'
        if re.match(r'^(note:|important:|remember:|warning:|বিঃদ্রঃ)', t, re.I) or t.endswith('!'):
            return 'callout'
        return 'para'

    @classmethod
    def format_blocks(cls, chars):
        """Turn raw character stream into smartly organized, conditionally formatted blocks.
        Returns list of dicts: {'type', 'text', 'time', 'level', 'badge'}."""
        lines, first_time = cls.extract_text_and_time(chars)
        if not lines:
            return []

        ts_ms = int(time.time() * 1000)
        if isinstance(first_time, (int, float)):
            ts_ms = int(first_time if first_time > 1e11 else first_time * 1000)
        elif isinstance(first_time, datetime):
            ts_ms = int(first_time.timestamp() * 1000)

        blocks = []
        for idx, raw_line in enumerate(lines):
            line = cls.fix_punctuation(raw_line)
            if not line:
                continue

            # 1. Check bullet or numbered list
            if re.match(r'^[-*•·→]\s+', line):
                clean = cls.fix_punctuation(re.sub(r'^[-*•·→]\s+', '', line))
                blocks.append({'type': 'bullet', 'text': clean, 'time': ts_ms, 'level': 0, 'badge': 'LIST'})
                continue
            if re.match(r'^\d+[.)]\s+', line):
                clean = cls.fix_punctuation(re.sub(r'^\d+[.)]\s+', '', line))
                blocks.append({'type': 'numbered', 'text': clean, 'time': ts_ms, 'level': 0, 'badge': 'STEP'})
                continue

            # 2. Check heading
            head = cls.heading_level(line)
            if head > 0 and len(line.split()) <= 10:
                badge = {1: 'CHAPTER', 2: 'SECTION', 3: 'LESSON', 4: 'EXERCISE'}.get(head, 'HEADING')
                blocks.append({'type': 'heading', 'text': line, 'time': ts_ms, 'level': head, 'badge': badge})
                continue

            # 3. Split line into sentences so questions, math, callouts, and prose paragraphs
            # are smartly organized!
            sentences = re.split(r'(?<=[.!?।])\s+', line)
            para_Accumulator = []

            def flush_para():
                if not para_Accumulator:
                    return
                # Group up to 3 sentences per paragraph for clean editorial readability
                for chunk_idx in range(0, len(para_Accumulator), 3):
                    chunk = para_Accumulator[chunk_idx:chunk_idx + 3]
                    joined = ' '.join(chunk)
                    blocks.append({'type': 'para', 'text': joined, 'time': ts_ms, 'level': 0, 'badge': ''})
                para_Accumulator.clear()

            for sent in sentences:
                sent = sent.strip()
                if not sent:
                    continue
                kind = cls.classify_sentence(sent)
                if kind == 'question':
                    flush_para()
                    blocks.append({'type': 'question', 'text': sent, 'time': ts_ms, 'level': 0, 'badge': 'QUESTION'})
                elif kind == 'answer':
                    flush_para()
                    blocks.append({'type': 'answer', 'text': sent, 'time': ts_ms, 'level': 0, 'badge': 'ANSWER'})
                elif kind == 'math':
                    flush_para()
                    blocks.append({'type': 'math', 'text': sent, 'time': ts_ms, 'level': 0, 'badge': 'MATH'})
                elif kind == 'callout':
                    flush_para()
                    blocks.append({'type': 'callout', 'text': sent, 'time': ts_ms, 'level': 0, 'badge': 'HIGHLIGHT'})
                else:
                    para_Accumulator.append(sent)

            flush_para()

        # Promote first short paragraph to document Title if there are multiple blocks
        if len(blocks) >= 2 and blocks[0]['type'] == 'para':
            first_txt = blocks[0]['text'].strip()
            if 0 < len(first_txt) <= 55 and len(first_txt.split()) <= 6 and not re.search(r'[.,;:!?।]$', first_txt):
                blocks[0]['type'] = 'title'
                blocks[0]['badge'] = 'DOCUMENT TITLE'

        return blocks

    @classmethod
    def to_plain_text(cls, blocks) -> str:
        out = []
        num = 0
        for b in blocks:
            btype = b.get('type', 'para')
            txt = b.get('text', '')
            if btype == 'title':
                out.extend([txt.upper(), '=' * len(txt), ''])
                num = 0
            elif btype == 'heading':
                out.extend(['', f'### {txt}', ''])
                num = 0
            elif btype == 'question':
                out.extend([f'[Question] {txt}', ''])
                num = 0
            elif btype == 'answer':
                out.extend([f'[Answer]   {txt}', ''])
                num = 0
            elif btype == 'math':
                out.extend([f'[Math]     {txt}', ''])
                num = 0
            elif btype == 'callout':
                out.extend([f'[IMPORTANT] {txt}', ''])
                num = 0
            elif btype == 'bullet':
                out.append(f'  • {txt}')
            elif btype == 'numbered':
                num += 1
                out.append(f'  {num}. {txt}')
            else:
                out.extend([txt, ''])
                num = 0
        return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'


class BleManager:
    """Manages concurrent Bluetooth Low Energy connections using Bleak + WinRT."""

    def __init__(self, relay):
        self.relay = relay
        self.discovered = {}   # address -> info dict
        self.last_error = None
        self._lock = threading.Lock()
        self._loop = None
        self._thread = None

        if BLEAK_AVAILABLE:
            self._loop = asyncio.new_event_loop()
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def run_coro(self, coro, timeout=10.0):
        if not self._loop or not self._loop.is_running():
            return None
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        try:
            return future.result(timeout=timeout)
        except Exception:
            return None

    async def _discover_winrt_paired_or_connected(self):
        """Enumerate BLE devices already paired or connected in Windows Settings
        (including devices where Windows HID took over and stopped BLE advertisements)."""
        found = []
        if not WINRT_BLE_AVAILABLE:
            return found
        try:
            selectors = [
                BluetoothLEDevice.get_device_selector_from_connection_status(
                    BluetoothConnectionStatus.CONNECTED
                ),
                BluetoothLEDevice.get_device_selector_from_pairing_state(True),
            ]
            seen_addrs = set()
            for sel in selectors:
                devs = await DeviceInformation.find_all_async_aqs_filter(sel)
                for d in devs:
                    try:
                        le = await BluetoothLEDevice.from_id_async(d.id)
                        if not le or not le.bluetooth_address:
                            continue
                        addr = ':'.join(
                            f'{(le.bluetooth_address >> (8 * i)) & 0xff:02X}'
                            for i in reversed(range(6))
                        )
                        if addr in seen_addrs:
                            continue
                        seen_addrs.add(addr)
                        name = (d.name or le.name or '').strip()
                        low = name.lower()
                        is_bb = ('braille' in low) or ('bridge' in low) or ('esp32' in low)
                        if is_bb:
                            status_lbl = (
                                "Connected in Windows"
                                if le.connection_status == BluetoothConnectionStatus.CONNECTED
                                else "Paired in Windows"
                            )
                            display_name = name if name else f"BrailleBridge ({addr[-8:]})"
                            info = {
                                'name': f"BLE:{addr}",
                                'label': f"{display_name} ({status_lbl})",
                                'type': 'bluetooth',
                                'address': addr,
                                'description': f"{display_name} — {status_lbl} [{addr}]",
                                'is_braille': True,
                            }
                            found.append(info)
                            with self._lock:
                                self.discovered[f"BLE:{addr}"] = info
                    except Exception:
                        continue
        except Exception:
            pass
        return found

    def scan_devices(self, include_all_named=False):
        """Asynchronously discover BLE devices advertising BrailleBridge or NUS,
        plus any paired/connected Windows BLE BrailleBridge devices."""
        if not BLEAK_AVAILABLE or not self._loop:
            return []

        async def _scan():
            found_map = {}

            # 1. Check Windows paired & system-connected BLE devices first
            win_devs = await self._discover_winrt_paired_or_connected()
            for item in win_devs:
                found_map[item['name']] = item

            # 2. Active BLE Advertisement Scan via Bleak (compatible with Bleak 3.x & 0.2x)
            try:
                try:
                    discovered_adv = await BleakScanner.discover(timeout=2.5, return_adv=True)
                    pairs = list(discovered_adv.values())
                except TypeError:
                    raw_devs = await BleakScanner.discover(timeout=2.5)
                    pairs = [(d, None) for d in raw_devs]

                self.last_error = None
                for d, adv in pairs:
                    name = (d.name or (adv.local_name if adv else '') or '').strip()
                    uuids = []
                    if adv and getattr(adv, 'service_uuids', None):
                        uuids = [str(u).lower() for u in adv.service_uuids]
                    elif hasattr(d, 'metadata') and d.metadata:
                        uuids = [str(u).lower() for u in (d.metadata.get('uuids') or [])]

                    low = name.lower()
                    is_braille = (
                        ('braille' in low)
                        or ('bridge' in low)
                        or ('esp32' in low)
                        or (NUS_SERVICE_UUID.lower() in uuids)
                    )
                    if is_braille or (include_all_named and name):
                        addr = d.address
                        display_name = name if name else f"BrailleBridge ({addr[-8:]})"
                        rssi = getattr(adv, 'rssi', None)
                        rssi_str = f" · {rssi} dBm" if rssi is not None else ""
                        info = {
                            'name': f"BLE:{addr}",
                            'label': f"{display_name} (Bluetooth)",
                            'type': 'bluetooth',
                            'address': addr,
                            'description': f"{display_name} — Bluetooth LE [{addr}]{rssi_str}",
                            'is_braille': is_braille,
                        }
                        found_map[f"BLE:{addr}"] = info
                        with self._lock:
                            self.discovered[f"BLE:{addr}"] = info
            except BleakBluetoothNotAvailableError:
                self.last_error = "Bluetooth radio is turned OFF in Windows Settings."
            except Exception as e:
                self.last_error = str(e)

            return list(found_map.values())

        res = self.run_coro(_scan(), timeout=6.0)
        return res or []

    def get_known_devices(self):
        with self._lock:
            return list(self.discovered.values())

    def connect(self, port_name, conn):
        """Connect to a BLE peripheral and start listening for NUS TX notifications."""
        if not BLEAK_AVAILABLE or not self._loop:
            return False

        addr = port_name[4:] if port_name.startswith('BLE:') else port_name

        async def _connect():
            try:
                def on_disconnect(client):
                    with conn['lock']:
                        conn['client'] = None
                    self.relay.emit('close', port_name, None)
                    self.relay._save_log(port_name, conn)

                client = BleakClient(addr, disconnected_callback=on_disconnect)
                await client.connect(timeout=10.0)
                if not client.is_connected:
                    return False

                decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
                buf = ''

                def on_notify(sender, data: bytearray):
                    nonlocal buf
                    text = decoder.decode(bytes(data))
                    buf += text
                    while '\n' in buf:
                        line, buf = buf.split('\n', 1)
                        self.relay._forward_line(port_name, conn, line)
                    if buf:
                        rest, buf = buf, ''
                        if rest.startswith('ets '):
                            conn['boot_suppress'] = True
                        if conn['boot_suppress'] or rest.startswith(BOOT_PREFIXES):
                            return
                        self.relay.emit('data', port_name, rest)
                        self.relay._buffer_chars(conn, rest)

                await client.start_notify(NUS_TX_UUID, on_notify)

                with conn['lock']:
                    conn['client'] = client
                    conn['decoder'] = decoder

                self.relay.emit('open', port_name, None)
                return True
            except Exception as e:
                self.last_error = str(e)
                return False

        res = self.run_coro(_connect(), timeout=14.0)
        return bool(res)

    def write_nus(self, conn, text: str):
        """Write a control command (e.g. LANG:en or LANG:bn) to NUS RX."""
        if not BLEAK_AVAILABLE or not self._loop:
            return False

        async def _write():
            client = conn.get('client')
            if client and client.is_connected:
                try:
                    await client.write_gatt_char(NUS_RX_UUID, text.encode('utf-8'))
                    return True
                except Exception:
                    return False
            return False

        return bool(self.run_coro(_write(), timeout=4.0))

    def disconnect(self, conn):
        """Disconnect Bleak client safely."""
        if not BLEAK_AVAILABLE or not self._loop:
            return

        async def _disconnect():
            client = conn.get('client')
            if client:
                try:
                    await client.stop_notify(NUS_TX_UUID)
                except Exception:
                    pass
                try:
                    await client.disconnect()
                except Exception:
                    pass

        self.run_coro(_disconnect(), timeout=4.0)

    def shutdown(self):
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)


class RelayManager:
    """Manages simultaneous Bluetooth Low Energy and Serial COM port connections."""

    def __init__(self, emit):
        self.emit = emit          # emit(kind: str, port: str|None, payload: any)
        self._conns = {}          # port -> connection dict
        self._lock = threading.Lock()
        self.ble = BleManager(self)
        self._monitor_stop = threading.Event()
        self._monitor = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor.start()

    # ------------------------------------------------------------ discovery
    def list_ports(self):
        """Enumerate both Bluetooth Low Energy devices (Priority #1) and COM ports."""
        items = []

        # 1. Bluetooth Low Energy Devices (Top Priority)
        ble_devices = self.ble.get_known_devices()
        for d in ble_devices:
            items.append({
                'name': d['name'],
                'description': d.get('description', 'Bluetooth Low Energy Device')
            })

        # 2. USB Serial COM Ports
        serial_ports = self._comports_raw()
        if not serial_ports:
            time.sleep(0.1)
            serial_ports = self._comports_raw()
        if not serial_ports:
            registry_names = self._registry_ports()
            if registry_names:
                serial_ports = [
                    {'name': n, 'description': 'COM port (Windows registry)'}
                    for n in registry_names
                ]

        for p in serial_ports:
            items.append({
                'name': p['name'],
                'description': p.get('description', 'COM port')
            })

        return items

    def scan_bluetooth(self, include_all_named=False):
        """Trigger an active BLE scan for BrailleBridge devices."""
        return self.ble.scan_devices(include_all_named=include_all_named)

    @staticmethod
    def _comports_raw():
        try:
            return [
                {'name': p.device, 'description': p.description or ''}
                for p in list_ports.comports()
            ]
        except Exception:
            return []

    @staticmethod
    def _registry_ports():
        """Windows fallback: read HKLM\\HARDWARE\\DEVICEMAP\\SERIALCOMM."""
        if os.name != 'nt':
            return []
        try:
            import winreg
        except Exception:
            return []
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r'HARDWARE\DEVICEMAP\SERIALCOMM')
            names = []
            i = 0
            while True:
                try:
                    names.append(winreg.EnumValue(key, i)[1])
                except OSError:
                    break
                i += 1
            winreg.CloseKey(key)
            return names
        except Exception:
            return []

    # ------------------------------------------------------------ lifecycle
    def open_port(self, port_name, baud=115200):
        """Open either a Bluetooth device (e.g. 'BLE:XX:XX:...') or a Serial COM port."""
        if not port_name:
            return False

        is_ble = port_name.startswith('BLE:')

        with self._lock:
            existing = self._conns.get(port_name)
            if existing:
                if is_ble and existing.get('client') and existing['client'].is_connected:
                    return True
                if not is_ble and existing.get('serial') and existing['serial'].is_open:
                    return True

        if is_ble:
            conn = {
                'is_ble': True,
                'client': None,
                'baud': int(baud),
                'chars': [],
                'name': None,
                'desired': True,
                'lock': threading.Lock(),
                'boot_suppress': False,
            }
            ok = self.ble.connect(port_name, conn)
            if ok:
                with self._lock:
                    self._conns[port_name] = conn
                return True
            return False

        # Connect via USB Serial
        try:
            ser = serial.Serial(port_name, int(baud), timeout=0.1)
        except Exception:
            return False

        conn = {
            'is_ble': False,
            'serial': ser,
            'stop': threading.Event(),
            'baud': int(baud),
            'chars': [],
            'name': None,
            'desired': True,
            'thread': None,
            'lock': threading.Lock(),
            'boot_suppress': False,
        }
        with self._lock:
            old = self._conns.get(port_name)
            if old and old.get('thread') and old['thread'].is_alive():
                old['stop'].set()
            self._conns[port_name] = conn
        conn['thread'] = threading.Thread(
            target=self._read_loop, args=(port_name, conn), daemon=True)
        conn['thread'].start()
        self.emit('open', port_name, None)
        return True

    def close_port(self, port_name):
        """Close an active Bluetooth or Serial connection cleanly."""
        with self._lock:
            conn = self._conns.get(port_name)
            if not conn:
                return True
            conn['desired'] = False
            is_ble = conn.get('is_ble', False)
            if not is_ble:
                conn['stop'].set()
                ser = conn.get('serial')

        self._save_log(port_name, conn)

        if is_ble:
            self.ble.disconnect(conn)
        else:
            try:
                if ser and ser.is_open:
                    ser.close()
            except Exception:
                pass

        with self._lock:
            self._conns.pop(port_name, None)
        self.emit('close', port_name, None)
        return True

    def set_name(self, port_name, name):
        with self._lock:
            conn = self._conns.get(port_name)
            if conn:
                with conn['lock']:
                    conn['name'] = name

    def shutdown(self):
        self._monitor_stop.set()
        for port_name in list(self._conns.keys()):
            self.close_port(port_name)
        self.ble.shutdown()

    # ------------------------------------------------------------ assignments
    def get_assignments(self):
        try:
            with open(ASSIGN_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def set_assignment(self, name, port_name):
        data = self.get_assignments()
        if not port_name:
            data.pop(name, None)
        else:
            data[name] = port_name
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(ASSIGN_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            if port_name:
                self.set_name(port_name, name)
            return True
        except Exception:
            return False

    # ------------------------------------------------------------ logging
    def save_all_logs(self):
        saved = 0
        with self._lock:
            conns = list(self._conns.items())
        for port_name, conn in conns:
            if self._save_log(port_name, conn):
                saved += 1
        return saved

    def _save_log(self, port_name, conn):
        with conn['lock']:
            if not conn['chars']:
                return None
            chars = list(conn['chars'])
            conn['chars'] = []
        os.makedirs(LOGS_DIR, exist_ok=True)
        clean_port = port_name.replace('\\', '').replace(':', '_').replace('-', '_')
        name = conn['name'] or clean_port
        stamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        path = os.path.join(LOGS_DIR, f'{name}_{stamp}.log')
        blocks = SmartFormatter.format_blocks(chars)
        plain_doc = SmartFormatter.to_plain_text(blocks)
        lines = self._wrap(chars)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f'BrailleBridge Session Log — {name} ({port_name})\n')
            f.write(f'Saved: {datetime.now().isoformat(timespec="seconds")}\n')
            f.write('=' * 50 + '\n\n')
            if plain_doc.strip():
                f.write(plain_doc + '\n')
            else:
                for ts_str, text in lines:
                    f.write(f'{text}\n')
        return path

    @staticmethod
    def _wrap(chars):
        MAX = 64
        lines = []
        words, line_len, cur, cur_ts = [], 0, '', None

        def flush_word():
            nonlocal cur, cur_ts, line_len
            if not cur:
                return
            add = len(cur) + (1 if words else 0)
            if line_len + add > MAX:
                flush_line()
            words.append((cur, cur_ts))
            line_len += add
            cur, cur_ts = '', None

        def flush_line():
            nonlocal words, line_len
            if not words:
                return
            lines.append((words[0][1].strftime('%H:%M:%S'),
                          ' '.join(w[0] for w in words)))
            words, line_len = [], 0

        for ts, ch in chars:
            if ch == ' ':
                flush_word()
            elif ch in '\n\r':
                # Ignore single-char packet newlines so words stay together
                continue
            else:
                if not cur:
                    cur_ts = ts
                cur += ch
        flush_word()
        flush_line()
        return lines

    # ------------------------------------------------------------ serial reader loop
    def _read_loop(self, port_name, conn):
        ser = conn['serial']
        decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
        buf = ''
        while not conn['stop'].is_set():
            try:
                data = ser.read(READ_SIZE)
            except Exception:
                break
            if not data:
                continue
            buf += decoder.decode(data)
            while '\n' in buf:
                line, buf = buf.split('\n', 1)
                self._forward_line(port_name, conn, line)
            if buf:
                rest, buf = buf, ''
                if rest.startswith('ets '):
                    conn['boot_suppress'] = True
                if conn['boot_suppress'] or rest.startswith(BOOT_PREFIXES):
                    continue
                self.emit('data', port_name, rest)
                self._buffer_chars(conn, rest)
        try:
            if ser.is_open:
                ser.close()
        except Exception:
            pass
        if not conn['desired']:
            return
        self._save_log(port_name, conn)
        self.emit('close', port_name, None)

    def _forward_line(self, port_name, conn, line):
        line = line.rstrip('\r')
        stripped = line.strip()
        if not stripped:
            return
        if stripped.startswith('ets '):
            conn['boot_suppress'] = True
            return
        if conn['boot_suppress']:
            if stripped.startswith('entry 0x') or stripped.startswith('SYSTEM:'):
                conn['boot_suppress'] = False
            else:
                return
        if stripped.startswith(BOOT_PREFIXES):
            return
        if stripped.startswith(CONTROL_PREFIXES):
            self.emit('data', port_name, stripped + '\n')
            return
        self.emit('data', port_name, line)
        self._buffer_chars(conn, line)

    def _buffer_chars(self, conn, text):
        now = datetime.now()
        with conn['lock']:
            for ch in text:
                if ch and ch not in ('\r', '\n'):
                    conn['chars'].append((now, ch))

    # ------------------------------------------------------------ monitor loop
    def _monitor_loop(self):
        """Auto-detect plugged USB devices and scan for nearby Bluetooth devices."""
        last_dev_names = None
        cycle = 0
        while not self._monitor_stop.is_set():
            try:
                if cycle % 2 == 0:
                    self.scan_bluetooth()
                cycle += 1

                ports = self.list_ports()
                port_names = {p['name'] for p in ports}
                if port_names != last_dev_names:
                    last_dev_names = port_names
                    self.emit('ports', None, ports)

                with self._lock:
                    wanted = [
                        (name, c)
                        for name, c in self._conns.items()
                        if c.get('desired')
                    ]

                for name, c in wanted:
                    if not c.get('is_ble'):
                        if not c.get('serial') or not c['serial'].is_open:
                            if name in port_names:
                                self.open_port(name, c.get('baud', 115200))
                                self.emit('reconnect', name, None)
                    else:
                        if not c.get('client') or not c['client'].is_connected:
                            if name in port_names:
                                self.open_port(name, c.get('baud', 115200))
                                self.emit('reconnect', name, None)
            except Exception:
                pass
            self._monitor_stop.wait(SCAN_INTERVAL)
