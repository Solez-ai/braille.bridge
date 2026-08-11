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


def test_registry_fallback():
    """When pyserial enumeration transiently returns empty (Windows quirk),
    list_ports() must fall back to the SERIALCOMM registry so the UI never
    shows '(no ports detected)' while the OS knows the port is present."""
    patch()
    events = []
    mgr = relay_mod.RelayManager(lambda kind, port, payload: events.append((kind, port, payload)))
    mgr._monitor_stop.set()

    # pyserial sees nothing...
    relay_mod.list_ports.comports = lambda include_links=False: []
    # ...but the Windows registry knows the port.
    relay_mod.RelayManager._registry_ports = staticmethod(lambda: ['COM6'])

    result = mgr.list_ports()
    assert result == [{'name': 'COM6', 'description': 'COM port (Windows registry)'}], result
    print('test_registry_fallback: OK')


def test_bangla_word_flow():
    """Full Bangla session through the relay: LANG:bn toggle + a Bangla word
    arriving byte-by-byte (as the ESP32 sends it), mixed with a backspace."""
    patch()
    events = []
    mgr = relay_mod.RelayManager(lambda kind, port, payload: events.append((kind, port, payload)))
    mgr._monitor_stop.set()
    assert mgr.open_port('COM97', 115200) is True
    ser = mgr._conns['COM97']['serial']

    # 1) language toggle line
    ser.incoming.append('LANG:bn\n'.encode('utf-8'))
    time.sleep(0.2)
    # 2) Bangla word 'বাংলা' — each char as separate multi-byte read
    for ch in 'বাংলা':
        ser.incoming.append(ch.encode('utf-8'))
        time.sleep(0.05)
    # 3) backspace control line
    ser.incoming.append(b'SYSTEM:BKSP\n')
    time.sleep(0.3)

    assert mgr.close_port('COM97') is True
    time.sleep(0.1)

    forwarded = ''.join(str(ev[2]) for ev in events if ev[0] == 'data')
    assert 'LANG:bn' in forwarded
    assert 'বাংলা' in forwarded, repr(forwarded)
    assert 'SYSTEM:BKSP' in forwarded

    log_files = os.listdir(relay_mod.LOGS_DIR)
    assert len(log_files) == 1, log_files
    with open(os.path.join(relay_mod.LOGS_DIR, log_files[0]), encoding='utf-8') as f:
        content = f.read()
    assert 'বাংলা' in content, content
    print('test_bangla_word_flow: OK')


def test_esp32_boot_preamble_suppressed():
    """The ESP32 ROM boot text (printed on every reset BEFORE the firmware
    runs) must be dropped — never forwarded to the UI or saved to logs.
    Real capture from the user's device:
      ets Jul 29 2019 12:21:46
      rst:0x1 (POWERON_RESET),boot:0x13 (SPI_FAST_FLASH_BOOT)
      configSPIWP:0xee ... entry 0x400806ac
    The firmware then prints 'SYSTEM: BrailleBridge Connected...' — after
    that, normal chars flow again."""
    patch()
    events = []
    mgr = relay_mod.RelayManager(lambda kind, port, payload: events.append((kind, port, payload)))
    mgr._monitor_stop.set()
    assert mgr.open_port('COM96', 115200) is True
    ser = mgr._conns['COM96']['serial']

    boot = (
        'ets Jul 29 2019 12:21:46\r\n\r\n'
        'rst:0x1 (POWERON_RESET),boot:0x13 (SPI_FAST_FLASH_BOOT)\r\n'
        'configSPIWP:0xee\r\n'
        'clk_drv:0x00,q_drv:0x00,d_drv:0x00,cs0_drv:0x00,hd_drv:0x00,wp_drv:0x00\r\n'
        'mode:DIO, clock div:2\r\n'
        'load:0x3fff0018,len:4\r\n'
        'load:0x3fff001c,len:1044\r\n'
        'load:0x40078000,len:10124\r\n'
        'load:0x40080400,len:5856\r\n'
        'entry 0x400806ac\r\n'
    )
    # The ROM text usually arrives in one blob; split it across two reads to
    # exercise both the full-line and trailing-partial paths.
    mid = len(boot) // 2
    ser.incoming.append(boot[:mid].encode('utf-8'))
    ser.incoming.append(boot[mid:].encode('utf-8'))
    time.sleep(0.4)

    # Firmware banner ends suppression; real chars then flow.
    ser.incoming.append('SYSTEM: BrailleBridge Connected. Waiting for BLE...\n'.encode('utf-8'))
    time.sleep(0.2)
    ser.incoming.append(b'hello')
    time.sleep(0.3)

    assert mgr.close_port('COM96') is True
    time.sleep(0.1)

    forwarded = ''.join(str(ev[2]) for ev in events if ev[0] == 'data')
    assert 'ets' not in forwarded, 'boot line leaked: ' + repr(forwarded)
    assert 'rst:0x' not in forwarded, 'boot line leaked: ' + repr(forwarded)
    assert 'configSPIWP' not in forwarded, 'boot line leaked: ' + repr(forwarded)
    assert 'entry 0x' not in forwarded, 'boot line leaked: ' + repr(forwarded)
    assert 'SYSTEM: BrailleBridge Connected' in forwarded
    assert 'hello' in forwarded, 'post-boot chars must flow: ' + repr(forwarded)

    log_files = os.listdir(relay_mod.LOGS_DIR)
    assert len(log_files) == 1, log_files
    with open(os.path.join(relay_mod.LOGS_DIR, log_files[0]), encoding='utf-8') as f:
        content = f.read()
    assert 'hello' in content, content
    assert 'ets' not in content and 'configSPIWP' not in content, content
    print('test_esp32_boot_preamble_suppressed: OK')


def test_boot_partial_chunk_suppressed():
    """Boot text can arrive with no trailing newline in a read (split
    transport). The trailing-chunk path must still arm suppression on a
    partial 'ets ' and keep dropping until the SYSTEM: banner."""
    patch()
    events = []
    mgr = relay_mod.RelayManager(lambda kind, port, payload: events.append((kind, port, payload)))
    mgr._monitor_stop.set()
    assert mgr.open_port('COM95', 115200) is True
    ser = mgr._conns['COM95']['serial']

    ser.incoming.append(b'ets Jul 29 2')            # no newline at all
    ser.incoming.append(b'019 12:21:46\r\nrst:0x1\r\n')  # rest of boot
    time.sleep(0.3)
    ser.incoming.append(b'SYSTEM: BrailleBridge Connected\n')
    time.sleep(0.2)
    ser.incoming.append(b'ok')
    time.sleep(0.3)

    assert mgr.close_port('COM95') is True
    time.sleep(0.1)

    forwarded = ''.join(str(ev[2]) for ev in events if ev[0] == 'data')
    assert 'ets' not in forwarded, repr(forwarded)
    assert 'rst:0x' not in forwarded, repr(forwarded)
    assert 'SYSTEM: BrailleBridge Connected' in forwarded
    assert 'ok' in forwarded, 'post-boot chars must flow: ' + repr(forwarded)
    print('test_boot_partial_chunk_suppressed: OK')


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
    test_bangla_word_flow()
    test_registry_fallback()
    test_esp32_boot_preamble_suppressed()
    test_boot_partial_chunk_suppressed()
    test_close_port_idempotent()
    print('ALL RELAY TESTS PASSED')
