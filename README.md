# BrailleBridge

*A low-cost, bilingual (English + Bangla) digital Braille writing and classroom examination system.*

BrailleBridge lets blind and visually impaired students write independently — during classwork, assignments, and formal examinations — using familiar six-dot Braille chords. An ESP32 translates each chord in real time into readable English, Bangla, numbers, punctuation, and mathematical symbols, and delivers the result over two independent channels:

- **Bluetooth HID keyboard** — the output appears on the student's own phone, tablet, or computer, where a built-in screen reader reads it aloud.
- **USB Serial** — the same text arrives in the browser-based **Teacher Software**, giving sighted teachers readable output without ever learning Braille.

---

## Table of Contents

- [Why BrailleBridge](#why-braillebridge)
- [Key Features](#key-features)
- [Repository Structure](#repository-structure)
- [Hardware](#hardware)
  - [Bill of Materials](#bill-of-materials)
  - [GPIO Mapping](#gpio-mapping)
- [How It Works](#how-it-works)
  - [Braille Chording](#braille-chording)
  - [Language Switching](#language-switching)
  - [Shift Modifier](#shift-modifier)
- [Getting Started](#getting-started)
  - [Firmware (ESP32)](#firmware-esp32)
  - [Teacher Software](#teacher-software)
  - [Marketing Website](#marketing-website)
  - [3D-Printed Enclosure](#3d-printed-enclosure)
- [Serial Protocol](#serial-protocol)
- [Documentation](#documentation)
- [Roadmap](#roadmap)
- [License](#license)
- [Author](#author)

---

## Why BrailleBridge

In many classrooms and examination halls, a blind student cannot independently produce an answer sheet that a sighted teacher can immediately read. The common workaround — dictating every answer to a sighted writer — forces the student to:

- Speak answers aloud, losing privacy and confidentiality;
- Work at the writer's pace, losing control over speed;
- Risk transcription errors in technical terms, names, and Bangla phonetics;
- Hand over control of the final written record entirely.

Traditional embossed Braille solves the writing problem but is unreadable to most sighted teachers, and commercial digital Braille systems can cost hundreds or thousands of dollars.

BrailleBridge addresses the whole gap: the student writes through familiar Braille chords, the ESP32 translates instantly, and the teacher receives ordinary digital text — at a bill-of-materials cost of roughly **$12 per device**.

---

## Key Features

**Hardware device**

- Six mechanical Braille dot keys (Outemu Red, rated ~50M presses) plus dedicated Space and Shift keys
- ESP32 Dev Module with Bluetooth and USB Serial
- 180 ms chording window that reliably merges near-simultaneous key presses
- Two status LEDs (Red = English, Green = Bangla)
- Custom 3D-printed enclosure (Fusion 360 / FDM, top and bottom shells)
- Software language switching — no physical toggle switch required

**Translation**

- Full English alphabet (Grade 1 Braille, A–Z)
- Full Bangla dictionary following the **Bharati Braille** standard (vowels, consonants grouped by varga, vowel signs, halant, anusvara, visarga, candrabindu)
- Shift layer for numbers (1–0), punctuation, and math symbols (`+ - × ÷ =`)
- Shift + vowel produces Bangla dependent vowel signs (kar/matra)
- Unknown chords are rejected cleanly with LED blink feedback

**Teacher Software (browser-based)**

- Zero installation — runs in Chrome/Edge via the Web Serial API
- Multi-student roster with per-student COM ports and baud rates
- Live real-time feeds with language detection (`LANG:en` / `LANG:bn`)
- Exam mode: all students side by side in a monitoring grid
- Expandable per-student view with large serif text
- Timestamped exports (`[HH:MM:SS]` per character) as `.txt` files
- Persistent roster via `localStorage`
- Light/dark theme with `Ctrl+Shift+T` shortcut

---

## Repository Structure

```
.
├── braile/
│   └── braile.ino            # ESP32 firmware (Arduino / C++)
├── braille-display/
│   ├── index.html            # Teacher Software
│   ├── script.js
│   └── style.css
├── website/
│   ├── index.html            # Marketing / project website
│   ├── script.js
│   └── style.css
├── docs/
│   ├── braillebridge.tex     # Full research paper (XeLaTeX / LuaLaTeX)
│   └── ppt.pptx              # Presentation materials
├── models/
│   ├── TOP_SHELL.stl         # 3D-printable enclosure top
│   └── BOTTOM_SHELL.stl      # 3D-printable enclosure bottom
├── LICENSE                   # Apache License 2.0
└── README.md
```

---

## Hardware

### Bill of Materials

| Component                | Qty | Cost (USD) |
| ------------------------ | --- | ---------- |
| ESP32 Dev Module         | 1   | $5.00      |
| Outemu Red switch        | 8   | $3.00      |
| Keycaps (3D-printed)     | 8   | $1.00      |
| LED (3mm) + resistor     | 2+2 | $0.30      |
| Perfboard                | 1   | $0.80      |
| PLA filament (enclosure) | 30g | $1.20      |
| M3 screws, wire, solder  | —   | $0.70      |
| **Total**                |     | **~$12.00**|

### GPIO Mapping

| Function | ESP32 GPIO | Notes           |
| -------- | ---------- | --------------- |
| Dot 1    | 14         | Top-left        |
| Dot 2    | 12         | Middle-left     |
| Dot 3    | 13         | Bottom-left     |
| Dot 4    | 27         | Top-right       |
| Dot 5    | 26         | Middle-right    |
| Dot 6    | 25         | Bottom-right    |
| Space    | 33         | Dedicated space |
| Shift    | 32         | Modifier        |
| Red LED  | 18         | English mode    |
| Green LED| 19         | Bangla mode     |

All switches share a common ground bus. The firmware uses the ESP32's internal pull-up resistors: unpressed reads `HIGH`, pressed reads `LOW`.

---

## How It Works

### Braille Chording

A six-dot Braille cell is laid out as:

```
1 4
2 5
3 6
```

A character is produced by pressing one or more dots simultaneously. Each dot maps to a bit in a 6-bit value:

| Dot | Bit |
| --- | --- |
| 1   | 0   |
| 2   | 1   |
| 3   | 2   |
| 4   | 3   |
| 5   | 4   |
| 6   | 5   |

Because human fingers rarely land at the exact same microsecond, the firmware collects all keys pressed within a **180 ms window**, ORs them into a single chord value, and looks up the result in the active language dictionary.

Example: dots 1 + 4 → `0b001001` → **c** (English) / **চ** (Bangla).

### Language Switching

Hold **dots 4 + 5 + 6 for 500 ms** to toggle between English and Bangla. This exact chord is used by no standard letter or symbol, so accidental switching is practically impossible. The LEDs confirm the active language, and the firmware announces the change over Serial (`LANG:en` / `LANG:bn`) so the Teacher Software can update its indicator.

### Shift Modifier

Holding the physical Shift key while pressing a chord expands the vocabulary:

| Shift + chord      | Output                          |
| ------------------ | ------------------------------- |
| Shift + A–J        | Numbers 1–0                     |
| Shift + math chord | `+`, `-`, `×`, `÷`, `=`         |
| Shift + punctuation| `,` `;` `:` `.`                |
| Shift + letter (EN)| Uppercase letter                |
| Shift + vowel (BN) | Bangla vowel sign (kar/matra)   |

### Shift Tap = Backspace

Tapping Shift alone (press + release **without** composing any chord) deletes the last typed character, like a normal keyboard's Backspace. All the hold-to-modify combos above work exactly as before — only a clean, unused tap fires the delete.

Guards so it never misfires:

- **Dots down during the tap** → modifier mode, no delete (checked both when dots are pressed and when Shift is released mid-chord).
- **Press shorter than 25 ms** → treated as bounce, ignored.
- **Hold longer than 1.5 s** → ignored, so pocketing the device can't wipe text.
- **100 ms cooldown** after a fired delete so contact bounce can't chain multiple backspaces.

The deletion goes out on both outputs: a real HID backspace over Bluetooth (works in any app on the connected computer/phone), and a `SYSTEM:BKSP` control line over Serial, which the Teacher Software already handles in student view, teacher mode, and exam mode.

### Shift Tap = Backspace

Tapping Shift alone (press + release **without** composing any chord) acts as a **Backspace** — it deletes the last typed character. Tap-and-chord combos behave exactly as before; only a clean, unused tap fires the delete. Deliberately long presses (>1.5 s) are ignored so the key can't misfire when pocketed.

The deletion is sent over both outputs: a real HID backspace to the connected device over Bluetooth, and a `SYSTEM:BKSP` control line over Serial, which the Teacher Software handles in student view, teacher mode, and exam mode.

---

## Getting Started

### Firmware (ESP32)

1. Install the [Arduino IDE](https://www.arduino.cc/en/software) and the [Arduino core for ESP32](https://github.com/espressif/arduino-esp32).
2. Open `braile/braile.ino` and upload it to an ESP32 Dev Module. *(No external libraries needed — the sketch uses only the ESP32 core's built-in BLE stack.)*
3. Pair the device (it appears as a Bluetooth keyboard named **BrailleBridge**) with the student's phone, tablet, or computer.
4. Open a text field, type Braille chords, and the translated text appears — while the same characters stream over USB Serial **and over BLE** to the Teacher Software.

> **BLE stream (Nordic UART Service):** alongside the HID keyboard service, the firmware now exposes the standard NUS (`6E400001-B5A3-F393-E0A9-E50E24DCCA9E`) — TX `…0002` notifies the exact serial stream (characters, `LANG:*`, `SYSTEM:BKSP`), RX `…0003` accepts `LANG:en` / `LANG:bn` commands back. This is the channel the future phone app (see [PHONE.md](PHONE.md)) consumes — no USB cable required.
>
> **Phone HID fix (firmware v3):** the HID service is now built with the core's `BLEHIDDevice` helper — the same GATT layout the original library-based build used (keyboard appearance 0x03C1, encrypted report characteristics, battery service, Secure Connections + MITM bonding). This restores **system-wide keyboard typing on Android phones** (WhatsApp text fields, etc.), which had regressed during the v2 custom-GATT rewrite. Still zero external libraries.

### Teacher Software

1. Open `braille-display/index.html` in **Chrome** or **Edge** (both support the Web Serial API).
2. Connect the ESP32 via USB; the browser will prompt you to select the serial port (115200 baud).
3. Add students, assign each to a COM port, and watch their typing appear live.
4. Use **Exam Mode** to monitor the whole class side by side, and **Export** to save timestamped logs per student.

No server, no database, and no installation required — the browser talks directly to the devices.

### Marketing Website

Open `website/index.html` in any browser, or deploy the folder to any static host (GitHub Pages, Netlify, etc.) for a public project site.

### 3D-Printed Enclosure

Print `models/TOP_SHELL.stl` and `models/BOTTOM_SHELL.stl` on an FDM printer (PLA, 0.2 mm layers). The MX-compatible switch cutouts let the eight Outemu switches snap in without glue or solder; the two shells fasten together with M3 screws.

---

## Serial Protocol

All translation happens on the ESP32, so the serial line carries only results at **115200 baud** (and the identical byte stream is mirrored over the BLE Nordic UART Service for the phone app):

| Message            | Meaning                              |
| ------------------ | ------------------------------------ |
| `LANG:en`          | Language switched to English         |
| `LANG:bn`          | Language switched to Bangla          |
| `Invalid`          | Unrecognised chord rejected          |
| `SYSTEM:BKSP`      | Shift tap → delete last character    |
| `<char>`           | A translated character               |

---

## Documentation

A full research paper is included at `docs/braillebridge.tex`. It covers the problem statement, hardware and firmware architecture, the English and Bharati Bangla dictionaries, the Teacher Software design, comparative analysis, affordability, and engineering innovations.

Compile it with **XeLaTeX or LuaLaTeX** (required for full Unicode/Bangla support):

```bash
xelatex braillebridge.tex
```

---

## Roadmap

- Verified full Bharati Braille implementation with experienced users
- Full mathematical Braille code (fractions, brackets, powers)
- Battery power with USB-C charging and battery reporting
- Audio confirmation and vibration feedback
- Secure examination mode with student identification
- PDF/DOCX export and cloud synchronisation
- Multi-school deployment and remote grading

---

## License

Licensed under the **Apache License, Version 2.0**. See [LICENSE](LICENSE) for the full text.

---

## Author

**Samin Yeasar**

- Email: [samin@mentormind.bd](mailto:samin@mentormind.bd)
- GitHub: [github.com/Solez-ai](https://github.com/Solez-ai)
- Web: [solez.html-5.me](https://solez.html-5.me)

*BrailleBridge does not replace Braille. It protects Braille as the student's natural writing method while removing the barrier between Braille input and teacher-readable output.*
