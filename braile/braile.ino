#include <Arduino.h>
#include "BBKeyboard.h"

#define DOT_1 14
#define DOT_2 12
#define DOT_3 13
#define DOT_4 27
#define DOT_5 26
#define DOT_6 25
#define SPACE 33
#define SHIFT 32
// Shift: hold for uppercase/numbers/math/Bangla vowel signs.
// Tapping Shift alone deletes the last character.

// #define RED_LED 18
// #define GREEN_LED 19

struct BrailleEntry {
  uint8_t chord;
  const char* english;
  const char* bangla;
};

// Bharati Braille cells (en.wikipedia.org/wiki/Bharati_Braille).
const BrailleEntry brailleDict[] = {
// Shared English + Bangla chords
{ 0b000001, "a", "অ" },     // dot 1 = অ
{ 0b000011, "b", "ব" },     // dots 12 = ব
{ 0b001001, "c", "চ" },     // dots 14 = চ
{ 0b011001, "d", "দ" },     // dots 145 = দ
{ 0b010001, "e", "এ" },     // dots 15 = এ
{ 0b001011, "f", nullptr },  // dots 124
{ 0b011011, "g", "গ" },     // dots 1245 = গ
{ 0b010011, "h", "হ" },     // dots 125 = হ
{ 0b001000, "i", "্" },     // dot 4 = hasanta (virama)
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
{ 0b100111, "v", "ৱ" },     // dots 1236 = ৱ
{ 0b111010, "w", nullptr },  // dots 2456
{ 0b101101, "x", "য" },     // dots 1346 = য
{ 0b111101, "y", "য" },     // dots 13456 = য
{ 0b110101, "z", "ড়" },     // dots 1356 = ড়

// Bangla-only standard cells
{ 0b001010, nullptr, "ই" },    // dots 24
{ 0b010010, nullptr, "ঞ" },    // dots 25
{ 0b001110, nullptr, "স" },    // dots 234
{ 0b111111, nullptr, "ঢ" },    // dots 123456
{ 0b100001, nullptr, "ছ" },    // dots 16
{ 0b100011, nullptr, "ঘ" },    // dots 126
{ 0b011000, nullptr, "ভ" },    // dots 45
{ 0b111001, nullptr, "থ" },    // dots 1456
{ 0b110110, nullptr, "ঠ" },    // dots 2456
{ 0b101010, nullptr, "ঔ" },    // dots 246
{ 0b010110, nullptr, "ফ" },    // dots 235
{ 0b110100, nullptr, "ঝ" },    // dots 356
{ 0b101011, nullptr, "ড" },    // dots 1246
{ 0b010100, nullptr, "ঈ" },    // dots 35

// Additional Bharati cells
{ 0b011110, nullptr, "ত" },    // dots 2345
{ 0b101000, nullptr, "খ" },    // dots 46
{ 0b101100, nullptr, "ঙ" },    // dots 346
{ 0b111110, nullptr, "ট" },    // dots 23456
{ 0b101110, nullptr, "ধ" },    // dots 2346
{ 0b111100, nullptr, "ণ" },    // dots 3456
{ 0b110011, nullptr, "ঊ" },    // dots 1256
{ 0b101111, nullptr, "ষ" },    // dots 12346
{ 0b110001, nullptr, "শ" },    // dots 156
{ 0b110000, nullptr, "ং" },    // dots 56 = anusvara
// ঃ (visarga) at dot 6 (0b100000) — free for future use
{ 0b010000, nullptr, "ঁ" },    // dot 5 = chandrabindu

// Convenience chords (not standard Bharati cells)
{ 0b100110, nullptr, "ি" },    // i-kar
{ 0b110010, nullptr, "ূ" },    // dirgho u-kar
{ 0b100010, nullptr, "স" },    // স at dots 236
};

// Shift + a-j chords produce digits 1–0.
const char* numberMap[] = { "1", "2", "3", "4", "5", "6", "7", "8", "9", "0" };

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

// Shift + chord math/punctuation, language-independent.
struct ShiftSymbol {
  uint8_t chord;
  const char* symbol;
};

const ShiftSymbol shiftSymbols[] = {
  { 0b010110, "+" },   // dots 235
  { 0b100100, "-" },   // dots 36
  { 0b100110, "×" },   // dots 236
  { 0b110110, "=" },   // dots 2356
  { 0b001100, "÷" },   // dots 34
  { 0b000010, "," },   // dot 2
  { 0b000110, ";" },   // dots 23
  { 0b010010, ":" },   // dots 25
  { 0b110010, "." },   // dots 256
};

// Shift + vowel chord → Bangla kar (matra).
struct BanglaShiftEntry {
  uint8_t chord;
  const char* kar;
};

const BanglaShiftEntry banglaShiftMap[] = {
  { 0b000001, nullptr },   // অ has no sign
  { 0b011100, "া" },       // আ-কার
  { 0b001010, "ি" },       // ই-কার
  { 0b010100, "ী" },       // ঈ-কার
  { 0b100101, "ু" },       // উ-কার
  { 0b110011, "ূ" },       // ঊ-কার
  { 0b010001, "ে" },       // এ-কার
  { 0b001100, "ৈ" },       // ঐ-কার
  { 0b010101, "ো" },       // ও-কার
  { 0b101010, "ৌ" },       // ঔ-কার
};

extern bool isBangla;
void sendChar(const char* c);
void sendBackspace();
void processChord(int chord);

BBKeyboard bleKeyboard("BrailleBridge");

// Send to both outputs: USB Serial and BLE NUS.
void streamOut(const char* s, bool newline) {
  Serial.print(s);
  if (newline) Serial.println();
  bleKeyboard.streamText(s, newline);
}

// Control lines arriving from the phone over NUS RX.
void onNusControl(const String& value) {
  String v = value; v.trim();
  if (v == "LANG:en")      { isBangla = false; streamOut("LANG:en", true); }
  else if (v == "LANG:bn") { isBangla = true;  streamOut("LANG:bn", true); }
  else                     { streamOut("Invalid", true); }
}

unsigned long pressStartTime = 0;
bool chordActive = false;
int currentChord = 0;
bool isBangla = false;
bool shiftActive = false;

// Shift tap = backspace. Shift stays a modifier while dots are held; a quick
// press+release with no chord in between deletes one character.
bool shiftWasDown = false;
bool shiftTapUsed = false;
unsigned long shiftDownTime = 0;
unsigned long lastBackspaceMs = 0;
const unsigned long SHIFT_TAP_MAX_MS = 1500;      // long presses are not taps
const unsigned long SHIFT_TAP_MIN_MS = 25;        // shorter = bounce, not a tap
const unsigned long SHIFT_BKSP_COOLDOWN_MS = 100; // stops release bounce double-firing

const char* lookupChord(int chord, bool bangla) {
  for (unsigned int i = 0; i < sizeof(brailleDict) / sizeof(brailleDict[0]); i++) {
    if (brailleDict[i].chord == chord) {
      if (bangla && brailleDict[i].bangla != nullptr) return brailleDict[i].bangla;
      if (!bangla && brailleDict[i].english != nullptr) return brailleDict[i].english;
      return nullptr;
    }
  }
  return nullptr;
}

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
  // setEnglishLED();

  bleKeyboard.begin();
  bleKeyboard.setNusRxHandler(onNusControl);
  Serial.println("SYSTEM: BrailleBridge Connected. Waiting for BLE...");
}

void loop() {
  bleKeyboard.processEvents();

  bool d1 = digitalRead(DOT_1) == LOW;
  bool d2 = digitalRead(DOT_2) == LOW;
  bool d3 = digitalRead(DOT_3) == LOW;
  bool d4 = digitalRead(DOT_4) == LOW;
  bool d5 = digitalRead(DOT_5) == LOW;
  bool d6 = digitalRead(DOT_6) == LOW;
  bool sp = digitalRead(SPACE) == LOW;
  bool sh = digitalRead(SHIFT) == LOW;

  shiftActive = sh;

  // Shift press/release edge tracking for the tap-to-backspace gesture.
  if (sh) {
    if (!shiftWasDown) {
      shiftWasDown = true;
      // If a backspace just fired, this re-arm is bounce residue — mark it
      // used so its release cannot fire again.
      shiftTapUsed = (millis() - lastBackspaceMs) < SHIFT_BKSP_COOLDOWN_MS;
      shiftDownTime = millis();
    }
  } else if (shiftWasDown) {
    shiftWasDown = false;
    bool dotsHeld = d1 || d2 || d3 || d4 || d5 || d6;
    unsigned long held = millis() - shiftDownTime;
    if (!shiftTapUsed && !dotsHeld && held >= SHIFT_TAP_MIN_MS && held <= SHIFT_TAP_MAX_MS) {
      sendBackspace();
      lastBackspaceMs = millis();
      delay(30);  // swallow release bounce
    }
    shiftTapUsed = false;
  }

  // Space inserts a space only when no dot is held.
  if (sp && !d1 && !d2 && !d3 && !d4 && !d5 && !d6) {
    if (sh) shiftTapUsed = true;
    sendChar(" ");
    delay(200);
    while (digitalRead(SPACE) == LOW) { delay(10); }
    return;
  }

  bool anyDot = d1 || d2 || d3 || d4 || d5 || d6;

  if (anyDot) {
    if (shiftWasDown) shiftTapUsed = true;  // Shift is a modifier here, not a tap
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

    // D4+D5+D6 held for 500ms toggles the language.
    if (currentChord == 0b111000 && elapsed >= 500 && !allReleased) {
      isBangla = !isBangla;
      streamOut(isBangla ? "LANG:bn" : "LANG:en", true);
      if (shiftActive) shiftTapUsed = true;
      chordActive = false;
      currentChord = 0;

      while (digitalRead(DOT_4) == LOW || digitalRead(DOT_5) == LOW || digitalRead(DOT_6) == LOW) {
        delay(10);
      }
      delay(50);
      return;
    }

    // A chord commits when all dots release or after 180ms, but D4+D5+D6
    // waits up to 500ms so a language toggle can still be detected.
    if (allReleased || elapsed > 180) {
      if (!allReleased && currentChord == 0b111000 && elapsed < 500) {
        // keep waiting
      } else {
        if (shiftActive) shiftTapUsed = true;
        processChord(currentChord);
        chordActive = false;
        currentChord = 0;
        delay(50);
      }
    }
  }
}

void sendBackspace() {
  if (bleKeyboard.isConnected()) {
    bleKeyboard.press(KEY_BACKSPACE);
    delay(8);
    bleKeyboard.releaseAll();
  }
  streamOut("SYSTEM:BKSP", true);
}

void sendChar(const char* c) {
  // HID keycodes cover ASCII only; pushing multi-byte UTF-8 (Bangla) through
  // the HID stack can wedge the ESP32. So ASCII goes to HID + stream, Bangla
  // goes to the stream only.
  bool isAscii = true;
  for (const char* p = c; *p; p++) {
    if ((unsigned char)*p >= 0x80) { isAscii = false; break; }
  }
  if (bleKeyboard.isConnected() && isAscii) {
    bleKeyboard.print(c);
  }
  streamOut(c, false);
}

void processChord(int chord) {
  if (shiftActive) {
    // Numbers (a-j chords → 1-0)
    for (int i = 0; i < 10; i++) {
      if (chord == numberChords[i]) {
        sendChar(numberMap[i]);
        return;
      }
    }

    // Math & punctuation
    for (unsigned int i = 0; i < sizeof(shiftSymbols) / sizeof(shiftSymbols[0]); i++) {
      if (chord == shiftSymbols[i].chord) {
        sendChar(shiftSymbols[i].symbol);
        return;
      }
    }

    // English uppercase
    if (!isBangla) {
      const char* ch = lookupChord(chord, false);
      if (ch != nullptr && ch[0] >= 'a' && ch[0] <= 'z') {
        char upper[2] = { (char)(ch[0] - 32), '\0' };
        sendChar(upper);
        return;
      }
    }
    // Bangla: vowel chord → kar (matra)
    else {
      for (unsigned int i = 0; i < sizeof(banglaShiftMap) / sizeof(banglaShiftMap[0]); i++) {
        if (banglaShiftMap[i].chord == chord) {
          if (banglaShiftMap[i].kar != nullptr) {
            sendChar(banglaShiftMap[i].kar);
            return;
          }
          break;  // অ has no sign — fall through to normal output
        }
      }

      const char* ch = lookupChord(chord, true);
      if (ch != nullptr) {
        sendChar(ch);
        return;
      }
    }

    // Unknown shifted chord: ignore
    return;
  }

  // Unshifted chord
  const char* result = lookupChord(chord, isBangla);
  if (result != nullptr) {
    sendChar(result);
  }
}
