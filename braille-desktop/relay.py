"""BrailleBridge desktop relay — owns the ESP32 COM ports and streams their
data into the embedded web UI.

The relay is deliberately transport-agnostic: it emits (kind, port, payload)
events and lets the host (main.py) decide how to deliver them to the UI.
Every character typed on the device is forwarded once; multiple consumers
(student view, teacher mode, exam mode) can subscribe without fighting over
the physical port.
"""
import codecs
import json
import os
import threading
import time
from datetime import datetime

import serial
from serial.tools import list_ports

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
DATA_DIR = os.path.join(BASE_DIR, 'data')
ASSIGN_FILE = os.path.join(DATA_DIR, 'assignments.json')

SCAN_INTERVAL = 2.0   # seconds between port re-scan / reconnect attempts
READ_SIZE = 256
CONTROL_PREFIXES = ('SYSTEM:', 'LANG:', 'Invalid', 'SHIFT')

# ESP32 ROM boot preamble — printed to serial on every reset BEFORE the
# firmware runs. These lines are not user text; drop them so they never
# pollute the live output or the saved logs.
BOOT_PREFIXES = ('ets ', 'rst:0x', 'boot:0x', 'configSPIWP', 'clk_drv:',
                 'q_drv:', 'd_drv:', 'cs0_drv:', 'hd_drv:', 'wp_drv:',
                 'mode:DIO', 'load:0x', 'entry 0x')


class RelayManager:
    """Manages one serial connection per COM port, each with a reader thread."""

    def __init__(self, emit):
        self.emit = emit          # emit(kind: str, port: str|None, payload: any)
        self._conns = {}          # port -> connection dict
        self._lock = threading.Lock()
        self._monitor_stop = threading.Event()
        self._monitor = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor.start()

    # ------------------------------------------------------------ discovery
    def list_ports(self):
        """Enumerate COM ports. On Windows, pyserial's setupapi/WMI enumeration
        can transiently return empty even while the OS knows the port is there
        (common with WCH CH9102/CH340 devices after connect/disconnect churn).
        Retry once, then fall back to the SERIALCOMM registry so the UI never
        falsely reports '(no ports detected)'."""
        ports = self._comports_raw()
        if not ports:
            time.sleep(0.2)  # transient enumeration failures self-heal
            ports = self._comports_raw()
        if not ports:
            registry_names = self._registry_ports()
            if registry_names:
                ports = [
                    {'name': n, 'description': 'COM port (Windows registry)'}
                    for n in registry_names
                ]
        return ports

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

    # ----------------------------------------------------------- lifecycle
    def open_port(self, port_name, baud=115200):
        with self._lock:
            existing = self._conns.get(port_name)
            if existing and existing.get('serial') and existing['serial'].is_open:
                return True
        try:
            ser = serial.Serial(port_name, int(baud), timeout=0.1)
        except Exception:
            return False

        conn = {
            'serial': ser, 'stop': threading.Event(), 'baud': int(baud),
            'chars': [], 'name': None, 'desired': True, 'thread': None,
            'lock': threading.Lock(), 'boot_suppress': False,
        }
        with self._lock:
            old = self._conns.get(port_name)
            if old and old['thread'] and old['thread'].is_alive():
                old['stop'].set()
            self._conns[port_name] = conn
        conn['thread'] = threading.Thread(
            target=self._read_loop, args=(port_name, conn), daemon=True)
        conn['thread'].start()
        self.emit('open', port_name, None)
        return True

    def close_port(self, port_name):
        with self._lock:
            conn = self._conns.get(port_name)
            if not conn:
                return True
            conn['desired'] = False
            conn['stop'].set()
            ser = conn['serial']
        self._save_log(port_name, conn)
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

    # ---------------------------------------------------------- assignments
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

    # -------------------------------------------------------------- logging
    def save_all_logs(self):
        saved = 0
        with self._lock:
            conns = list(self._conns.items())
        for port_name, conn in conns:
            if self._save_log(port_name, conn):
                saved += 1
        return saved

    def _save_log(self, port_name, conn):
        # Snapshot under the connection lock so the reader thread can never
        # append mid-iteration or lose chars between snapshot and reset.
        with conn['lock']:
            if not conn['chars']:
                return None
            chars = conn['chars']
            conn['chars'] = []
        os.makedirs(LOGS_DIR, exist_ok=True)
        name = conn['name'] or port_name.replace('\\', '').replace(':', '')
        stamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        path = os.path.join(LOGS_DIR, f'{name}_{stamp}.log')
        lines = self._wrap(chars)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f'BrailleBridge Session Log — Port {port_name}\n')
            f.write(f'Saved: {datetime.now().isoformat(timespec="seconds")}\n')
            f.write('=' * 50 + '\n\n')
            for ts_str, text in lines:
                f.write(f'[{ts_str}] {text}\n')
        return path

    @staticmethod
    def _wrap(chars):
        """Group characters into readable wrapped prose lines (mirrors the
        JS buildReadableLog in braille-display). Each line keeps the timestamp
        of its first character."""
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

    # ----------------------------------------------------------- reader loop
    def _read_loop(self, port_name, conn):
        ser = conn['serial']
        # Incremental decoder: a multi-byte UTF-8 character (Bangla) split
        # across two read() calls must decode correctly, not become garbage.
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
                # Drop partial boot text arriving without a trailing newline.
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
            return  # explicit close already handled by close_port()
        self._save_log(port_name, conn)
        self.emit('close', port_name, None)

    def _forward_line(self, port_name, conn, line):
        line = line.rstrip('\r')
        stripped = line.strip()
        if not stripped:
            return
        # ---- ESP32 boot preamble suppression ----
        if stripped.startswith('ets '):
            conn['boot_suppress'] = True
            return
        if conn['boot_suppress']:
            # Firmware takes over after 'entry 0x' or its own SYSTEM: banner.
            if stripped.startswith('entry 0x') or stripped.startswith('SYSTEM:'):
                conn['boot_suppress'] = False
            else:
                return
        if stripped.startswith(BOOT_PREFIXES):
            return
        # ---- normal forwarding ----
        if stripped.startswith(CONTROL_PREFIXES):
            self.emit('data', port_name, stripped + '\n')
            return
        # Keep the raw line (spaces included) — chars are forwarded as-is.
        self.emit('data', port_name, line)
        self._buffer_chars(conn, line)

    def _buffer_chars(self, conn, text):
        now = datetime.now()
        with conn['lock']:
            for ch in text:
                if ch and ch != '\r':
                    conn['chars'].append((now, ch))

    # ----------------------------------------------------------- monitor
    def _monitor_loop(self):
        """Auto-detect plugged devices and reconnect dropped ports."""
        last_ports = None
        while not self._monitor_stop.is_set():
            try:
                # Use the same resilient enumeration as list_ports() so a
                # transient pyserial failure can't falsely empty the list.
                ports = {p['name'] for p in self.list_ports()}
                if ports != last_ports:
                    last_ports = ports
                    self.emit('ports', None, self.list_ports())
                with self._lock:
                    wanted = [
                        (name, c['baud'])
                        for name, c in self._conns.items()
                        if c['desired'] and (not c['serial'] or not c['serial'].is_open)
                    ]
                for name, baud in wanted:
                    if name in ports:
                        self.open_port(name, baud)
                        self.emit('reconnect', name, None)
            except Exception:
                pass
            self._monitor_stop.wait(SCAN_INTERVAL)
