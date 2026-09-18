# PHONE.md — Building BrailleBridge for Android (Kotlin, Bluetooth-Only)

> **Goal:** a phone app that looks and behaves **exactly** like the existing
> BrailleBridge teacher platform (`braille-display/` + `braille-desktop/`),
> except the transport is **Bluetooth Low Energy instead of USB serial** —
> with a **custom BLE proxy service that starts with the app**, so the phone
> takes full advantage of BLE from the first second.
>
> Every protocol rule, control line, boot-filter, chord table, timing constant
> and UI behavior below is copied **verbatim** from the current codebase, so
> the phone app is a drop-in replacement for the desktop one. Nothing about
> the student experience changes.

---

## 0. What must be identical (the rules)

| Rule | Value (do not change) | Source of truth |
|---|---|---|
| Device BLE name | `BrailleBridge` | `braile/braile.ino` — `BBKeyboard bleKeyboard("BrailleBridge")` (vendored T-vK library + NUS) |
| Serial baud (legacy/USB) | 115200 (also 9600/57600/38400 selectable) | `braille-display` UI + `braille-desktop/main.py` |
| Chord collection window | **180 ms** timeout, process on all-released OR timeout | `loop()` in `braile.ino` |
| Language toggle chord | Dots **4+5+6 held 500 ms** → toggle EN/BN, wait for release, then 50 ms settle | `loop()` |
| Shift behavior | Held = modifier; **tap alone (press+release, no chord) = BACKSPACE** | `braile.ino` shift state machine |
| Shift tap guards | min 25 ms, max 1500 ms, 100 ms cooldown, dots-held veto | `braile.ino` |
| Space | Immediate char + 200 ms debounce, block until released | `loop()` |
| Control lines | `SYSTEM:…`, `LANG:en`, `LANG:bn`, `Invalid`, `SHIFT` — never rendered as text | `relay.py CONTROL_PREFIXES` |
| Backspace control line | `SYSTEM:BKSP` on its own line | `sendBackspace()` |
| Language lines | `LANG:en` / `LANG:bn` (exactly, lowercase suffix) | `loop()` |
| Boot preamble filter | Drop `ets `, `rst:0x`, `boot:0x`, `configSPIWP`, `clk_drv:`, `q_drv:`, `d_drv:`, `cs0_drv:`, `hd_drv:`, `wp_drv:`, `mode:DIO`, `load:0x`, `entry 0x`; stateful: after `ets ` suppress until `entry 0x` or a `SYSTEM:` line | `relay.py BOOT_PREFIXES` + `makeBootFilter()` in `script.js` |
| Chord dictionaries | Bharati Braille tables — EN a–z, BN full varnmala, কার shift map, numbers 1–0 on Shift+A–J, math/punct symbols | `brailleDict[]`, `numberChords[]`, `shiftSymbols[]`, `banglaShiftMap[]` |
| Unknown chord | **Silently ignored** (no output, no error) | `processChord()` |
| BLE ASCII rule | Only ASCII goes to BLE HID; Bangla (multi-byte UTF-8) is serial/transport only — pushing it to HID wedges the ESP32 | `sendChar()` comment in `braile.ino` |

---

## 1. Transport: what changes on the phone

The desktop app reads the ESP32 over **USB COM port via pyserial**. On Android
there is no COM port — the same byte stream arrives over **BLE GATT
notifications**. The protocol layer above it must not change.

### 1.1 The ESP32 side — ✅ IMPLEMENTED (`braile/braile.ino`)

The firmware runs the **T-vK BleKeyboard code that worked in v1 — vendored
into the sketch folder** as `braile/BBKeyboard.h/.cpp` (class renamed
`BBKeyboard`), with the **Nordic UART Service grafted on** as a second
service. No library install needed. This is the proven pairing/typing stack
(keyboard appearance 0x03C1, SC+MITM bonding, T-vK report map and
advertising shape) plus one added data channel:

1. **HID over GATT (0x1812):** byte-for-byte the library build — paired
   hosts see a keyboard named **BrailleBridge** and receive ASCII typing
   exactly as v1 did on phones and PCs.
2. **Nordic UART Service (the proxy channel):** the *raw character +
   control-line stream* that goes to Serial is mirrored over BLE:

```cpp
// implemented — BBKeyboard.h (NUS ADDITION section)
#define NUS_SERVICE_UUID "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
#define NUS_TX_UUID      "6E400002-…"   // notify: chars, LANG:*, SYSTEM:BKSP
#define NUS_RX_UUID      "6E400003-…"   // write: phone can send LANG:en/LANG:bn
```

`sendChar()` writes to Serial **and** notifies NUS (MTU-chunked);
`streamLine()` does the same with `\n` appended. Non-subscribed centrals are
skipped automatically by the stack's CCCD handling.

**MTU:** the peripheral sets MTU 247. On the Android side call
`requestMtu(247)` right after `onDescriptorWrite` succeeds and **buffer
partial notifications** (see §2.3).

### 1.2 The BLE proxy service (starts with the app)

A foreground `Service` that owns *all* Bluetooth work, starts on app launch,
survives Activity recreation, and re-publishes itself:

```kotlin
class BleProxyService : Service() {
    // One connection per student device, mirroring relay.py's _conns map
    private val connections = ConcurrentHashMap<String, BleDeviceConn>()
    private val assignments = ... // persisted name->MAC, like data/assignments.json

    override fun onStartCommand(...) = START_STICKY
}
```

Responsibilities (each one maps 1:1 to `relay.py`):

| relay.py | BleProxyService |
|---|---|
| `_monitor_loop()` re-scan every 2 s | `ScanCallback` loop with `ScanSettings.SCAN_MODE_LOW_POWER` between windows; auto-connect by MAC when a **bonded/known** `BrailleBridge` device appears |
| `open_port(name, baud)` | `connectGatt(context, false, callback, TRANSPORT_LE)` + discovery + enable notifications |
| `close_port(name)` | `gatt.disconnect(); gatt.close()`, keep the conn object for reconnect |
| auto-reconnect on drop | `onConnectionStateChange → DISCONNECTED` ⇒ exponential backoff reconnect (1s, 2s, 4s… cap 10s), emit `reconnect` event when back |
| `_read_loop` incremental UTF-8 decoder | accumulate `ByteArray` notifications; decode with `CharsetDecoder` in `CodingErrorAction.REPLACE` — a Bangla char split across two notifications must not become garbage |
| `CONTROL_PREFIXES` routing | identical line splitter, §2.2 |
| logs/ + data/assignments.json | Room DB + DataStore, same JSON shape |

**Foreground requirement:** `FOREGROUND_SERVICE` + `BLUETOOTH_CONNECT` +
`ACCESS_FINE_LOCATION` (scan) permissions; show a persistent
"BrailleBridge BLE bridge active — N devices" notification. Start the service
in `Application.onCreate()` so BLE is live before the first frame renders —
that is the "proxy comes up as the app starts" rule.

### 1.3 Connection UX parity

- Student view "Connect" button lists nearby `BrailleBridge` devices
  (name-filtered scan), shows RSSI; remembers last device and auto-connects.
- Teacher roster Add-Student form: same three rows (Name / **Bluetooth**
  / "baud" row becomes **Device picker**) — keep the baud select in the UI for
  parity but disable it when connType = bluetooth (baud is a USB concept).
- Status dot + `Connected/Disconnected` label behave identically
  (`updateSerialUI` equivalent).

---

## 2. Protocol layer (port these exactly)

### 2.1 Line model

`makeSerialFeed(onLine, onChars)` in `script.js` is the canonical behavior:

```
buffer += chunk
while newline in buffer: emit trimmed line to onLine
if trailing partial: emit to onChars   // chars arrive without \n
```

The Kotlin port (`LineFeed`) must do the same split, then classify:

- starts with `SYSTEM:` → control (handle `SYSTEM:BKSP`, ignore rest)
- equals `LANG:en` / `LANG:bn` → switch language state, update indicators
- equals `Invalid` or `SHIFT` → ignore (never render)
- else → character data

### 2.2 Boot suppression (stateful port)

```
var suppress = false
fun dropLine(line): Boolean {
  if (line.startsWith("ets ")) { suppress = true; return true }
  if (suppress) {
    if (line.startsWith("entry 0x") || line.startsWith("SYSTEM:")) suppress = false
    else return true
  }
  return BOOT_PREFIXES.any(line::startsWith)
}
```
Partial chunks (`ets ` without newline) set suppress exactly like
`relay.py _read_loop`.

### 2.3 MTU-safe reassembly

BLE notifications arrive in ≤ (MTU-3) byte chunks. Reassemble at the byte
level, decode incrementally (surrogate-safe), then feed `LineFeed`. This
mirrors `codecs.getincrementaldecoder('utf-8')(errors='replace')`.

---

## 3. Dictionaries (port these tables byte-for-byte)

Copy from `braille-display/script.js` (identical to the firmware tables):

- `brailleDict` — 52 entries: shared EN/BN chords + Bangla-only cells +
  convenience cells (ি, ূ, duplicate স). Keep **`f`, `w` having `bangla: null`**
  and the `null` entries exactly — the "chord exists but not in this language"
  rule returns null (silently ignored).
- `numberChords` / `numberMap` — Shift+A–J → 1–0.
- `shiftSymbols` — math first (`+ − × ÷ =` — note `×` at 0b100110 shares chord
  with `,` handling order), then `, ; : .` (order matters: 0b010110 `+` before
  0b100110 `×`).
- `banglaShiftMap` — vowel → কার, with অ (0b000001) mapping to **null**
  → falls through to normal output (do not "fix" this).
- Translation priority when Shift held: numbers → math/punct → uppercase EN →
  কার BN → fallback normal BN char → else ignore.

## 4. Feature parity checklist (all of these exist today; all must exist on phone)

### Student view
- 6-dot clickable Braille cell with dot order layout (1-4 / 2-5 / 3-6 columns),
  pressed-dot animation + pulse, chord binary + dots readout, live mapping line
- English/বাংলা + Shift indicators (LED semantics: EN=red LED, BN=green LED)
- Live output stream with per-char spans, Bangla font stack
  (`Noto Serif Bengali → Nirmala UI → Vrinda`), blinking cursor, auto-scroll
- Recent characters strip (80-char rolling window)
- Clear button, keyboard shortcuts (1–6 dots, Space, Enter commit, Esc clear,
  L language, S shift) — on phone these become physical-keyboard support only
- **Backspace tap** reflected live (device Shift tap removes last char)
- Send-to-Teacher mirror (`mirrorStudentId` semantics: one connection, two views)

### Teacher view
- Roster with avatars (initials + 8-color palette `#5a8ae0 #d45a5a #5ab85a
  #c49a4a #8a6ad4 #4ac8b8 #e08a5a #5ab8b8`), online/offline dot, connect button
- Feed grid cards: header (avatar/name/conn badge/baud/status), body
  (live stream), chord bar (6 mini dots + `0b…` + char count)
- Per-card actions: Preview(prose) · Expand · Test(simulate `hello বাংলা`
  typing at 200 ms/char) · Export · Clear · Remove
- Toolbar: student count, total chars, Save Logs, **Export All**, Clear All
- Backspace handling per student (`handleStudentBackspace` pops `{char,time}`)
- Periodic 500 ms failsafe refresh of all feeds

### Exam view
- Same cards, no per-card actions, toolbar shows student/char counts,
  Export button — feeds stay live during exams, chars still timestamped

### Modals
- **Preview modal:** readable prose — group chars into words/lines, ≤52 chars
  per line after the `[HH:MM:SS]` prefix, line timestamp = first char typed;
  Export + Save-to-Exports buttons; footer "N character(s) — M line(s)"
- **Expand modal:** full live view of one student, scroll-to-bottom button,
  Ctrl+Enter clear, preview hand-off
- **Send modal:** mirror flow (name + conn + baud), duplicate-mirror guard

### Everything new that must also exist on phone (§6–§8)
- Teacher account UI — **Samin Yeasar** (identical to §7)
- Google Translate integration (identical to §6)
- Exports tab with saved exports, review screen, auto-formatter (§8)

---

## 5. Android architecture

```
/app
  /ble            BleProxyService, BleDeviceConn, GattCallbacks, LineFeed,
                  BootFilter, Utf8Reassembler      ← §1–2
  /protocol       BrailleDict.kt, Translate.kt (tables + lookup priority) ← §3
  /data           StudentRepo (Room: students, chars{char,time}, exports),
                  SettingsStore (theme, assignments JSON)
  /ui
    /student      StudentScreen (cell, output, translate bar)
    /teacher      RosterScreen, FeedGrid, StudentCard
    /exam         ExamScreen
    /exports      ExportsScreen (list) + ReviewScreen (formatted doc)
    /account      AccountSheet (Samin Yeasar profile)
    /theme        Theme.kt — port BOTH light & dark palettes
```

- **Jetpack Compose**, MVVM, one `SharedViewModel` per mode mirroring the
  global-state style of `script.js` (`students[]`, `totalCharsAllStudents`,
  `isBangla`, `shiftActive`).
- **Compose Multiplatform note:** not needed — single Android target.
- ViewModels survive rotation; the BLE service is the source of truth and
  pushes via `StateFlow` — exactly how `relay.py` pushes into the webview.

### Theme ports

Dark (default) from `style.css :root`:
`--bg-dark #0f111a · --bg-panel #161822 · --bg-card #1c1f2e ·
--bg-surface #242738 · --bg-hover #2d3044 · --text #e8e6e0 / #a8a4a0 / #6a6a7a ·
--gold #c49a4a · --gold-light #dbb86a · --gold-dark #a07828 ·
--accent-red #d45a5a · --accent-green #5ab85a · --accent-blue #5a8ae0 ·
--accent-purple #8a6ad4 · --accent-teal #4ac8b8 ·
--radius 8/14/20 · Inter + Playfair Display + Noto Serif Bengali`

Light: `#f4f3f0 / #ffffff / #faf9f6 / #efede8 / #e6e3dc`, ink `#1a1a2e`,
same accents. Ctrl+Shift+T theme toggle → app setting + top-bar icon.
The dot buttons use `linear-gradient(145deg …)` with the `0 5px 0` hard
drop-shadow — replicate with two-layer shadow in Compose.

---

## 6. Google Translate (same behavior on both platforms)

Reference implementation: `braille-display/shared.js → BBTranslate`.

- **FULL LANGUAGE CATALOGUE (updated rule):** every language Google Translate
  supports (~128 codes) must be selectable — port the `LANGUAGES` table from
  `braille-display/shared.js` verbatim into `Translate.kt` as
  `data class BBLanguage(val code: String, val name: String, val cc: String)`.
  The picker is a native dropdown (Material3 `ExposedDropdownMenuBox` or
  `Spinner`) listing "flag + English name", defaulting to English (`en`).
- Endpoint: `https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=<target>&dt=t&q=<text>`
  (parse `data[0][i][0]` segments), fallback
  `/language/translate/v2` v2 shape. **Cache** every (source,target,text) pair.
- Source is ALWAYS `auto`; Google returns the detected code — display it:
  `"(Bangla → French)"` style, via a `name(code)` lookup over the same table.
  Local fallback (`detectLanguage()`): Bengali range `[\u0980-\u09FF]` →
  display "Bangla" when Google's detection is unavailable.
- **Live bar (student view):** appears under Live Output the moment the stream
  has content (MutationObserver on web / snapshot flow on Android), language
  dropdown + "Translate" button → shows result inline with the
  `(detected → target)` caption. Choosing a new language and pressing
  Translate again re-translates from the ORIGINAL text (keep the original
  stream text separately from the displayed translation).
- **Review translate:** see §8.3 (translate the formatted document into ANY
  chosen catalogue language, original preserved, picker defaults to last use).
- Android: `OkHttp` + `kotlinx.serialization`; do the request off-main;
  same cache in memory (and optionally DiskLru).

## 7. Teacher Account UI — Samin Yeasar (both platforms, look legit)

Reference: `shared.js ensureModals()` + `shared.css`. Two parts:

1. **Header chip** (always visible, both modes): gold-gradient avatar `SY`,
   name **Samin Yeasar**, role *Teacher*, chevron. On the website the same
   chip lives in the nav (`siteAccountChip`).
2. **Profile modal** (opens on tap; Esc/overlay click closes):

```
┌────────────────────────────────────┐
│ ░ patterned navy/gold banner ░  ✕  │
│  (SY)  ← 78px gold avatar, overlap │
│                                    │
│  Samin Yeasar  ✓(teal verified)    │
│  Teacher · Braille Literacy        │
│  [🪪 BB-T-0001][🛡 Verified][🔒 Local profile] │
│  ┌───────┬────────┬───────────┐    │
│  │   3   │   12   │   1,204   │    │
│  │Students│Exports│Characters │    │   ← live from app state
│  └───────┴────────┴───────────┘    │
│  ✉ samin.yeasar@braillebridge.edu  │
│  🏫 Special Education — BrailleBridge Academy │
│  🌐 English · বাংলা · Google Translate enabled  │
│  📅 Member since 2026 · Device owner│
│  ( Sign out )  ( Close )           │
└────────────────────────────────────┘
```

Stats row is **live**: students = roster size, exports = exports count,
characters = `totalCharsAllStudents` (website shows `—` when no roster).
Sign out shows the demo toast: *"Signed out of this session (demo account
stays active)."*

## 8. The Exports section (both platforms)

### 8.1 Trigger points
- **"Export All"** (teacher toolbar), **"Export"** (exam toolbar),
  **Export** (per-student card & preview modal) → the .txt download happens
  exactly as today, **and** the export is saved into the Exports library with
  a toast *"…saved to Exports"*.
- Website demo: new **Export** toggle next to Clear saves the demo stream
  (`source: demo`).
- Preview modal gains **"Save to Exports"** (save without downloading).

### 8.2 The Exports tab
- Desktop app: new **Exports** button in the mode toggle (Student/Teacher/
  Exam/**Exports**) → opens the Exports modal (does not switch away from the
  current view). Phone: bottom-nav destination.
- List cards: icon (user/class/flask), title, timestamp, mode, char count,
  conn info, block count, actions: **Review** · **.txt** · **Delete**.
  Clear-all with confirm. Storage cap 100 (FIFO). Web storage:
  `localStorage['bb-exports-v1']` / `['bb-site-exports-v1']`;
  Android: Room table `exports(id, title, mode, source, charsCount,
  blocksJson, created)`.

### 8.3 Review screen (the "better way to review")
- Formatted document view rendered by the **auto-formatter** (§8.4):
  real title/heading/paragraph/list typography, gold rule under titles,
  per-block timestamps visible in Raw mode.
- Toolbar: **Back · Translate → <language picker> · Raw · Download .txt**
  - Translate converts the whole document into the picked language (full
    catalogue); toggling between original/translated preserves both;
    download exports whatever is currently shown.
  - Raw = monospace timestamped lines.
- Footer: title · char count · formatted block count.

### 8.4 Auto-formatter rules (port `BBAutoFormat` exactly)
1. Chars → lines: space = word boundary (collapse runs), `\n/\r` = line break;
   each line keeps the **timestamp of its first character**.
2. Headings by keyword, EN + BN:
   `chapter/অধ্যায়`→H1 · `section/অনুচ্ছেদ`→H2 · `lesson/পাঠ`→H3 ·
   `exercise/অনুশীলন/question/প্রশ্ন`→H4.
3. Bullets: line starts `- * • · →`; numbered: `\d+[.)]`.
4. Everything else accumulates into a paragraph (lines joined with spaces).
5. Punctuation fixer: no space **before** `.,;:!?।`, exactly one space
   **after** (not between digits/decimal), collapse multi-spaces, `....`→`...`.
6. Title: first paragraph block if ≤60 chars, ≤6 words, no terminal
   punctuation.
7. Output blocks `{type: title|heading|para|bullet|numbered, text, time,
   level}` — same JSON stored in each export; `.txt` serializer: titles
   UPPERCASE, blank lines around headings/paras, `• ` bullets, `N.`
   numbering (counter resets at headings/paras/titles).

---

## 9. Milestones

1. **M1 Transport:** firmware NUS addition + Android BLE service that connects
   and streams the same byte stream the desktop sees (verify with the
   `SYSTEM:` banner, `LANG:` lines, boot-filter working).
2. **M2 Student parity:** dot cell, output stream, indicators, backspace tap,
   keyboard parity — golden test: type the alphabet in EN, vowels+কার in BN,
   numbers/math/punct with Shift, tap-delete, language toggle; byte-compare
   the resulting stream against desktop.
3. **M3 Teacher/Exam:** roster, feeds, modals, timestamps, backspace sync.
4. **M4 Shared features:** account UI, translate, exports + auto-formatter.
5. **M5 Hardening:** reconnection storms, MTU fragmentation fuzz (split
   Bangla chars across notifications), 2+ devices concurrently, battery
   (scan duty cycling).

## 10. Testing checklist (run on both platforms, expect identical output)

- [ ] Chord → char for all 26 EN, all BN cells, all কার, digits, `+ − × ÷ = , ; : .`
- [ ] Shift priority conflicts (e.g. 0b010110 = `+` and also ফ-chord family)
- [ ] D4+5+6 short press does NOT toggle; ≥500 ms does; works while Shift held
- [ ] Shift tap = 1 backspace; Shift+chord = modifier; Shift+Space = space, no delete
- [ ] Bounce: 15 ms Shift flicker → nothing; release bounce → 1 delete
- [ ] `SYSTEM:BKSP` removes last char in student view, teacher feed, exam feed, mirror
- [ ] Boot garbage never appears (power-cycle the ESP32 mid-session)
- [ ] Bangla split across BLE packets renders correctly
- [ ] Export saved → appears in Exports → review shows title/headings/lists →
      translate to any catalogue language → download matches on-screen text
- [ ] Account modal shows live stats; website shows `—` stats without roster
- [ ] Theme toggle persists; both palettes render all new UI correctly
