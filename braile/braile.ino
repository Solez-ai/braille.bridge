#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <BLEHIDDevice.h>

// ==========================================
// BrailleBridge — ESP32 firmware
//
// BLE exposes TWO services at once:
//   1. HID keyboard (0x1812)  → typed characters reach any paired
//      computer/phone text field exactly like the original T-vK
//      BleKeyboard build (phone keyboard mode works again).
//   2. Nordic UART Service    → the raw character + control-line stream
//      (the same bytes that go to USB Serial) mirrored over BLE so the
//      phone app (see PHONE.md) receives it without a USB cable.
//
// HID layer rebuild notes (v3): the HID service is now created with
// BLEHIDDevice — the SAME helper class the proven T-vK BleKeyboard
// library uses. This restores the exact GATT layout Android's BLE HID
// stack expects: keyboard appearance 0x03C1 (NOT generic mouse 0x03C2),
// encrypted report characteristics, HIDS Protocol Mode, battery service,
// Secure Connections + MITM bonding, and the T-vK report map (report ID 1
// keyboard). The NUS service rides alongside it untouched.
// ==========================================

// ==========================================
// PIN DEFINITIONS
// ==========================================
#define DOT_1 14
#define DOT_2 12
#define DOT_3 13
#define DOT_4 27
#define DOT_5 26
#define DOT_6 25
#define SPACE 33
#define SHIFT 32
// (Physical Shift button — hold while pressing dots for uppercase/numbers/math/Bangla vowel signs)
// Tap Shift alone (press + release without any chord) → Backspace (deletes last character)
// #define RED_LED 18
// #define GREEN_LED 19

// ==========================================
// BRAILLE ENTRY STRUCTURE
// ==========================================
struct BrailleEntry {
  uint8_t chord;
  const char* english;
  const char* bangla;
};

// ==========================================
// BRAILLE DICTIONARY — Bharati Braille Standard
// ==========================================
// Based on the Bharati Braille standard (https://en.wikipedia.org/wiki/Bharati_Braille)
// Dot patterns follow International Phonetic Alphabet (IPA) mappings.
//
const BrailleEntry brailleDict[] = {
// ===== Shared English + Bangla chords (Bharati standard) =====
{ 0b000001, "a", "অ" },     // dot 1 = অ
{ 0b000011, "b", "ব" },     // dots 12 = ব
{ 0b001001, "c", "চ" },     // dots 14 = চ
{ 0b011001, "d", "দ" },     // dots 145 = দ
{ 0b010001, "e", "এ" },     // dots 15 = এ
{ 0b001011, "f", nullptr },  // dots 124 = (no standard Bharati Bengali)
{ 0b011011, "g", "গ" },     // dots 1245 = গ
{ 0b010011, "h", "হ" },     // dots 125 = হ
{ 0b001000, "i", "্" },     // dot 4 = হসন্ত (virama/halant)
{ 0b011010, "j", "জ" },     // dots 245 = জ
{ 0b000101, "k", "ক" },     // dots 13 = ক
{ 0b000111, "l", "ল" },     // dots 123 = ল
{ 0b001101, "m", "ম" },     // dots 134 = ম
{ 0b011101, "n", "ন" },     // dots 1345 = ন
{ 0b010101, "o", "ও" },     // dots 135 = ও
{ 0b001111, "p", "প" },     // dots 1234 = প
{ 0b011111, "q", "ক্ষ" },   // dots 12345 = ক্ষ
{ 0b010111, "r", "র" },     // dots 1235 = র
{ 0b001100, "s", "ঐ" },     // dots 34 = ঐ
{ 0b011100, "t", "আ" },     // dots 345 = আ
{ 0b100101, "u", "উ" },     // dots 136 = উ
{ 0b100111, "v", "ৱ" },     // dots 1236 = ৱ (Assamese/Bengali v)
{ 0b111010, "w", nullptr },  // dots 2456 = w
{ 0b101101, "x", "য" },     // dots 1346 = য (yya) — convenience
{ 0b111101, "y", "য" },     // dots 13456 = য
{ 0b110101, "z", "ড়" },     // dots 1356 = z + ড়

  // ===== Bangla-only chords (standard Bharati cells) =====
  { 0b001010, nullptr, "ই" },    // dots 24 = ই
  { 0b010010, nullptr, "ঞ" },    // dots 25 = ঞ
  { 0b001110, nullptr, "স" },    // dots 234 = স
  { 0b111111, nullptr, "ঢ" },    // all 6 dots = ঢ
  { 0b100001, nullptr, "ছ" },    // dots 16 = ছ
  { 0b100011, nullptr, "ঘ" },    // dots 126 = ঘ
  { 0b011000, nullptr, "ভ" },    // dots 45 = ভ (you said 245 but জ is already there, 45 per standard Bharati)
  { 0b111001, nullptr, "থ" },    // dots 1456 = থ
  { 0b110110, nullptr, "ঠ" },    // dots 2456 = ঠ
  { 0b101010, nullptr, "ঔ" },    // dots 246 = ঔ
  { 0b010110, nullptr, "ফ" },    // dots 235 = ফ
  { 0b110100, nullptr, "ঝ" },    // dots 356 = ঝ
  { 0b101011, nullptr, "ড" },    // dots 1246 = ড
  { 0b010100, nullptr, "ঈ" },    // dots 35 = ঈ

  // ===== Additional Bharati cells (not in original dict) =====
  { 0b011110, nullptr, "ত" },    // dots 2345 = ত
  { 0b101000, nullptr, "খ" },    // dots 46 = খ
  { 0b101100, nullptr, "ঙ" },    // dots 346 = ঙ
  { 0b111110, nullptr, "ট" },    // dots 23456 = ট
  { 0b101110, nullptr, "ধ" },    // dots 2346 = ধ
  { 0b111100, nullptr, "ণ" },    // dots 3456 = ণ
  { 0b110011, nullptr, "ঊ" },    // dots 1256 = ঊ
  { 0b101111, nullptr, "ষ" },    // dots 12346 = ষ
  { 0b110001, nullptr, "শ" },    // dots 156 = শ
  { 0b110000, nullptr, "ং" },    // dots 56 = অনুস্বার
  // ঃ (visarga) at dot 6 (0b100000) — available for future use
  { 0b010000, nullptr, "ঁ" },    // dot 5 = চন্দ্রবিন্দু

  // ===== Non-standard convenience chords =====
  { 0b100110, nullptr, "ি" },    // ই-কার (convenience, not a Bharati cell)
  { 0b110010, nullptr, "ূ" },    // দীর্ঘ উ-কার (convenience, not a Bharati cell)
  // ড় moved to shared section with z at 0b110101
  { 0b100010, nullptr, "স" },    // duplicate স at dots 236 (convenience)
};

// Number mappings for Shift + a-j
const char* numberMap[] = { "1", "2", "3", "4", "5", "6", "7", "8", "9", "0" };

// Chords for a-j (used for number lookup)
const uint8_t numberChords[] = {
  0b000001,  // a → 1
  0b000011,  // b → 2
  0b001001,  // c → 3
  0b011001,  // d → 4
  0b010001,  // e → 5
  0b001011,  // f → 6
  0b011011,  // g → 7
  0b010011,  // h → 8
  0b001000,  // i → 9
  0b011010,  // j → 0
};

// Shift symbols — math & punctuation via Shift + chord (language-independent)
// Note: some punctuation shares chord values with math; math entries come first in conflicts.
struct ShiftSymbol {
  uint8_t chord;
  const char* symbol;
};

const ShiftSymbol shiftSymbols[] = {
  // Math symbols
  { 0b010110, "+" },   // dots 235 = plus
  { 0b100100, "-" },   // dots 36  = minus
  { 0b100110, "×" },   // dots 236 = times
  { 0b110110, "=" },   // dots 2356 = equals
  { 0b001100, "÷" },   // dots 34  = divide

  // Punctuation & decimal
  { 0b000010, "," },   // dot 2   = comma
  { 0b000110, ";" },   // dots 23 = semicolon
  { 0b010010, ":" },   // dots 25 = colon
  { 0b110010, "." },   // dots 256 = decimal point / period
};

// Bangla vowel → vowel sign mapping (Shift + vowel → kar/matra)
struct BanglaShiftEntry {
  uint8_t chord;
  const char* kar; // vowel sign
};

const BanglaShiftEntry banglaShiftMap[] = {
  { 0b000001, nullptr },   // অ → (no sign)
  { 0b011100, "া" },       // আ → আ-কার  (Bharati: dots 345)
  { 0b001010, "ি" },       // ই → ই-কার  (Bharati: dots 24)
  { 0b010100, "ী" },       // ঈ → দীর্ঘ ই-কার (Bharati: dots 35)
  { 0b100101, "ু" },       // উ → উ-কার  (Bharati: dots 136)
  { 0b110011, "ূ" },       // ঊ → দীর্ঘ উ-কার (Bharati: dots 1256)
  { 0b010001, "ে" },       // এ → এ-কার  (Bharati: dots 15)
  { 0b001100, "ৈ" },       // ঐ → ঐ-কার  (Bharati: dots 34)
  { 0b010101, "ো" },       // ও → ও-কার  (Bharati: dots 135)
  { 0b101010, "ৌ" },       // ঔ → ঔ-কার  (Bharati: dots 246)
};

// ==========================================
// FORWARD DECLARATIONS (used by the BLE layer & loop)
// ==========================================
extern bool isBangla;
void sendChar(const char* c);
void sendBackspace();
void processChord(int chord);

// ==========================================
// BLE — PROVEN HID KEYBOARD + NORDIC UART (NUS)
// ==========================================
// The HID service is built with BLEHIDDevice — the same helper class the
// proven T-vK BleKeyboard library uses — so phones and PCs pair and type
// exactly as they did before the v2 rewrite (phones had stopped working).
// Same public API surface the rest of this sketch already used:
//   begin() / isConnected() / print() / press() / releaseAll()

#define HID_SERVICE_UUID        0x1812
#define CCCD_UUID               0x2902

// Standard Nordic UART Service UUIDs (see PHONE.md §1.1)
#define NUS_SERVICE_UUID "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
#define NUS_TX_UUID      "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"  // ESP32 → phone (notify)
#define NUS_RX_UUID      "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"  // phone → ESP32 (write)

// Keyboard usage codes (USB HID Usage Tables)
#define KEY_BACKSPACE 0xB2   // raw usage; press() converts 0xB2 → 0x2A

// T-vK BleKeyboard's virtual keyboard USB identity — hosts recognise it,
// and it matches the pre-rewrite pairing behaviour.
#define BB_VID 0x05ac
#define BB_PID 0x820a
#define BB_VERSION 0x0210

// Boot keyboard report map — byte-identical to the one T-vK BleKeyboard
// ships (a single keyboard INPUT collection, report ID 1). Android and
// desktop hosts parse this layout unchanged.
static const uint8_t KEYBOARD_REPORT_MAP[] = {
  0x05, 0x01, 0x09, 0x06, 0xA1, 0x01, 0x01, 0x01, 0x05, 0x07,
  0x19, 0xE0, 0x29, 0xE7, 0x15, 0x00, 0x25, 0x01, 0x75, 0x01,
  0x95, 0x08, 0x81, 0x02, 0x95, 0x01, 0x75, 0x08, 0x81, 0x01,
  0x95, 0x05, 0x75, 0x01, 0x05, 0x08, 0x19, 0x01, 0x29, 0x05,
  0x91, 0x02, 0x95, 0x01, 0x75, 0x03, 0x91, 0x01, 0x95, 0x06,
  0x75, 0x08, 0x15, 0x00, 0x25, 0x65, 0x05, 0x07, 0x19, 0x00,
  0x29, 0x65, 0x81, 0x00, 0xC0
};

// ==========================================
// GATT EVENT BRIDGE
// Callbacks are defined BEFORE the BLE class and only touch plain globals
// (C++ unqualified lookup in inline member bodies can't see types declared
// after the class). loop() drains these flags via bleBridge.processEvents().
// ==========================================
volatile uint8_t g_bleEvents = 0;                 // bit0 = connect, bit1 = disconnect, bit2 = rx
String g_rxValue = "";                            // last NUS RX payload

class BrailleServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer*) override { g_bleEvents |= 0x01; }
  void onDisconnect(BLEServer*) override { g_bleEvents |= 0x02; }
};

class BrailleCharCallbacks : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic* c) override {
    g_rxValue = String(c->getValue().c_str());
    g_bleEvents |= 0x04;
  }
};

class BrailleBridgeBLE {
public:

  void begin(const char* name) {
    BLEDevice::init(name);
    // Security: bond + Secure Connections + MITM — byte-for-byte the mode
    // the working T-vK BleKeyboard build used (ESP_LE_AUTH_REQ_SC_MITM_BOND).
    BLESecurity* sec = new BLESecurity();
    sec->setAuthenticationMode(ESP_LE_AUTH_REQ_SC_MITM_BOND);
    BLEDevice::setMTU(247);  // Bangla conjuncts + control lines must not fragment badly

    BLEServer* server = BLEDevice::createServer();
    server->setCallbacks(new BrailleServerCallbacks());

    // ---------- HID keyboard service (via BLEHIDDevice, like T-vK) ----------
    // This helper produces the exact GATT layout of the previously-working
    // keyboard: 0x1812 + HIDS mandatory characteristics + Protocol Mode,
    // encrypted 0x2A4D report characteristics with 0x2908 Report Reference
    // and 0x2902 CCCDs, plus the 0x180F battery service hosts query.
    _hid = new BLEHIDDevice(server);
    _input = _hid->inputReport(1);      // report ID 1 → keyboard
    _output = _hid->outputReport(1);    // keyboard LED output (host → device)

    _hid->hidInfo(0x00, 0x01);          // country 0, flags: normally connectable
    _hid->pnp(0x02, BB_VID, BB_PID, BB_VERSION);  // USB SIG, T-vK keyboard identity
    _hid->reportMap((uint8_t*)KEYBOARD_REPORT_MAP, sizeof(KEYBOARD_REPORT_MAP));

    // ---------- Nordic UART Service (the phone-app stream) ----------
    BLEService* nus = server->createService(BLEUUID(NUS_SERVICE_UUID));

    _tx = nus->createCharacteristic(BLEUUID(NUS_TX_UUID), BLECharacteristic::PROPERTY_NOTIFY);
    _txCccd = new BLE2902();
    _tx->addDescriptor(_txCccd);   // stack updates this on CCCD writes; getNotifications() reads it

    BLECharacteristic* rx = nus->createCharacteristic(BLEUUID(NUS_RX_UUID),
      BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_WRITE_NR);
    rx->setCallbacks(new BrailleCharCallbacks());

    _hid->startServices();
    nus->start();

    // ---------- Advertising (T-vK advertising shape, plus NUS) ----------
    BLEAdvertising* adv = BLEDevice::getAdvertising();
    adv->setAppearance(HID_KEYBOARD);          // 0x03C1 — a KEYBOARD (was 0x03C2 = mouse!)
    adv->addServiceUUID(_hid->hidService()->getUUID());
    adv->addServiceUUID(BLEUUID(NUS_SERVICE_UUID));
    adv->setScanResponse(false);               // T-vK ships without scan response
    BLEDevice::startAdvertising();
  }

  bool isConnected() const { return _connCount > 0; }

  // ---------- HID keyboard output ----------
  void press(int k) {
    if (k >= 0x88) k -= 0x88;   // raw usage shorthand (KEY_BACKSPACE 0xB2 → 0x2A etc.)
    if (k >= 0xE0) { _modifiers |= (1 << (k - 0xE0)); sendReport(); return; }
    if (k <= 0 || k > 0x65) return;
    for (int i = 0; i < 6; i++) if (_keys[i] == k) { sendReport(); return; }
    for (int i = 0; i < 6; i++) if (_keys[i] == 0) { _keys[i] = (uint8_t)k; sendReport(); return; }
  }

  void release(int k) {
    if (k >= 0x88) k -= 0x88;
    if (k >= 0xE0) { _modifiers &= ~(1 << (k - 0xE0)); sendReport(); return; }
    for (int i = 0; i < 6; i++) if (_keys[i] == k) { _keys[i] = 0; sendReport(); return; }
  }

  void releaseAll() {
    _modifiers = 0;
    for (int i = 0; i < 6; i++) _keys[i] = 0;
    sendReport();
  }

  // Type an ASCII string over HID (press+release per char, like before)
  void print(const char* s) {
    for (const char* p = s; *p; p++) {
      uint8_t usage, mod;
      if (!asciiToUsage(*p, usage, mod)) continue;  // non-mappable → skip
      _modifiers = mod;
      press(usage);
      release(usage);
      _modifiers = 0;
    }
  }

  // ---------- NUS + Serial stream (the "serial line" that feeds the apps) ----------
  // Mirrors every Serial write as a BLE notification. This is the byte stream
  // the phone app subscribes to — identical content to USB Serial.
  void streamText(const char* s, bool newline) {
    Serial.print(s);
    if (newline) Serial.println();
    if (!_tx || !_connCount) return;
    String payload(s);
    if (newline) payload += '\n';
    size_t mtu = BLEDevice::getMTU();
    size_t chunk = (mtu >= 23 ? mtu - 3 : 20);
    size_t len = payload.length();
    for (size_t i = 0; i < len; i += chunk) {
      size_t n = (len - i < chunk) ? (len - i) : chunk;
      _tx->setValue((uint8_t*)payload.c_str() + i, n);
      // notify() checks each client's CCCD internally — unsubscribed
      // centrals are skipped automatically, so this is safe to call always.
      _tx->notify();
    }
  }

  void streamLine(const char* line) { streamText(line, true); }

  // ---------- callbacks ----------
  // Called from loop() — drains the callback flags set by the GATT events
  void processEvents() {
    noInterrupts();
    uint8_t events = g_bleEvents;
    g_bleEvents = 0;
    interrupts();
    if (events & 0x01) onCentralConnect();
    if (events & 0x02) onCentralDisconnect();
    if (events & 0x04) { String v = g_rxValue; onRxWrite(v); }
  }

  void onCentralConnect() { _connCount++; }
  void onCentralDisconnect() {
    _connCount--;
    if (_connCount <= 0) _connCount = 0;
    // Reset keyboard state so the next host doesn't see stuck keys
    _modifiers = 0;
    for (int i = 0; i < 6; i++) _keys[i] = 0;
    BLEDevice::startAdvertising();  // like BleKeyboard: keep discoverable
  }

  void onRxWrite(const String& value) {
    // The phone app can push control lines back over NUS. Only language
    // commands are accepted; anything else echoes the control vocabulary.
    String v = value; v.trim();
    if (v == "LANG:en")      { isBangla = false; streamLine("LANG:en"); }
    else if (v == "LANG:bn") { isBangla = true;  streamLine("LANG:bn"); }
    else                     { streamLine("Invalid"); }
  }

private:
  // BLEHIDDevice creates the encrypted report characteristics + Report
  // Reference descriptors itself, so no manual 0x2908 helper is needed.

  static bool asciiToUsage(char ch, uint8_t& usage, uint8_t& mod) {
    mod = 0;
    if (ch >= 'a' && ch <= 'z') { usage = 0x04 + (ch - 'a'); return true; }
    if (ch >= 'A' && ch <= 'Z') { usage = 0x04 + (ch - 'A'); mod = 0x40; return true; }  // 0x40 = left shift
    if (ch >= '1' && ch <= '9') { usage = 0x1E + (ch - '1'); return true; }
    switch (ch) {
      case '0': usage = 0x27; return true;
      case '!': usage = 0x1E; mod = 0x40; return true;
      case '@': usage = 0x1F; mod = 0x40; return true;
      case '#': usage = 0x20; mod = 0x40; return true;
      case '$': usage = 0x21; mod = 0x40; return true;
      case '%': usage = 0x22; mod = 0x40; return true;
      case '^': usage = 0x23; mod = 0x40; return true;
      case '&': usage = 0x24; mod = 0x40; return true;
      case '*': usage = 0x25; mod = 0x40; return true;
      case '(': usage = 0x26; mod = 0x40; return true;
      case ')': usage = 0x27; mod = 0x40; return true;
      case '\n': case '\r': usage = 0x28; return true;
      case '\b': case 0x7F: usage = 0x2A; return true;   // backspace / delete
      case '\t': usage = 0x2B; return true;
      case ' ': usage = 0x2C; return true;
      case '-': usage = 0x2D; return true;   case '_': usage = 0x2D; mod = 0x40; return true;
      case '=': usage = 0x2E; return true;   case '+': usage = 0x2E; mod = 0x40; return true;
      case '[': usage = 0x2F; return true;   case '{': usage = 0x2F; mod = 0x40; return true;
      case ']': usage = 0x30; return true;   case '}': usage = 0x30; mod = 0x40; return true;
      case '\\': usage = 0x31; return true;  case '|': usage = 0x31; mod = 0x40; return true;
      case ';': usage = 0x33; return true;   case ':': usage = 0x33; mod = 0x40; return true;
      case '\'': usage = 0x34; return true;  case '"': usage = 0x34; mod = 0x40; return true;
      case '`': usage = 0x35; return true;   case '~': usage = 0x35; mod = 0x40; return true;
      case ',': usage = 0x36; return true;   case '<': usage = 0x36; mod = 0x40; return true;
      case '.': usage = 0x37; return true;   case '>': usage = 0x37; mod = 0x40; return true;
      case '/': usage = 0x38; return true;   case '?': usage = 0x38; mod = 0x40; return true;
      default: return false;
    }
  }

  void sendReport() {
    uint8_t report[8] = { _modifiers, 0, _keys[0], _keys[1], _keys[2], _keys[3], _keys[4], _keys[5] };
    if (_input) {
      _input->setValue(report, 8);
      if (_connCount) _input->notify();
    }
  }

  BLEHIDDevice* _hid = nullptr;
  BLECharacteristic* _input = nullptr;
  BLECharacteristic* _output = nullptr;
  BLECharacteristic* _tx = nullptr;
  BLE2902* _txCccd = nullptr;
  uint8_t _modifiers = 0;
  uint8_t _keys[6] = { 0, 0, 0, 0, 0, 0 };
  int _connCount = 0;
};

BrailleBridgeBLE bleBridge;

// ==========================================
// OBJECTS & GLOBALS
// ==========================================
unsigned long pressStartTime = 0;
bool chordActive = false;
int currentChord = 0;
bool isBangla = false;
bool shiftActive = false;

// --- Shift tap → Backspace state machine ---
// Shift normally acts as a held modifier. If it is pressed AND released
// without any dot chord being composed meanwhile, that tap is a Backspace.
bool shiftWasDown = false;      // Shift was held at some point since last release
bool shiftTapUsed = false;      // a chord was processed (or Space) while Shift was held
unsigned long shiftDownTime = 0;  // when the current Shift press started
unsigned long lastBackspaceMs = 0;  // cooldown anchor so release bounce can't chain deletes
const unsigned long SHIFT_TAP_MAX_MS = 1500;  // ultra-long presses are not taps (pocket/garage protection)
const unsigned long SHIFT_TAP_MIN_MS = 25;    // shorter than this = press bounce, not a real tap
const unsigned long SHIFT_BKSP_COOLDOWN_MS = 100;  // ignore re-arms right after a fired delete

// ==========================================
// DICTIONARY LOOKUP
// ==========================================
const char* lookupChord(int chord, bool bangla) {
  for (unsigned int i = 0; i < sizeof(brailleDict) / sizeof(brailleDict[0]); i++) {
    if (brailleDict[i].chord == chord) {
      if (bangla && brailleDict[i].bangla != nullptr) return brailleDict[i].bangla;
      if (!bangla && brailleDict[i].english != nullptr) return brailleDict[i].english;
      return nullptr; // chord exists but not in this language
    }
  }
  return nullptr; // not found
}

// ==========================================
// SETUP
// ==========================================
void setup() {
  Serial.begin(115200);

  pinMode(DOT_1, INPUT_PULLUP);
  pinMode(DOT_2, INPUT_PULLUP);
  pinMode(DOT_3, INPUT_PULLUP);
  pinMode(DOT_4, INPUT_PULLUP);
  pinMode(DOT_5, INPUT_PULLUP);
  pinMode(DOT_6, INPUT_PULLUP);
  pinMode(SPACE, INPUT_PULLUP);
  pinMode(SHIFT, INPUT_PULLUP);

  // pinMode(RED_LED, OUTPUT);
  // pinMode(GREEN_LED, OUTPUT);
  // setEnglishLED(); // Start in English mode

  bleBridge.begin("BrailleBridge");
  Serial.println("SYSTEM: BrailleBridge Connected. Waiting for BLE...");
}

// ==========================================
// MAIN LOOP
// ==========================================
void loop() {
  bleBridge.processEvents();   // handle connect/disconnect/NUS-RX events

  bool d1 = digitalRead(DOT_1) == LOW;
  bool d2 = digitalRead(DOT_2) == LOW;
  bool d3 = digitalRead(DOT_3) == LOW;
  bool d4 = digitalRead(DOT_4) == LOW;
  bool d5 = digitalRead(DOT_5) == LOW;
  bool d6 = digitalRead(DOT_6) == LOW;
  bool sp = digitalRead(SPACE) == LOW;
  bool sh = digitalRead(SHIFT) == LOW;

  // ----- SHIFT MODIFIER (held while pressed, like a real keyboard Shift) -----
  shiftActive = sh;  // sh is already true when pressed (digitalRead(...)==LOW)

  // ----- SHIFT TAP → BACKSPACE -----
  // Track Shift press/release edges. A clean tap (released quickly, with no
  // chord or Space used while it was held) deletes the last typed character.
  if (sh) {
    if (!shiftWasDown) {           // falling edge: Shift just went down
      shiftWasDown = true;
      // Cooldown: if a backspace just fired, this re-arm is bounce residue,
      // not a fresh tap — mark it used so its release can't fire again.
      shiftTapUsed = (millis() - lastBackspaceMs) < SHIFT_BKSP_COOLDOWN_MS;
      shiftDownTime = millis();
    }
  } else if (shiftWasDown) {       // rising edge: Shift just came back up
    shiftWasDown = false;
    bool dotsHeld = d1 || d2 || d3 || d4 || d5 || d6;
    // Fire only on a clean tap: quick, unused, and not in the middle of a chord
    unsigned long held = millis() - shiftDownTime;
    if (!shiftTapUsed && !dotsHeld && held >= SHIFT_TAP_MIN_MS && held <= SHIFT_TAP_MAX_MS) {
      sendBackspace();
      lastBackspaceMs = millis();
      delay(30);                 // swallow release bounce so it can't double-fire
    }
    shiftTapUsed = false;
  }

  // ----- SPACE -----
  if (sp && !d1 && !d2 && !d3 && !d4 && !d5 && !d6) {
    if (sh) shiftTapUsed = true;   // Shift was doing something while held
    sendChar(" ");
    delay(200);
    while (digitalRead(SPACE) == LOW) { delay(10); }
    return;
  }

  // ----- CHORD DETECTION -----
  bool anyDot = d1 || d2 || d3 || d4 || d5 || d6;

  if (anyDot) {
    if (shiftWasDown) shiftTapUsed = true;  // dots involved → this Shift is a modifier, not a tap
    if (!chordActive) {
      chordActive = true;
      pressStartTime = millis();
      currentChord = 0;
    }

    if (d1) currentChord |= (1 << 0);
    if (d2) currentChord |= (1 << 1);
    if (d3) currentChord |= (1 << 2);
    if (d4) currentChord |= (1 << 3);
    if (d5) currentChord |= (1 << 4);
    if (d6) currentChord |= (1 << 5);
  }

  if (chordActive) {
    unsigned long elapsed = millis() - pressStartTime;
    bool allReleased = !anyDot;

    // D4+D5+D6 held 500ms → language toggle
    if (currentChord == 0b111000 && elapsed >= 500 && !allReleased) {
      isBangla = !isBangla;
      bleBridge.streamLine(isBangla ? "LANG:bn" : "LANG:en");
      if (shiftActive) shiftTapUsed = true;  // Shift was part of a deliberate gesture, not a tap
      chordActive = false;
      currentChord = 0;

      // Wait for all three keys to be released
      while (digitalRead(DOT_4) == LOW || digitalRead(DOT_5) == LOW || digitalRead(DOT_6) == LOW) {
        delay(10);
      }
      delay(50);
      return;
    }

    // Process when all released or timeout (180ms)
    if (allReleased || elapsed > 180) {
      // If D4+D5+D6 is still held and < 500ms, keep waiting
      if (!allReleased && currentChord == 0b111000 && elapsed < 500) {
        // Wait longer for potential toggle
      } else {
        if (shiftActive) shiftTapUsed = true;  // chord consumed the Shift modifier
        processChord(currentChord);
        chordActive = false;
        currentChord = 0;
        delay(50);
      }
    }
  }
}

// ==========================================
// BACKSPACE — delete the last typed character
// ==========================================
void sendBackspace() {
  if (bleBridge.isConnected()) {
    bleBridge.press(KEY_BACKSPACE);
    delay(8);
    bleBridge.releaseAll();
  }
  bleBridge.streamLine("SYSTEM:BKSP");   // teacher app listens for this control line
}

// ==========================================
// SEND CHARACTER TO BLE & STREAM
// ==========================================
void sendChar(const char* c) {
  // HID keycodes can only represent ASCII. Bangla (multi-byte UTF-8) has no
  // keycode mapping, and pushing it through the HID stack can wedge the
  // ESP32 and cause a reboot. So:
  //   - ASCII  → HID keyboard (paired host types it out) + stream
  //   - Bangla → stream only (USB Serial + BLE NUS → teacher/phone app)
  bool isAscii = true;
  for (const char* p = c; *p; p++) {
    if ((unsigned char)*p >= 0x80) { isAscii = false; break; }
  }
  if (bleBridge.isConnected() && isAscii) {
    bleBridge.print(c);
  }
  // The stream carries EVERYTHING (ASCII + Bangla + control lines) — this is
  // what the teacher software and the phone app receive.
  bleBridge.streamText(c, false);
}

// ==========================================
// PROCESS A BRAILLE CHORD
// ==========================================
void processChord(int chord) {
  // ----- SHIFTED CHORD (activated by physical SHIFT button) -----
  if (shiftActive) {
    // shiftActive follows the button state in loop(), so it resets naturally on release

    // Check for numbers (a-j chords → 1-0)
    for (int i = 0; i < 10; i++) {
      if (chord == numberChords[i]) {
        sendChar(numberMap[i]);
        // flashValid();
        return;
      }
    }

    // Check for shift symbols — math & punctuation (language-independent)
    for (unsigned int i = 0; i < sizeof(shiftSymbols) / sizeof(shiftSymbols[0]); i++) {
      if (chord == shiftSymbols[i].chord) {
        sendChar(shiftSymbols[i].symbol);
        // flashValid();
        return;
      }
    }

    // English uppercase
    if (!isBangla) {
      const char* ch = lookupChord(chord, false);
      if (ch != nullptr && ch[0] >= 'a' && ch[0] <= 'z') {
        char upper[2] = { (char)(ch[0] - 32), '\0' };
        sendChar(upper);
        // flashValid();
        return;
      }
    }
    // Bangla shifted: vowel → vowel sign (কার)
    else {
      // Check vowel sign map first
      for (unsigned int i = 0; i < sizeof(banglaShiftMap) / sizeof(banglaShiftMap[0]); i++) {
        if (banglaShiftMap[i].chord == chord) {
          if (banglaShiftMap[i].kar != nullptr) {
            sendChar(banglaShiftMap[i].kar);
            // flashValid();
            return;
          }
          // অ has no vowel sign → fall through to normal output
          break;
        }
      }

      // Not a vowel chord, or অ → output normal Bangla character
      const char* ch = lookupChord(chord, true);
      if (ch != nullptr) {
        sendChar(ch);
        // flashValid();
        return;
      }
    }

    // Unknown shifted chord → silently ignore
    // flashInvalid();
    // Serial.println("Invalid");
    return;
  }

  // ----- NORMAL (UNSHIFTED) CHORD -----
  const char* result = lookupChord(chord, isBangla);
  if (result != nullptr) {
    sendChar(result);
  }
  // Unknown chord → silently ignore
}
