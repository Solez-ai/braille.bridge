// ============================================================================
// BrailleBridge 2 — Multi-Student Classroom Demo Firmware (ESP32 #1)
// Bluetooth Name: "BrailleBridge 2"
//
// Behavior:
// - Advertises over Bluetooth Low Energy as "BrailleBridge 2" with the
//   Nordic UART Service (NUS) expected by the BrailleBridge Teacher Software.
// - Waits until the Teacher Software connects to it (or sends SYSTEM:START).
// - Immediately begins typing a beginner-sized description of BrailleBridge
//   at a natural beginner Perkins Brailler chording pace (character-by-character,
//   with realistic finger-placement delays, word/sentence pauses, Dot-6 capital
//   pauses, and occasional beginner self-corrections via SYSTEM:BKSP).
// ============================================================================

#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

#define DEVICE_BLE_NAME  "BrailleBridge 2"

#define NUS_SERVICE_UUID "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
#define NUS_TX_UUID      "6E400002-B5A3-F393-E0A9-E50E24DCCA9E" // ESP32 -> Teacher App (Notify)
#define NUS_RX_UUID      "6E400003-B5A3-F393-E0A9-E50E24DCCA9E" // Teacher App -> ESP32 (Write)

BLEServer* pServer = nullptr;
BLECharacteristic* pTxChar = nullptr;
BLE2902* pTx2902 = nullptr;

volatile bool bleConnected = false;
volatile bool startRequested = false;
volatile unsigned long connectedAtMs = 0;

// Beginner-sized paragraph describing BrailleBridge (written from a student's perspective)
const char* DEMO_TEXT =
  "BrailleBridge is a smart braille writer for students like me. "
  "It uses six dot keys just like a Perkins Brailler and connects to my teacher over Bluetooth. "
  "As I press each chord, my teacher can read my document live on the screen and help me learn.";

size_t textIndex = 0;
bool typingActive = false;
unsigned long nextActionMs = 0;

// Typo state machine for realistic beginner Perkins Brailler self-correction
enum TypoPhase { TYPO_NONE, TYPO_WAIT_BEFORE_BKSP, TYPO_WAIT_AFTER_BKSP };
TypoPhase typoPhase = TYPO_NONE;

void sendRaw(const char* s, bool withNewline) {
  Serial.print(s);
  if (withNewline) Serial.println();

  if (bleConnected && pTxChar != nullptr) {
    String payload = String(s);
    if (withNewline) payload += "\n";
    pTxChar->setValue((uint8_t*)payload.c_str(), payload.length());
    pTxChar->notify();
  }
}

void restartTyping(unsigned long delayBeforeFirstCharMs) {
  textIndex = 0;
  typoPhase = TYPO_NONE;
  typingActive = true;
  nextActionMs = millis() + delayBeforeFirstCharMs;
}

class ServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer* s) override {
    bleConnected = true;
    connectedAtMs = millis();
    if (pTx2902) pTx2902->setNotifications(true);
    startRequested = true;
  }

  void onDisconnect(BLEServer* s) override {
    bleConnected = false;
    typingActive = false;
    textIndex = 0;
    typoPhase = TYPO_NONE;
    if (pTx2902) pTx2902->setNotifications(false);
    BLEDevice::startAdvertising();
  }
};

class RxCallbacks : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic* c) override {
    String rx = c->getValue().c_str();
    rx.trim();
    if (rx == "SYSTEM:START" || rx == "RESET") {
      startRequested = true;
    }
  }
};

// Pick a realistic beginner Perkins Brailler delay before the next character
unsigned long nextPerkinsDelay(char justTyped, char upcoming) {
  if (justTyped == '.' || justTyped == '!') {
    return random(2300, 3300); // End-of-sentence pause to think about next sentence
  }
  if (justTyped == ',') {
    return random(1400, 2000); // Mid-sentence clause pause
  }
  if (justTyped == ' ') {
    return random(1100, 1750); // Pause between words before chording next word
  }
  if (upcoming >= 'A' && upcoming <= 'Z') {
    return random(1250, 1750); // Extra time to press Dot-6 capital sign + letter chord
  }
  return random(650, 1150);    // Normal beginner 6-key chord rhythm
}

void setup() {
  Serial.begin(115200);
  randomSeed(esp_random());

  BLEDevice::init(DEVICE_BLE_NAME);
  BLEDevice::setMTU(247);

  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new ServerCallbacks());

  BLEService* nus = pServer->createService(BLEUUID(NUS_SERVICE_UUID));

  pTxChar = nus->createCharacteristic(
    BLEUUID(NUS_TX_UUID),
    BLECharacteristic::PROPERTY_NOTIFY
  );
  pTx2902 = new BLE2902();
  pTxChar->addDescriptor(pTx2902);

  BLECharacteristic* pRxChar = nus->createCharacteristic(
    BLEUUID(NUS_RX_UUID),
    BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_WRITE_NR
  );
  pRxChar->setCallbacks(new RxCallbacks());

  nus->start();

  BLEAdvertising* adv = BLEDevice::getAdvertising();
  adv->addServiceUUID(BLEUUID(NUS_SERVICE_UUID));
  adv->setScanResponse(true);
  adv->setMinPreferred(0x06);
  BLEDevice::startAdvertising();

  Serial.println("SYSTEM: BrailleBridge 2 ready and advertising over BLE.");
}

void loop() {
  // Also allow USB Serial trigger if tested over USB cable
  while (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "SYSTEM:START" || cmd == "RESET") {
      bleConnected = true;
      startRequested = true;
    }
  }

  if (startRequested) {
    startRequested = false;
    // Wait 1.5s after BLE connection so GATT notification subscription is settled
    restartTyping(1500);
  }

  if (!bleConnected || !typingActive) {
    delay(10);
    return;
  }

  unsigned long now = millis();
  if ((long)(now - nextActionMs) < 0) {
    delay(10);
    return;
  }

  size_t totalLen = strlen(DEMO_TEXT);
  if (textIndex >= totalLen) {
    // Finished writing the beginner paragraph; pause 15s, then stay idle until reconnected/cleared
    typingActive = false;
    return;
  }

  // Handle beginner self-correction (wrong chord -> pause -> backspace -> pause -> right chord)
  if (typoPhase == TYPO_WAIT_BEFORE_BKSP) {
    sendRaw("SYSTEM:BKSP", true);
    typoPhase = TYPO_WAIT_AFTER_BKSP;
    nextActionMs = now + random(650, 980);
    return;
  }

  char ch = DEMO_TEXT[textIndex];

  if (typoPhase == TYPO_NONE && ch >= 'a' && ch <= 'z' && textIndex > 4 && random(0, 100) < 4) {
    // 4% chance on lowercase letters: beginner presses an adjacent wrong chord first
    char wrongChar = (ch == 'e') ? 'i' : ((ch == 'a') ? 'b' : 'e');
    char wrongStr[2] = { wrongChar, '\0' };
    sendRaw(wrongStr, false);
    typoPhase = TYPO_WAIT_BEFORE_BKSP;
    nextActionMs = now + random(850, 1250); // Pause realizing the mistake
    return;
  }

  typoPhase = TYPO_NONE;

  // If uppercase, emit Dot-6 capital indicator first
  if (ch >= 'A' && ch <= 'Z') {
    sendRaw("SYSTEM:CAP_ONCE", true);
  }

  char out[2] = { ch, '\0' };
  sendRaw(out, false);
  textIndex++;

  char upcoming = (textIndex < totalLen) ? DEMO_TEXT[textIndex] : ' ';
  nextActionMs = now + nextPerkinsDelay(ch, upcoming);
}
