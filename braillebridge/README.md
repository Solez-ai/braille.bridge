# BrailleBridge — Android App (Kotlin / Compose)

The mobile counterpart to the ESP32 BrailleBridge keyboard: receives the live
character + control-line stream over **Bluetooth Low Energy** (Nordic UART
Service) and mirrors every feature of the desktop/web teacher platform.

## ⚠️ How this app is built — READ FIRST

**Never build this app locally. No `gradlew`, no Android Studio builds on your
machine.** The single source of APKs is **GitHub Actions**:

1. Commit & push to `main` (any change — the workflow runs on every push).
2. Open the repo → **Actions** tab → *Build BrailleBridge APK*.
3. When the run finishes (green ✓), open it → **Artifacts** →
   **BrailleBridge-debug-apk** → download & unzip.
4. Copy `app-debug.apk` to your phone and install it
   (allow *Install unknown apps* for your file manager when prompted).

Need a build without a code change? **Actions → Build BrailleBridge APK →
Run workflow** (manual trigger).

The workflow (`.github/workflows/build-apk.yml`) uses JDK 17 + Gradle 9.3.1
and generates the debug keystore itself, so nothing secret is needed for
debug builds.

## Connecting to the BrailleBridge device

- **Keyboard mode (type into WhatsApp, any text field):** pair once in
  **Android Settings → Bluetooth** — the phone's own BLE HID stack handles it.
  No app involvement required.
- **App mode (live stream in this app):** open the app → the BLE service
  auto-connects to any device named *BrailleBridge* (or tap the Bluetooth
  icon in the top bar to scan manually).
- Both work at the same time: HID gives raw ASCII typing, the Nordic UART
  stream carries ASCII + Bangla + control lines (`LANG:*`, `SYSTEM:BKSP`).
- If characters ever stop appearing in the app: toggle the device's language
  switch (D4+D5+D6) — any `LANG:` line confirms the stream; if still silent,
  forget & re-pair the device in system settings, then reconnect.

## Feature parity

Student / Teacher / Exam / Exports tabs, teacher account (Samin Yeasar),
Google Translate with the full ~128-language catalogue, auto-formatted
export review with .txt download — all mirroring `braille-display/` and
`braille-desktop/`. Protocol and firmware details live in `PHONE.md`.
