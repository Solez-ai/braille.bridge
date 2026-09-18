// ============================================================================
// BBKeyboard — vendored from T-vK's ESP32_BLE_Keyboard (BleKeyboard v0.0.4)
// See BBKeyboard.h for the rationale. Upstream code paths are kept verbatim;
// NUS additions are marked "NUS ADDITION".
// ============================================================================

#include "BBKeyboard.h"

#if defined(CONFIG_BT_ENABLED)

#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include "BLE2902.h"
#include "BLEHIDDevice.h"
#include "HIDTypes.h"
#include <driver/adc.h>
#include "sdkconfig.h"

#include "esp_log.h"
static const char* LOG_TAG = "BLEDevice";

// NUS ADDITION: guard for deferred-event queue + RX buffer (touched from the
// BLE task in callbacks and from loop() in processEvents).
static portMUX_TYPE s_nusMux = portMUX_INITIALIZER_UNLOCKED;

// NUS ADDITION: single-instance self pointer — the NUS RX callback shim
// (BBKeyboardNusRxCallbacks) routes writes into the one BBKeyboard instance.
static BBKeyboard* s_bbSelf = nullptr;

// Report IDs:
#define KEYBOARD_ID 0x01
#define MEDIA_KEYS_ID 0x02

static const uint8_t _hidReportDescriptor[] = {
  USAGE_PAGE(1),      0x01,          // USAGE_PAGE (Generic Desktop Ctrls)
  USAGE(1),           0x06,          // USAGE (Keyboard)
  COLLECTION(1),      0x01,          // COLLECTION (Application)
  // ------------------------------------------------- Keyboard
  REPORT_ID(1),       KEYBOARD_ID,   //   REPORT_ID (1)
  USAGE_PAGE(1),      0x07,          //   USAGE_PAGE (Kbrd/Keypad)
  USAGE_MINIMUM(1),   0xE0,          //   USAGE_MINIMUM (0xE0)
  USAGE_MAXIMUM(1),   0xE7,          //   USAGE_MAXIMUM (0xE7)
  LOGICAL_MINIMUM(1), 0x00,          //   LOGICAL_MINIMUM (0)
  LOGICAL_MAXIMUM(1), 0x01,          //   Logical Maximum (1)
  REPORT_SIZE(1),     0x01,          //   REPORT_SIZE (1)
  REPORT_COUNT(1),    0x08,          //   REPORT_COUNT (8)
  HIDINPUT(1),        0x02,          //   INPUT (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
  REPORT_COUNT(1),    0x01,          //   REPORT_COUNT (1) ; 1 byte (Reserved)
  REPORT_SIZE(1),     0x08,          //   REPORT_SIZE (8)
  HIDINPUT(1),        0x01,          //   INPUT (Const,Array,Abs,No Wrap,Linear,Preferred State,No Null Position)
  REPORT_COUNT(1),    0x05,          //   REPORT_COUNT (5) ; 5 bits (Num lock, Caps lock, Scroll lock, Compose, Kana)
  REPORT_SIZE(1),     0x01,          //   REPORT_SIZE (1)
  USAGE_PAGE(1),      0x08,          //   USAGE_PAGE (LEDs)
  USAGE_MINIMUM(1),   0x01,          //   USAGE_MINIMUM (0x01) ; Num Lock
  USAGE_MAXIMUM(1),   0x05,          //   USAGE_MAXIMUM (0x05) ; Kana
  HIDOUTPUT(1),       0x02,          //   OUTPUT (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position,Non-volatile)
  REPORT_COUNT(1),    0x01,          //   REPORT_COUNT (1) ; 3 bits (Padding)
  REPORT_SIZE(1),     0x03,          //   REPORT_SIZE (3)
  HIDOUTPUT(1),       0x01,          //   OUTPUT (Const,Array,Abs,No Wrap,Linear,Preferred State,No Null Position,Non-volatile)
  REPORT_COUNT(1),    0x06,          //   REPORT_COUNT (6) ; 6 bytes (Keys)
  REPORT_SIZE(1),     0x08,          //   REPORT_SIZE(8)
  LOGICAL_MINIMUM(1), 0x00,          //   LOGICAL_MINIMUM(0)
  LOGICAL_MAXIMUM(1), 0x65,          //   LOGICAL_MAXIMUM(0x65) ; 101 keys
  USAGE_PAGE(1),      0x07,          //   USAGE_PAGE (Kbrd/Keypad)
  USAGE_MINIMUM(1),   0x00,          //   USAGE_MINIMUM (0)
  USAGE_MAXIMUM(1),   0x65,          //   USAGE_MAXIMUM (0x65)
  HIDINPUT(1),        0x00,          //   INPUT (Data,Array,Abs,No Wrap,Linear,Preferred State,No Null Position)
  END_COLLECTION(0),                 // END_COLLECTION
  // ------------------------------------------------- Media Keys
  USAGE_PAGE(1),      0x0C,          // USAGE_PAGE (Consumer)
  USAGE(1),           0x01,          // USAGE (Consumer Control)
  COLLECTION(1),      0x01,          // COLLECTION (Application)
  REPORT_ID(1),       MEDIA_KEYS_ID, //   REPORT_ID (2)
  USAGE_PAGE(1),      0x0C,          //   USAGE_PAGE (Consumer)
  LOGICAL_MINIMUM(1), 0x00,          //   LOGICAL_MINIMUM (0)
  LOGICAL_MAXIMUM(1), 0x01,          //   LOGICAL_MAXIMUM (1)
  REPORT_SIZE(1),     0x01,          //   REPORT_SIZE (1)
  REPORT_COUNT(1),    0x10,          //   REPORT_COUNT (16)
  USAGE(1),           0xB5,          //   USAGE (Scan Next Track)     ; bit 0: 1
  USAGE(1),           0xB6,          //   USAGE (Scan Previous Track) ; bit 1: 2
  USAGE(1),           0xB7,          //   USAGE (Stop)                ; bit 2: 4
  USAGE(1),           0xCD,          //   USAGE (Play/Pause)          ; bit 3: 8
  USAGE(1),           0xE2,          //   USAGE (Mute)                ; bit 4: 16
  USAGE(1),           0xE9,          //   USAGE (Volume Increment)    ; bit 5: 32
  USAGE(1),           0xEA,          //   USAGE (Volume Decrement)    ; bit 6: 64
  USAGE(2),           0x23, 0x02,    //   Usage (WWW Home)            ; bit 7: 128
  USAGE(2),           0x94, 0x01,    //   Usage (My Computer) ; bit 0: 1
  USAGE(2),           0x92, 0x01,    //   Usage (Calculator)  ; bit 1: 2
  USAGE(2),           0x2A, 0x02,    //   Usage (WWW fav)     ; bit 2: 4
  USAGE(2),           0x21, 0x02,    //   Usage (WWW search)  ; bit 3: 8
  USAGE(2),           0x26, 0x02,    //   Usage (WWW stop)    ; bit 4: 16
  USAGE(2),           0x24, 0x02,    //   Usage (WWW back)    ; bit 5: 32
  USAGE(2),           0x83, 0x01,    //   Usage (Media sel)   ; bit 6: 64
  USAGE(2),           0x8A, 0x01,    //   Usage (Mail)        ; bit 7: 128
  HIDINPUT(1),        0x02,          //   INPUT (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
  END_COLLECTION(0)                  // END_COLLECTION
};

BBKeyboard::BBKeyboard(std::string deviceName, std::string deviceManufacturer, uint8_t batteryLevel)
    : hid(0)
    , deviceName(std::string(deviceName).substr(0, 15))
    , deviceManufacturer(std::string(deviceManufacturer).substr(0,15))
    , batteryLevel(batteryLevel) {
  for (int i = 0; i < NUS_EVENT_MAX; i++) _nusEvents[i] = 0;  // NUS ADDITION
  s_bbSelf = this;  // NUS ADDITION: single-instance RX routing
}

void BBKeyboard::begin(void)
{
  BLEDevice::init(deviceName);

  // NUS ADDITION: larger ATT MTU so Bangla conjuncts and control lines
  // notify in fewer chunks. Does not affect HID or advertising.
  BLEDevice::setMTU(247);

  BLEServer* pServer = BLEDevice::createServer();
  pServer->setCallbacks(this);

  hid = new BLEHIDDevice(pServer);
  inputKeyboard = hid->inputReport(KEYBOARD_ID);  // <-- input REPORTID from report map
  outputKeyboard = hid->outputReport(KEYBOARD_ID);
  inputMediaKeys = hid->inputReport(MEDIA_KEYS_ID);

  outputKeyboard->setCallbacks(this);

  hid->manufacturer()->setValue(deviceManufacturer);

  hid->pnp(0x02, vid, pid, version);
  hid->hidInfo(0x00, 0x01);

  BLESecurity* pSecurity = new BLESecurity();
  pSecurity->setAuthenticationMode(ESP_LE_AUTH_REQ_SC_MITM_BOND);

  hid->reportMap((uint8_t*)_hidReportDescriptor, sizeof(_hidReportDescriptor));
  hid->startServices();

  // ---------------- NUS ADDITION: Nordic UART Service ----------------
  // Own service, created AFTER the HID services are started, exactly like
  // any normal secondary service. The HID service above is untouched.
  BLEService* nus = pServer->createService(BLEUUID(NUS_SERVICE_UUID));

  _nusTx = nus->createCharacteristic(BLEUUID(NUS_TX_UUID), BLECharacteristic::PROPERTY_NOTIFY);
  _nusTxCccd = new BLE2902();
  _nusTx->addDescriptor(_nusTxCccd);   // stack updates on phone subscribe

  BLECharacteristic* nusRx = nus->createCharacteristic(BLEUUID(NUS_RX_UUID),
    BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_WRITE_NR);
  nusRx->setCallbacks(new BBKeyboardNusRxCallbacks());

  nus->start();
  // -------------------------------------------------------------------

  advertising = pServer->getAdvertising();
  advertising->setAppearance(HID_KEYBOARD);
  advertising->addServiceUUID(hid->hidService()->getUUID());
  advertising->setScanResponse(false);
  advertising->start();
  hid->setBatteryLevel(batteryLevel);

  ESP_LOGD(LOG_TAG, "Advertising started!");
}

void BBKeyboard::end(void)
{
}

bool BBKeyboard::isConnected(void) {
  return this->connected;
}

void BBKeyboard::setBatteryLevel(uint8_t level) {
  this->batteryLevel = level;
  if (hid != 0)
    this->hid->setBatteryLevel(this->batteryLevel);
}

//must be called before begin in order to set the name
void BBKeyboard::setName(std::string deviceName) {
  this->deviceName = deviceName;
}

/**
 * @brief Sets the waiting time (in milliseconds) between multiple keystrokes in NimBLE mode.
 *
 * @param ms Time in milliseconds
 */
void BBKeyboard::setDelay(uint32_t ms) {
  this->_delay_ms = ms;
}

void BBKeyboard::set_vendor_id(uint16_t vid) {
	this->vid = vid;
}

void BBKeyboard::set_product_id(uint16_t pid) {
	this->pid = pid;
}

void BBKeyboard::set_version(uint16_t version) {
	this->version = version;
}

void BBKeyboard::sendReport(KeyReport* keys)
{
  if (this->isConnected())
  {
    this->inputKeyboard->setValue((uint8_t*)keys, sizeof(KeyReport));
    this->inputKeyboard->notify();
  }
}

void BBKeyboard::sendReport(MediaKeyReport* keys)
{
  if (this->isConnected())
  {
    this->inputMediaKeys->setValue((uint8_t*)keys, sizeof(MediaKeyReport));
    this->inputMediaKeys->notify();
  }
}

extern
const uint8_t _asciimap[128] PROGMEM;

#define SHIFT 0x80
const uint8_t _asciimap[128] =
{
	0x00,             // NUL
	0x00,             // SOH
	0x00,             // STX
	0x00,             // ETX
	0x00,             // EOT
	0x00,             // ENQ
	0x00,             // ACK
	0x00,             // BEL
	0x2a,			// BS	Backspace
	0x2b,			// TAB	Tab
	0x28,			// LF	Enter
	0x00,             // VT
	0x00,             // FF
	0x00,             // CR
	0x00,             // SO
	0x00,             // SI
	0x00,             // DEL
	0x00,             // DC1
	0x00,             // DC2
	0x00,             // DC3
	0x00,             // DC4
	0x00,             // NAK
	0x00,             // SYN
	0x00,             // ETB
	0x00,             // CAN
	0x00,             // EM
	0x00,             // SUB
	0x00,             // ESC
	0x00,             // FS
	0x00,             // GS
	0x00,             // RS
	0x00,             // US

	0x2c,			//  ' '
	0x1e|SHIFT,		// !
	0x34|SHIFT,		// "
	0x20|SHIFT,		// #
	0x21|SHIFT,		// $
	0x22|SHIFT,		// %
	0x24|SHIFT,		// &
	0x34,			// '
	0x26|SHIFT,		// (
	0x27|SHIFT,		// )
	0x25|SHIFT,		// *
	0x2e|SHIFT,		// +
	0x2c,			// ,
	0x2d,			// -
	0x2e,			// .
	0x2f,			// /
	0x1f,			// 0
	0x14,			// 1
	0x15,			// 2
	0x16,			// 3
	0x17,			// 4
	0x18,			// 5
	0x19,			// 6
	0x1a,			// 7
	0x1b,			// 8
	0x1c,			// 9
	0x2f|SHIFT,		// :
	0x2e|SHIFT,		// ;
	0x36,			// <
	0x2d|SHIFT,		// =
	0x37,			// >
	0x38|SHIFT,		// ?
	0x1f|SHIFT,		// @
	0x04|SHIFT,		// A
	0x05|SHIFT,		// B
	0x06|SHIFT,		// C
	0x07|SHIFT,		// D
	0x08|SHIFT,		// E
	0x09|SHIFT,		// F
	0x0a|SHIFT,		// G
	0x0b|SHIFT,		// H
	0x0c|SHIFT,		// I
	0x0d|SHIFT,		// J
	0x0e|SHIFT,		// K
	0x0f|SHIFT,		// L
	0x10|SHIFT,		// M
	0x11|SHIFT,		// N
	0x12|SHIFT,		// O
	0x13|SHIFT,		// P
	0x14|SHIFT,		// Q
	0x15|SHIFT,		// R
	0x16|SHIFT,		// S
	0x17|SHIFT,		// T
	0x18|SHIFT,		// U
	0x19|SHIFT,		// V
	0x1a|SHIFT,		// W
	0x1b|SHIFT,		// X
	0x1c|SHIFT,		// Y
	0x1d|SHIFT,		// Z
	0x22,			// [
	0x31,			// backslash
	0x23,			// ]
	0x2d|SHIFT,		// ^
	0x35|SHIFT,		// _
	0x35,			// `
	0x04,			// a
	0x05,			// b
	0x06,			// c
	0x07,			// d
	0x08,			// e
	0x09,			// f
	0x0a,			// g
	0x0b,			// h
	0x0c,			// i
	0x0d,			// j
	0x0e,			// k
	0x0f,			// l
	0x10,			// m
	0x11,			// n
	0x12,			// o
	0x13,			// p
	0x14,			// q
	0x15,			// r
	0x16,			// s
	0x17,			// t
	0x18,			// u
	0x19,			// v
	0x1a,			// w
	0x1b,			// x
	0x1c,			// y
	0x1d,			// z
	0x24,			// {
	0x25,			// |
	0x26,			// }
	0x2d|SHIFT,		// ~
	0				// DEL
};

size_t BBKeyboard::press(uint8_t k)
{
	uint8_t i;
	if (k >= 136) {			// it's a non-printing key (not a modifier)
		k = k - 136;
	} else if (k >= 128) {	// it's a modifier key
		_keyReport.modifiers |= (1<<(k-128));
		k = 0;
	} else {				// it's a printing key
		k = pgm_read_byte(_asciimap + k);
		if (!k) {
			setWriteError();
			return 0;
		}
		if (k & 0x80) {						// it's a capital letter or other character reached with shift
			_keyReport.modifiers |= 0x02;	// the left shift modifier
			k &= 0x7F;
		}
	}

	// Add k to the key report only if it's not already present
	// and if there is an empty slot.
	if (_keyReport.keys[0] != k && _keyReport.keys[1] != k &&
		_keyReport.keys[2] != k && _keyReport.keys[3] != k &&
		_keyReport.keys[4] != k && _keyReport.keys[5] != k) {

		for (i=0; i<6; i++) {
			if (_keyReport.keys[i] == 0x00) {
				_keyReport.keys[i] = k;
				break;
			}
		}
		if (i == 6) {
			setWriteError();
			return 0;
		}
	}
	sendReport(&_keyReport);
	return 1;
}

size_t BBKeyboard::press(const MediaKeyReport k)
{
    uint16_t k_16 = k[1] | (k[0] << 8);
    uint16_t mediaKeyReport_16 = _mediaKeyReport[1] | (_mediaKeyReport[0] << 8);

    mediaKeyReport_16 |= k_16;
    _mediaKeyReport[0] = (uint8_t)((mediaKeyReport_16 & 0xFF00) >> 8);
    _mediaKeyReport[1] = (uint8_t)(mediaKeyReport_16 & 0x00FF);

	sendReport(&_mediaKeyReport);
	return 1;
}

// release() takes the specified key out of the persistent key report and
// sends the report.  This tells the OS the key is no longer pressed and that
// it shouldn't be repeated any more.
size_t BBKeyboard::release(uint8_t k)
{
	uint8_t i;
	if (k >= 136) {			// it's a non-printing key (not a modifier)
		k = k - 136;
	} else if (k >= 128) {	// it's a modifier key
		_keyReport.modifiers &= ~(1<<(k-128));
		k = 0;
	} else {				// it's a printing key
		k = pgm_read_byte(_asciimap + k);
		if (!k) {
			return 0;
		}
		if (k & 0x80) {							// it's a capital letter or other character reached with shift
			_keyReport.modifiers &= ~(0x02);	// the left shift modifier
			k &= 0x7F;
		}
	}

	// Test the key report to see if k is present.  Clear it if it exists.
	// Check all positions in case the key is present more than once (which it shouldn't be)
	for (i=0; i<6; i++) {
		if (0 != k && _keyReport.keys[i] == k) {
			_keyReport.keys[i] = 0x00;
		}
	}

	sendReport(&_keyReport);
	return 1;
}

size_t BBKeyboard::release(const MediaKeyReport k)
{
    uint16_t k_16 = k[1] | (k[0] << 8);
    uint16_t mediaKeyReport_16 = _mediaKeyReport[1] | (_mediaKeyReport[0] << 8);
    mediaKeyReport_16 &= ~k_16;
    _mediaKeyReport[0] = (uint8_t)((mediaKeyReport_16 & 0xFF00) >> 8);
    _mediaKeyReport[1] = (uint8_t)(mediaKeyReport_16 & 0x00FF);

	sendReport(&_mediaKeyReport);
	return 1;
}

void BBKeyboard::releaseAll(void)
{
	_keyReport.keys[0] = 0;
	_keyReport.keys[1] = 0;
	_keyReport.keys[2] = 0;
	_keyReport.keys[3] = 0;
	_keyReport.keys[4] = 0;
	_keyReport.keys[5] = 0;
	_keyReport.modifiers = 0;
    _mediaKeyReport[0] = 0;
    _mediaKeyReport[1] = 0;
	sendReport(&_keyReport);
	sendReport(&_mediaKeyReport);
}

size_t BBKeyboard::write(uint8_t c)
{
	uint8_t p = press(c);  // Keydown
	release(c);            // Keyup
	return p;              // just return the result of press() since release() almost always returns 1
}

size_t BBKeyboard::write(const MediaKeyReport c)
{
	uint16_t p = press(c);  // Keydown
	release(c);            // Keyup
	return p;              // just return the result of press() since release() almost always returns 1
}

size_t BBKeyboard::write(const uint8_t *buffer, size_t size) {
	size_t n = 0;
	while (size--) {
		if (*buffer != '\r') {
			if (write(*buffer)) {
			  n++;
			} else {
			  break;
			}
		}
		buffer++;
	}
	return n;
}

void BBKeyboard::onConnect(BLEServer* pServer) {
  this->connected = true;

  BLE2902* desc = (BLE2902*)this->inputKeyboard->getDescriptorByUUID(BLEUUID((uint16_t)0x2902));
  desc->setNotifications(true);
  desc = (BLE2902*)this->inputMediaKeys->getDescriptorByUUID(BLEUUID((uint16_t)0x2902));
  desc->setNotifications(true);

  // NUS ADDITION: force-enable NUS notifications — the SAME treatment T-vK
  // just applied to the HID characteristics above. Some hosts subscribe
  // without the CCCD write visibly landing in the descriptor object; without
  // this the NUS stream stays dead while HID typing works (exact symptom of
  // the v4 firmware). Matches the proven upstream pattern.
  if (this->_nusTxCccd) this->_nusTxCccd->setNotifications(true);

  // NUS ADDITION: track connections, queue event for loop()
  portENTER_CRITICAL(&s_nusMux);
  this->_connCount++;
  this->_nusSubscribed = true;   // force-enabled above; CCCD sync confirms later
  if (this->_nusEventCount < NUS_EVENT_MAX) this->_nusEvents[this->_nusEventCount++] = NUS_EVT_CONNECT;
  portEXIT_CRITICAL(&s_nusMux);
}

void BBKeyboard::onDisconnect(BLEServer* pServer) {
  this->connected = false;

  BLE2902* desc = (BLE2902*)this->inputKeyboard->getDescriptorByUUID(BLEUUID((uint16_t)0x2902));
  desc->setNotifications(false);
  desc = (BLE2902*)this->inputMediaKeys->getDescriptorByUUID(BLEUUID((uint16_t)0x2902));
  desc->setNotifications(false);

  // NUS ADDITION: mirror the HID treatment — disable while no client
  if (this->_nusTxCccd) this->_nusTxCccd->setNotifications(false);

  advertising->start();

  // NUS ADDITION: track disconnection, queue event for loop().
  // (advertising->start() above is upstream's own re-advertise call.)
  portENTER_CRITICAL(&s_nusMux);
  this->_connCount--;
  if (this->_connCount < 0) this->_connCount = 0;
  this->_nusSubscribed = false;   // phone must resubscribe after reconnect
  if (this->_nusEventCount < NUS_EVENT_MAX) this->_nusEvents[this->_nusEventCount++] = NUS_EVT_DISCONNECT;
  portEXIT_CRITICAL(&s_nusMux);
}

void BBKeyboard::onWrite(BLECharacteristic* me) {
  uint8_t* value = (uint8_t*)(me->getValue().c_str());
  (void)value;
  ESP_LOGI(LOG_TAG, "special keys: %d", *value);
}

void BBKeyboard::delay_ms(uint64_t ms) {
  uint64_t m = esp_timer_get_time();
  if(ms){
    uint64_t e = (m + (ms * 1000));
    if(m > e){ //overflow
        while(esp_timer_get_time() > e) { }
    }
    else{
        while(esp_timer_get_time() < e) { }
    }
  }
}

// ============================================================================
// NUS ADDITIONS — implementation of the stream/event API.
// ============================================================================

void BBKeyboardNusRxCallbacks::onWrite(BLECharacteristic* characteristic) {
  if (s_bbSelf) s_bbSelf->queueNusRx(characteristic->getValue().c_str(), characteristic->getValue().length());
}

void BBKeyboard::queueNusRx(const char* data, size_t len) {
  // Allocation-free handoff: fixed buffer, filled under the spinlock.
  if (len > sizeof(_nusRxBuf) - 1) len = sizeof(_nusRxBuf) - 1;
  portENTER_CRITICAL(&s_nusMux);
  memcpy(_nusRxBuf, data, len);
  _nusRxBuf[len] = 0;
  _nusRxLen = (uint8_t)len;
  if (_nusEventCount < NUS_EVENT_MAX) _nusEvents[_nusEventCount++] = NUS_EVT_RX;
  portEXIT_CRITICAL(&s_nusMux);
}

void BBKeyboard::streamText(const char* s, bool newline) {
  // Mirror the USB Serial stream to the phone app over NUS notifications.
  // PROTOCOL RULE: a line's terminating '\n' must ride in the SAME
  // notification as its text. The receiving side treats a chunk without
  // '\n' as typed characters — splitting text and newline across two
  // notifications makes control lines (LANG:*, SYSTEM:*) show up as
  // literal text on the phone and breaks backspace handling.
  if (!_nusTx || !_connCount || !_nusSubscribed) return;

  size_t len = strlen(s);
  size_t total = len + (newline ? 1 : 0);
  uint16_t mtu = BLEDevice::getMTU();
  size_t chunkCap = (mtu > 3) ? (mtu - 3) : 20;

  size_t off = 0;
  while (off < total) {
    uint8_t chunk[280];                       // stack buffer; MTU 247 → 244-byte payload max
    size_t cap = (total - off) < sizeof(chunk) ? (total - off) : sizeof(chunk);
    size_t n = cap < chunkCap ? cap : chunkCap;
    for (size_t i = 0; i < n; i++) {
      size_t idx = off + i;
      chunk[i] = (idx == len) ? '\n' : s[idx];  // newline sits logically at position len
    }
    _nusTx->setValue(chunk, n);
    _nusTx->notify();
    off += n;
  }
}

void BBKeyboard::processEvents() {
  // Drain queued GATT events OUTSIDE the BLE task, so sketch code (chord
  // state machine, timing guards) never runs inside a BLE callback.
  for (;;) {
    uint8_t ev;
    portENTER_CRITICAL(&s_nusMux);
    if (_nusEventCount == 0) { portEXIT_CRITICAL(&s_nusMux); break; }
    ev = _nusEvents[0];
    for (int i = 1; i < _nusEventCount; i++) _nusEvents[i-1] = _nusEvents[i];
    _nusEventCount--;
    portEXIT_CRITICAL(&s_nusMux);

    if (ev == NUS_EVT_RX && _nusRxHandler) {
      char local[sizeof(_nusRxBuf)];
      portENTER_CRITICAL(&s_nusMux);
      memcpy(local, _nusRxBuf, sizeof(_nusRxBuf));
      portEXIT_CRITICAL(&s_nusMux);
      local[sizeof(_nusRxBuf) - 1] = 0;
      _nusRxHandler(String(local));
    }
    // NUS_EVT_CONNECT / NUS_EVT_DISCONNECT: state is tracked in the
    // callbacks; queued only so the sketch can observe ordering.
  }
  // Re-sync the subscription flag with what the stack reports (some stacks
  // update the CCCD outside any callback we see).
  if (_nusTxCccd) {
    bool now = _nusTxCccd->getNotifications();
    if (now != _nusSubscribed) _nusSubscribed = now;
  }
}

#endif // CONFIG_BT_ENABLED
