"""BrailleBridge desktop relay — owns the ESP32 Bluetooth Low Energy (BLE)
and USB Serial connections and streams their data into the embedded web UI.

Bluetooth is the PRIMARY transport: the relay scans for multiple BrailleBridge
devices advertising the Nordic UART Service (NUS) and can connect to multiple
student devices simultaneously. Serial COM ports are fully supported as a
secondary/hardware transport.

Every character typed on any device is forwarded once; multiple consumers
(student view, teacher mode, exam mode) can subscribe without fighting over
the physical connection.
"""
import asyncio
import codecs
import json
import os
import threading
import time
from datetime import datetime

import serial
from serial.tools import list_ports

try:
    from bleak import BleakScanner, BleakClient
    BLEAK_AVAILABLE = True
except ImportError:
    BLEAK_AVAILABLE = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
DATA_DIR = os.path.join(BASE_DIR, 'data')
ASSIGN_FILE = os.path.join(DATA_DIR, 'assignments.json')

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
NUS_TX_UUID      = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"  # ESP32 → Host (notify)
NUS_RX_UUID      = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # Host → ESP32 (write)


class BleManager:
    """Manages concurrent Bluetooth Low Energy connections using Bleak."""

    def __init__(self, relay):
        self.relay = relay
        self.discovered = {}   # address -> info dict
        self._lock = threading.Lock()
        self._loop = None
        self._thread = None
        self._scanning = False
        self._scanner = None

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

    def scan_devices(self):
        """Asynchronously discover BLE devices advertising BrailleBridge or NUS."""
        if not BLEAK_AVAILABLE or not self._loop:
            return []

        async def _scan():
            try:
                devices = await BleakScanner.discover(timeout=2.0)
                found = []
                for d in devices:
                    name = d.name or ''
                    # Match name contains 'braille' or advertises NUS service
                    uuids = [str(u).lower() for u in (d.metadata.get('uuids') or [])] if d.metadata else []
                    is_braille = ('braille' in name.lower()) or (NUS_SERVICE_UUID.lower() in uuids)

                    # We include any device with a BrailleBridge identity or explicit name
                    if is_braille or ('bridge' in name.lower()):
                        addr = d.address
                        display_name = name if name else f"BrailleBridge ({addr[-8:]})"
                        info = {
                            'name': f"BLE:{addr}",
                            'label': f"{display_name} (Bluetooth)",
                            'type': 'bluetooth',
                            'address': addr,
                            'description': f"Bluetooth LE — {addr}",
                            'is_braille': True
                        }
                        found.append(info)
                        with self._lock:
                            self.discovered[f"BLE:{addr}"] = info
                return found
            except Exception:
                return []

        res = self.run_coro(_scan(), timeout=4.0)
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
                await client.connect(timeout=8.0)
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

                # Start notification on Nordic UART TX characteristic
                await client.start_notify(NUS_TX_UUID, on_notify)

                with conn['lock']:
                    conn['client'] = client
                    conn['decoder'] = decoder

                self.relay.emit('open', port_name, None)
                return True
            except Exception:
                return False

        res = self.run_coro(_connect(), timeout=12.0)
        return bool(res)

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

    def scan_bluetooth(self):
        """Trigger an active BLE scan for new BrailleBridge devices."""
        return self.ble.scan_devices()

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
            # Connect via Bluetooth Low Energy
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
            chars = conn['chars']
            conn['chars'] = []
        os.makedirs(LOGS_DIR, exist_ok=True)
        clean_port = port_name.replace('\\', '').replace(':', '_').replace('-', '_')
        name = conn['name'] or clean_port
        stamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        path = os.path.join(LOGS_DIR, f'{name}_{stamp}.log')
        lines = self._wrap(chars)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f'BrailleBridge Session Log — Device {port_name}\n')
            f.write(f'Saved: {datetime.now().isoformat(timespec="seconds")}\n')
            f.write('=' * 50 + '\n\n')
            for ts_str, text in lines:
                f.write(f'[{ts_str}] {text}\n')
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
                flush_word()
                flush_line()
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
                if ch and ch != '\r':
                    conn['chars'].append((now, ch))

    # ------------------------------------------------------------ monitor loop
    def _monitor_loop(self):
        """Auto-detect plugged USB devices and scan for nearby Bluetooth devices."""
        last_dev_names = None
        cycle = 0
        while not self._monitor_stop.is_set():
            try:
                # Periodic active BLE scan every 2 cycles (6 seconds)
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
                    # Serial auto-reconnect
                    if not c.get('is_ble'):
                        if not c.get('serial') or not c['serial'].is_open:
                            if name in port_names:
                                self.open_port(name, c.get('baud', 115200))
                                self.emit('reconnect', name, None)
                    # BLE auto-reconnect
                    else:
                        if not c.get('client') or not c['client'].is_connected:
                            if name in port_names:
                                self.open_port(name, c.get('baud', 115200))
                                self.emit('reconnect', name, None)
            except Exception:
                pass
            self._monitor_stop.wait(SCAN_INTERVAL)
