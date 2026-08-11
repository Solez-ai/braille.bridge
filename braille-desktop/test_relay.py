"""Minimal tests for the relay core — no real hardware, no GUI.

Run:  python test_relay.py
"""
import os
import sys
import tempfile
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import relay as relay_mod  # noqa: E402


class FakeSerial:
    def __init__(self, port, baud, timeout=0.1):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.is_open = True
        self.incoming = []

    def read(self, n=1):
        if self.incoming:
            return self.incoming.pop(0)
        time.sleep(0.005)
        return b''

    def write(self, data):
        pass

    def close(self):
        self.is_open = False


def patch():
    relay_mod.serial.Serial = FakeSerial
    relay_mod.LOGS_DIR = tempfile.mkdtemp(prefix='bb_logs_')
    relay_mod.DATA_DIR = tempfile.mkdtemp(prefix='bb_data_')
    relay_mod.ASSIGN_FILE = os.path.join(relay_mod.DATA_DIR, 'assignments.json')


def test_relay_flow():
    patch()
    events = []
    mgr = relay_mod.RelayManager(lambda kind, port, payload: events.append((kind, port, payload)))
    mgr._monitor_stop.set()  # deterministic: disable background scanning

    assert mgr.open_port('COM99', 115200) is True
    conn = mgr._conns['COM99']
    ser = conn['serial']

    # Chars arrive one byte at a time (firmware uses print() with no newline)
    for b in b'hello world':
        ser.incoming.append(bytes([b]))
    time.sleep(0.4)

    # Control lines arrive as whole println() lines
    ser.incoming.append(b'SYSTEM:BKSP\n')
    ser.incoming.append(b'LANG:bn\n')
    ser.incoming.append(b'Invalid\n')
    time.sleep(0.4)

    assert mgr.close_port('COM99') is True
    time.sleep(0.2)

    data_joined = ''.join(str(ev[2]) for ev in events if ev[0] == 'data')
    assert 'SYSTEM:BKSP' in data_joined, 'control line must be forwarded'
    assert 'hello world' in data_joined, 'char stream must be forwarded'

    # Session log written as readable prose
    log_files = os.listdir(relay_mod.LOGS_DIR)
    assert len(log_files) == 1, log_files
    with open(os.path.join(relay_mod.LOGS_DIR, log_files[0]), encoding='utf-8') as f:
        content = f.read()
    assert 'hello world' in content, content

    # Assignments persist
    assert mgr.set_assignment('Sarah', 'COM3') is True
    assert mgr.get_assignments() == {'Sarah': 'COM3'}
    assert mgr.set_assignment('Sarah', '') is True
    assert mgr.get_assignments() == {}

    # Wrap sanity
    now = datetime.now()
    lines = relay_mod.RelayManager._wrap([(now, c) for c in 'a b c d e f g h i j'])
    assert any('a b c d e f g h i j' == t for _, t in lines)

    print('test_relay_flow: OK')


def test_split_utf8_bangla():
    """A multi-byte Bangla character split across two reads must not corrupt."""
    patch()
    events = []
    mgr = relay_mod.RelayManager(lambda kind, port, payload: events.append((kind, port, payload)))
    mgr._monitor_stop.set()
    assert mgr.open_port('COM98', 115200) is True
    ser = mgr._conns['COM98']['serial']
    # U+09AC (ব) is E0 A6 AC — split it across two reads.
    ser.incoming.append(b'\xe0\xa6')
    ser.incoming.append(b'\xac')
    time.sleep(0.3)
    assert mgr.close_port('COM98') is True
    time.sleep(0.1)
    chars = ''.join(str(ev[2]) for ev in events if ev[0] == 'data')
    assert '\u09ac' in chars, repr(chars)
    log_files = os.listdir(relay_mod.LOGS_DIR)
    assert len(log_files) == 1, log_files
    with open(os.path.join(relay_mod.LOGS_DIR, log_files[0]), encoding='utf-8') as f:
        content = f.read()
    assert '\u09ac' in content, content
    print('test_split_utf8_bangla: OK')


def test_close_port_idempotent():
    patch()
    events = []
    mgr = relay_mod.RelayManager(lambda kind, port, payload: events.append((kind, port, payload)))
    mgr._monitor_stop.set()
    assert mgr.close_port('never_opened') is True
    print('test_close_port_idempotent: OK')


if __name__ == '__main__':
    test_relay_flow()
    test_split_utf8_bangla()
    test_close_port_idempotent()
    print('ALL RELAY TESTS PASSED')
