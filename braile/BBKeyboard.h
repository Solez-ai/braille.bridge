// ============================================================================
// BBKeyboard — vendored from T-vK's ESP32_BLE_Keyboard (BleKeyboard v0.0.4)
// ============================================================================
// WHY THIS FILE EXISTS
//   The v1 firmware used the BleKeyboard library and Bluetooth pairing/typing
//   worked on phones AND PCs. The v2/v3 rewrites replaced it with hand-rolled
//   GATT code and broke discoverability + typing (report-map tag bug,
//   advertising overflow). Per decision: return to the PROVEN library code.
//
//   The only modifications from upstream BleKeyboard are marked "NUS ADDITION"
//   below. Everything else — report map, BLEHIDDevice usage, security mode,
//   advertising shape, pairing callbacks — is byte-for-byte T-vK 0.0.4.
//   Do not "clean up" the upstream parts; they are the reason it works.
//
//   NUS ADDITION (the one new feature): a Nordic UART Service so the
//   BrailleBridge phone app can read the same character/control-line stream
//   that goes to USB Serial. NUS lives on its own service UUID; it does NOT
//   change HID behaviour, the report map, or the advertising payload.
// ============================================================================

#ifndef BB_KEYBOARD_H
#define BB_KEYBOARD_H

#include <Arduino.h>   // String, Print — used by the NUS stream API
#include "sdkconfig.h"
#if defined(CONFIG_BT_ENABLED)

#include "BLEHIDDevice.h"
#include "BLECharacteristic.h"

class BLE2902;  // only used as a pointer here; full type included in the .cpp

#include "Print.h"

// NUS ADDITION: standard Nordic UART Service UUIDs (PHONE.md §1.1)
#define NUS_SERVICE_UUID "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
#define NUS_TX_UUID      "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"  // ESP32 → phone (notify)
#define NUS_RX_UUID      "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"  // phone → ESP32 (write)

const uint8_t KEY_LEFT_CTRL = 0x80;
const uint8_t KEY_LEFT_SHIFT = 0x81;
const uint8_t KEY_LEFT_ALT = 0x82;
const uint8_t KEY_LEFT_GUI = 0x83;
const uint8_t KEY_RIGHT_CTRL = 0x84;
const uint8_t KEY_RIGHT_SHIFT = 0x85;
const uint8_t KEY_RIGHT_ALT = 0x86;
const uint8_t KEY_RIGHT_GUI = 0x87;

const uint8_t KEY_UP_ARROW = 0xDA;
const uint8_t KEY_DOWN_ARROW = 0xD9;
const uint8_t KEY_LEFT_ARROW = 0xD8;
const uint8_t KEY_RIGHT_ARROW = 0xD7;
const uint8_t KEY_BACKSPACE = 0xB2;
const uint8_t KEY_TAB = 0xB3;
const uint8_t KEY_RETURN = 0xB0;
const uint8_t KEY_ESC = 0xB1;
const uint8_t KEY_INSERT = 0xD1;
const uint8_t KEY_PRTSC = 0xCE;
const uint8_t KEY_DELETE = 0xD4;
const uint8_t KEY_PAGE_UP = 0xD3;
const uint8_t KEY_PAGE_DOWN = 0xD6;
const uint8_t KEY_HOME = 0xD2;
const uint8_t KEY_END = 0xD5;
const uint8_t KEY_CAPS_LOCK = 0xC1;
const uint8_t KEY_F1 = 0xC2;
const uint8_t KEY_F2 = 0xC3;
const uint8_t KEY_F3 = 0xC4;
const uint8_t KEY_F4 = 0xC5;
const uint8_t KEY_F5 = 0xC6;
const uint8_t KEY_F6 = 0xC7;
const uint8_t KEY_F7 = 0xC8;
const uint8_t KEY_F8 = 0xC9;
const uint8_t KEY_F9 = 0xCA;
const uint8_t KEY_F10 = 0xCB;
const uint8_t KEY_F11 = 0xCC;
const uint8_t KEY_F12 = 0xCD;
const uint8_t KEY_F13 = 0xF0;
const uint8_t KEY_F14 = 0xF1;
const uint8_t KEY_F15 = 0xF2;
const uint8_t KEY_F16 = 0xF3;
const uint8_t KEY_F17 = 0xF4;
const uint8_t KEY_F18 = 0xF5;
const uint8_t KEY_F19 = 0xF6;
const uint8_t KEY_F20 = 0xF7;
const uint8_t KEY_F21 = 0xF8;
const uint8_t KEY_F22 = 0xF9;
const uint8_t KEY_F23 = 0xFA;
const uint8_t KEY_F24 = 0xFB;

const uint8_t KEY_NUM_0 = 0xEA;
const uint8_t KEY_NUM_1 = 0xE1;
const uint8_t KEY_NUM_2 = 0xE2;
const uint8_t KEY_NUM_3 = 0xE3;
const uint8_t KEY_NUM_4 = 0xE4;
const uint8_t KEY_NUM_5 = 0xE5;
const uint8_t KEY_NUM_6 = 0xE6;
const uint8_t KEY_NUM_7 = 0xE7;
const uint8_t KEY_NUM_8 = 0xE8;
const uint8_t KEY_NUM_9 = 0xE9;
const uint8_t KEY_NUM_SLASH = 0xDC;
const uint8_t KEY_NUM_ASTERISK = 0xDD;
const uint8_t KEY_NUM_MINUS = 0xDE;
const uint8_t KEY_NUM_PLUS = 0xDF;
const uint8_t KEY_NUM_ENTER = 0xE0;
const uint8_t KEY_NUM_PERIOD = 0xEB;

typedef uint8_t MediaKeyReport[2];

const MediaKeyReport KEY_MEDIA_NEXT_TRACK = {1, 0};
const MediaKeyReport KEY_MEDIA_PREVIOUS_TRACK = {2, 0};
const MediaKeyReport KEY_MEDIA_STOP = {4, 0};
const MediaKeyReport KEY_MEDIA_PLAY_PAUSE = {8, 0};
const MediaKeyReport KEY_MEDIA_MUTE = {16, 0};
const MediaKeyReport KEY_MEDIA_VOLUME_UP = {32, 0};
const MediaKeyReport KEY_MEDIA_VOLUME_DOWN = {64, 0};
const MediaKeyReport KEY_MEDIA_WWW_HOME = {128, 0};
const MediaKeyReport KEY_MEDIA_LOCAL_MACHINE_BROWSER = {0, 1}; // Opens "My Computer" on Windows
const MediaKeyReport KEY_MEDIA_CALCULATOR = {0, 2};
const MediaKeyReport KEY_MEDIA_WWW_BOOKMARKS = {0, 4};
const MediaKeyReport KEY_MEDIA_WWW_SEARCH = {0, 8};
const MediaKeyReport KEY_MEDIA_WWW_STOP = {0, 16};
const MediaKeyReport KEY_MEDIA_WWW_BACK = {0, 32};
const MediaKeyReport KEY_MEDIA_CONSUMER_CONTROL_CONFIGURATION = {0, 64}; // Media Selection
const MediaKeyReport KEY_MEDIA_EMAIL_READER = {0, 128};


//  Low level key report: up to 6 keys and shift, ctrl etc at once
typedef struct
{
  uint8_t modifiers;
  uint8_t reserved;
  uint8_t keys[6];
} KeyReport;

class BBKeyboard : public Print, public BLEServerCallbacks, public BLECharacteristicCallbacks
{
private:
  BLEHIDDevice* hid;
  BLECharacteristic* inputKeyboard;
  BLECharacteristic* outputKeyboard;
  BLECharacteristic* inputMediaKeys;
  BLEAdvertising*    advertising;
  KeyReport          _keyReport;
  MediaKeyReport     _mediaKeyReport;
  std::string        deviceName;
  std::string        deviceManufacturer;
  uint8_t            batteryLevel;
  bool               connected = false;
  uint32_t           _delay_ms = 7;
  void delay_ms(uint64_t ms);

  uint16_t vid       = 0x05ac;
  uint16_t pid       = 0x820a;
  uint16_t version   = 0x0210;

  // ---- NUS ADDITION: state (upstream BleKeyboard has nothing below) ----
  static const uint8_t NUS_EVT_CONNECT = 1;      // deferred event codes
  static const uint8_t NUS_EVT_DISCONNECT = 2;
  static const uint8_t NUS_EVT_RX = 3;
  BLECharacteristic* _nusTx = nullptr;      // NUS TX (notify) characteristic
  BLE2902*           _nusTxCccd = nullptr;  // its CCCD — stack updates on subscribe
  volatile int       _connCount = 0;        // >0 while any central is connected
  volatile bool      _nusSubscribed = false;// phone wrote CCCD enable
  static const int   NUS_EVENT_MAX = 8;     // deferred GATT event queue
  volatile uint8_t   _nusEvents[NUS_EVENT_MAX];
  volatile int       _nusEventCount = 0;
  static const uint8_t NUS_RX_BUF_SIZE = 64; // control lines are short
  char               _nusRxBuf[NUS_RX_BUF_SIZE]; // last NUS RX payload (guarded)
  volatile uint8_t   _nusRxLen = 0;
  void (*_nusRxHandler)(const String&) = nullptr;  // sketch-provided handler

public:
  BBKeyboard(std::string deviceName = "ESP32 Keyboard", std::string deviceManufacturer = "Espressif", uint8_t batteryLevel = 100);
  void begin(void);
  void end(void);
  void sendReport(KeyReport* keys);
  void sendReport(MediaKeyReport* keys);
  size_t press(uint8_t k);
  size_t press(const MediaKeyReport k);
  size_t release(uint8_t k);
  size_t release(const MediaKeyReport k);
  size_t write(uint8_t c);
  size_t write(const MediaKeyReport c);
  size_t write(const uint8_t *buffer, size_t size);
  void releaseAll(void);
  bool isConnected(void);
  void setBatteryLevel(uint8_t level);
  void setName(std::string deviceName);
  void setDelay(uint32_t ms);

  void set_vendor_id(uint16_t vid);
  void set_product_id(uint16_t pid);
  void set_version(uint16_t version);

  // ---- NUS ADDITION: stream + event API used by the BrailleBridge sketch ----
  // streamText mirrors the USB Serial byte stream to the phone app.
  void streamText(const char* s, bool newline);
  void streamLine(const char* line) { streamText(line, true); }
  // processEvents drains queued connect/disconnect/NUS-RX events.
  // Call from loop() — the chord state machine must run outside BLE callbacks.
  void processEvents();
  // RX callback shim hands the payload here (public: called from the shim).
  void queueNusRx(const char* data, size_t len);
  // Register the handler invoked (in loop() context) for NUS RX payloads.
  void setNusRxHandler(void (*handler)(const String&)) { _nusRxHandler = handler; }
  // True once the phone has enabled NUS notifications.
  bool nusSubscribed() const { return _nusSubscribed; }

protected:
  virtual void onStarted(BLEServer *pServer) { };
  virtual void onConnect(BLEServer* pServer) override;
  virtual void onDisconnect(BLEServer* pServer) override;
  virtual void onWrite(BLECharacteristic* me) override;

};

// NUS ADDITION: RX callback shim — routes NUS writes into BBKeyboard.// Defined in the .cpp; needs the single instance pointer declared there.
class BBKeyboardNusRxCallbacks : public BLECharacteristicCallbacks {
public:
  void onWrite(BLECharacteristic* characteristic) override;
};

#endif // CONFIG_BT_ENABLED
#endif // BB_KEYBOARD_H
