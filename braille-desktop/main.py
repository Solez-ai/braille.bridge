"""BrailleBridge — Teacher Desktop (Python relay + embedded web UI).

A pywebview window hosts the existing braille-display web app while a Python
relay (relay.RelayManager) owns the ESP32 COM ports. The UI talks to Python
through window.pywebview.api, and Python pushes serial data into the page via
evaluate_js — no Web Serial exclusivity, no "port in use" errors, and multiple
views can watch the same device at once.

Run:  python main.py
Setup: pip install -r requirements.txt
"""
import json
import os

import webview

from relay import RelayManager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_FILE = os.path.abspath(os.path.join(BASE_DIR, '..', 'braille-display', 'index.html'))


class BridgeApi:
    """Exposed to the web UI as window.pywebview.api.*"""

    def __init__(self):
        self._window = None
        self._relay = None

    def attach(self, window):
        self._window = window

        def emit(kind, port, payload):
            try:
                if kind == 'data':
                    code = f'window.__relayOnData({json.dumps(port)}, {json.dumps(payload)})'
                elif kind == 'ports':
                    code = f'window.__relayOnPorts({json.dumps(payload)})'
                else:
                    code = f'window.__relayOnEvent({json.dumps(port)}, {json.dumps(kind)})'
                window.evaluate_js(code)
            except Exception:
                pass  # UI not ready yet — the relay keeps buffering

        self._relay = RelayManager(emit)

    # ------------------------------------------------------------ js_api
    def list_ports(self):
        return self._relay.list_ports()

    def open_port(self, port_name, baud=115200):
        return self._relay.open_port(port_name, int(baud))

    def close_port(self, port_name):
        return self._relay.close_port(port_name)

    def get_assignments(self):
        return self._relay.get_assignments()

    def set_assignment(self, name, port_name):
        return self._relay.set_assignment(name, port_name)

    def save_all_logs(self):
        saved = self._relay.save_all_logs()
        return f'Saved {saved} session log(s) to the logs/ folder.'

    # ------------------------------------------------------------ cleanup
    def shutdown(self):
        if self._relay:
            self._relay.save_all_logs()
            self._relay.shutdown()


def main():
    api = BridgeApi()
    index_url = 'file:///' + INDEX_FILE.replace('\\', '/')
    window = webview.create_window(
        'BrailleBridge — Teacher Desktop',
        url=index_url,
        js_api=api,
        width=1440,
        height=920,
        min_size=(1100, 700),
    )
    api.attach(window)
    window.events.closing += api.shutdown
    webview.start(debug=False)


if __name__ == '__main__':
    main()
