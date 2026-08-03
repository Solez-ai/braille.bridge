#include <BleKeyboard.h>

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
{ 0b101101, "x", "য়" },     // dots 1346 = য় (yya) — convenience
{ 0b111101, "y", "য" },     // dots 13456 = য
{ 0b110101, "z", "ড়" },     // dots 1356 = z + ড়

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
  // ড় moved to shared section with z at 0b110101
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
// OBJECTS & GLOBALS
// ==========================================
BleKeyboard bleKeyboard("BrailleBridge", "StudentProject", 100);

unsigned long pressStartTime = 0;
bool chordActive = false;
int currentChord = 0;
bool isBangla = false;
bool shiftActive = false;

// ==========================================
// LED HELPERS (DISABLED)
// ==========================================
// void setEnglishLED() {
//   digitalWrite(RED_LED, HIGH);
//   digitalWrite(GREEN_LED, LOW);
// }
//
// void setBanglaLED() {
//   digitalWrite(RED_LED, LOW);
//   digitalWrite(GREEN_LED, HIGH);
// }
//
// void updateLEDs() {
//   if (isBangla) {
//     setBanglaLED();
//   } else {
//     setEnglishLED();
//   }
// }
//
// void flashValid() {
//   digitalWrite(RED_LED, HIGH);
//   digitalWrite(GREEN_LED, HIGH);
//   delay(100);
//   updateLEDs();
// }
//
// void flashInvalid() {
//   for (int i = 0; i < 3; i++) {
//     digitalWrite(RED_LED, HIGH);
//     digitalWrite(GREEN_LED, HIGH);
//     delay(150);
//     digitalWrite(RED_LED, LOW);
//     digitalWrite(GREEN_LED, LOW);
//     delay(150);
//   }
//   updateLEDs();
// }

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

  bleKeyboard.begin();
  Serial.println("SYSTEM: BrailleBridge Connected. Waiting for BLE...");
}

// ==========================================
// MAIN LOOP
// ==========================================
void loop() {
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

  // ----- SPACE -----
  if (sp && !d1 && !d2 && !d3 && !d4 && !d5 && !d6) {
    sendChar(" ");
    delay(200);
    while (digitalRead(SPACE) == LOW) { delay(10); }
    return;
  }

  // ----- CHORD DETECTION -----
  bool anyDot = d1 || d2 || d3 || d4 || d5 || d6;

  if (anyDot) {
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
      Serial.println(isBangla ? "LANG:bn" : "LANG:en");
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
        processChord(currentChord);
        chordActive = false;
        currentChord = 0;
        delay(50);
      }
    }
  }
}

// ==========================================
// SEND CHARACTER TO BLE & SERIAL
// ==========================================
void sendChar(const char* c) {
  if (bleKeyboard.isConnected()) {
    bleKeyboard.print(c);
  }
  Serial.print(c);
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
