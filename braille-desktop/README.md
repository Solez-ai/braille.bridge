# BrailleBridge — Teacher Desktop

The BrailleBridge web app, wrapped in a desktop window with a **Python serial
relay**. Python owns every ESP32 COM port, so one device can be watched by the
Student View, the Teacher roster, and the Exam grid at the same time — no more
"Failed to open serial port" from two views fighting over one connection.

## Quick start

```bash
cd braille-desktop
pip install -r requirements.txt
python main.py
```

## What the Python side does

| Feature | Where |
|---|---|
| Owns COM ports (pyserial), one reader thread per port | `relay.py` |
| Streams every serial line/char into the embedded web UI | `relay.py` → `main.py` → JS |
| Auto-detects plug/unplug, pushes the port list to the UI | `relay.py` monitor loop |
| Auto-reconnects a dropped device when the port returns | `relay.py` monitor loop |
| Persists student ⇄ COM port assignments | `data/assignments.json` |
| Auto-saves each session as readable prose | `logs/` (on disconnect, Save Logs button, and app close) |

## Notes

- The window is Edge WebView2 (bundled with Windows 10/11). The browser
  version of `braille-display` still works unchanged — the app only switches
  to the relay transport when it detects `window.pywebview`.
- Google Fonts need an internet connection; offline the UI falls back to
  system serif fonts.
- Session logs land in `braille-desktop/logs/` as
  `{StudentName}_{timestamp}.log` with per-line timestamps.
