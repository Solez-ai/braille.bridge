package com.example.ble

import android.annotation.SuppressLint
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothGatt
import android.bluetooth.BluetoothGattCallback
import android.bluetooth.BluetoothGattCharacteristic
import android.bluetooth.BluetoothGattDescriptor
import android.bluetooth.BluetoothProfile
import android.content.Context
import android.os.Handler
import android.os.Looper
import android.util.Log
import java.util.UUID

@SuppressLint("MissingPermission")
class BleDeviceConn(
    private val context: Context,
    val device: BluetoothDevice,
    val desiredName: String? = null,
    private val onLine: (String) -> Unit,
    private val onChars: (String) -> Unit,
    private val onStateChange: (Boolean, String) -> Unit,
    private val onDebug: (String) -> Unit = {}
) {
    companion object {
        const val TAG = "BleDeviceConn"
        val SERVICE_UUID: UUID = UUID.fromString("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
        val TX_CHAR_UUID: UUID = UUID.fromString("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
        val RX_CHAR_UUID: UUID = UUID.fromString("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")
        val CCCD_UUID: UUID = UUID.fromString("00002902-0000-1000-8000-00805F9B34FB")
    }

    private var gatt: BluetoothGatt? = null
    var isConnected = false
        private set
    var isDesired = true
        private set
    /** True once the NUS TX CCCD write has been dispatched (subscribe attempt made). */
    @Volatile
    private var subscribeAttempted = false

    private val handler = Handler(Looper.getMainLooper())
    private var reconnectBackoffMs = 1000L
    private val reassembler = Utf8Reassembler()
    private val lineFeed = LineFeed(onLine, onChars)

    /** Set true the moment any NUS notification bytes arrive. */
    @Volatile
    private var notificationsFlowing = false

    /** Current live GATT handle for the watchdog (guarded to the main thread). */
    private var gattRef: BluetoothGatt? = null

    private val gattCallback = object : BluetoothGattCallback() {
        override fun onConnectionStateChange(gatt: BluetoothGatt, status: Int, newState: Int) {
            Log.d(TAG, "Connection state changed: status=$status, newState=$newState")
            if (newState == BluetoothProfile.STATE_CONNECTED) {
                isConnected = true
                reconnectBackoffMs = 1000L
                onStateChange(true, device.address)
                onDebug("🔗 GATT link up — discovering services")
                gatt.discoverServices()
            } else if (newState == BluetoothProfile.STATE_DISCONNECTED) {
                if (isConnected || status != BluetoothGatt.GATT_SUCCESS) {
                    onDebug("⚠️ GATT disconnected (status=$status)")
                }
                isConnected = false
                onStateChange(false, device.address)
                try {
                    gatt.close()
                } catch (e: Exception) {
                    // Ignore
                }
                this@BleDeviceConn.gatt = null
                if (isDesired) {
                    scheduleReconnect()
                }
            } else if (status != BluetoothGatt.GATT_SUCCESS) {
                onDebug("⚠️ GATT event status=$status")
            }
        }

        override fun onServicesDiscovered(gatt: BluetoothGatt, status: Int) {
            if (status != BluetoothGatt.GATT_SUCCESS) {
                onDebug("❌ Service discovery failed (status=$status)")
                Log.e(TAG, "Service discovery failed: status=$status")
                return
            }
            val service = gatt.getService(SERVICE_UUID)
            if (service == null) {
                onDebug("❌ NUS service missing on device — firmware too old?")
                Log.e(TAG, "NUS service not found on ${device.address} — firmware may lack the Nordic UART service")
                return
            }
            val txChar = service.getCharacteristic(TX_CHAR_UUID)
            if (txChar == null) {
                onDebug("❌ NUS TX characteristic missing")
                Log.e(TAG, "NUS TX characteristic not found on ${device.address}")
                return
            }
            // Local subscription enable — must precede the CCCD write.
            if (!gatt.setCharacteristicNotification(txChar, true)) {
                onDebug("⚠️ Local notification enable returned false")
                Log.e(TAG, "setCharacteristicNotification returned false for NUS TX")
            }
            onDebug("✅ NUS service found — subscribing")
            subscribeNusCccd(gatt)
        }

        /** Write the CCCD that actually turns firmware notifications ON. Retried by watchdog. */
        private fun subscribeNusCccd(gatt: BluetoothGatt) {
            val txChar = gatt.getService(SERVICE_UUID)?.getCharacteristic(TX_CHAR_UUID)
            val descriptor = txChar?.getDescriptor(CCCD_UUID)
            if (descriptor == null) {
                onDebug("❌ NUS CCCD (0x2902) missing — cannot subscribe")
                Log.e(TAG, "NUS TX CCCD (0x2902) missing — cannot subscribe")
                return
            }
            subscribeAttempted = true
            descriptor.value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
            if (!gatt.writeDescriptor(descriptor)) {
                onDebug("⚠️ CCCD write rejected by stack")
                Log.e(TAG, "writeDescriptor(CCCD) rejected by stack — requesting MTU anyway")
                gatt.requestMtu(247)
            }
        }

        override fun onDescriptorWrite(gatt: BluetoothGatt, descriptor: BluetoothGattDescriptor, status: Int) {
            if (descriptor.uuid == CCCD_UUID) {
                if (status == BluetoothGatt.GATT_SUCCESS) {
                    onDebug("✅ Subscribed — waiting for data…")
                    Log.d(TAG, "NUS CCCD subscribed — requesting MTU 247")
                } else {
                    onDebug("❌ Subscribe write failed (status=$status)")
                    Log.e(TAG, "NUS CCCD write failed: status=$status — continuing without optimized MTU")
                }
                // Proceed regardless: default 23-byte MTU still carries the small
                // character chunks; retrying the CCCD is the watchdog's job.
                gatt.requestMtu(247)
            }
        }

        override fun onMtuChanged(gatt: BluetoothGatt, mtu: Int, status: Int) {
            Log.d(TAG, "MTU changed to $mtu, status=$status")
            onDebug("📡 MTU negotiated: $mtu bytes")
            // Faster connection interval → snappier character-by-character notifications
            try {
                gatt.requestConnectionPriority(BluetoothGatt.CONNECTION_PRIORITY_HIGH)
            } catch (e: Exception) {
                Log.w(TAG, "requestConnectionPriority unavailable: ${e.message}")
            }
            // Watchdog: if the CCCD write never completed (some stacks silently drop
            // it right after bonding), retry exactly once now that security is up.
            handler.postDelayed({
                val g = gattRef
                if (g != null && isConnected && !notificationsFlowing && subscribeAttempted) {
                    Log.w(TAG, "No data since subscribe — retrying NUS CCCD write once")
                    onDebug("⏳ No data yet — retrying subscribe once")
                    subscribeAttempted = true
                    val d = g.getService(SERVICE_UUID)?.getCharacteristic(TX_CHAR_UUID)?.getDescriptor(CCCD_UUID)
                    if (d != null) {
                        d.value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
                        if (!g.writeDescriptor(d)) {
                            onDebug("❌ Subscribe retry rejected")
                            Log.e(TAG, "CCCD retry also rejected")
                        }
                    }
                }
            }, 2500)
        }

        // For Android 13+ (API 33+)
        override fun onCharacteristicChanged(
            gatt: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic,
            value: ByteArray
        ) {
            if (characteristic.uuid == TX_CHAR_UUID) {
                processIncomingBytes(value)
            }
        }

        // For Android < 13
        @Deprecated("Deprecated in Java")
        override fun onCharacteristicChanged(
            gatt: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic
        ) {
            if (characteristic.uuid == TX_CHAR_UUID) {
                @Suppress("DEPRECATION")
                val value = characteristic.value ?: return
                processIncomingBytes(value)
            }
        }
    }

    private fun processIncomingBytes(bytes: ByteArray) {
        if (bytes.isEmpty()) return
        if (!notificationsFlowing) {
            notificationsFlowing = true
            onDebug("✅ Data flowing — ${bytes.size} bytes")
        }
        val decoded = reassembler.feed(bytes)
        if (decoded.isNotEmpty()) {
            lineFeed.feed(decoded)
        }
    }

    fun connect() {
        isDesired = true
        notificationsFlowing = false
        subscribeAttempted = false
        try {
            gatt = device.connectGatt(context, false, gattCallback, BluetoothDevice.TRANSPORT_LE)
            gattRef = gatt
        } catch (e: Exception) {
            Log.e(TAG, "connect failed", e)
            onDebug("❌ connectGatt threw: ${e.message}")
            scheduleReconnect()
        }
    }

    fun disconnect() {
        isDesired = false
        handler.removeCallbacksAndMessages(null)
        try {
            gatt?.disconnect()
            gatt?.close()
        } catch (e: Exception) {
            Log.e(TAG, "disconnect failed", e)
        }
        gatt = null
        gattRef = null
        isConnected = false
        notificationsFlowing = false
        onStateChange(false, device.address)
    }

    private fun scheduleReconnect() {
        if (!isDesired) return
        handler.postDelayed({
            if (isDesired && !isConnected) {
                Log.d(TAG, "Reconnecting to ${device.address} after $reconnectBackoffMs ms")
                onDebug("🔄 Reconnecting in ${reconnectBackoffMs / 1000}s…")
                connect()
                reconnectBackoffMs = (reconnectBackoffMs * 2).coerceAtMost(10000L)
            }
        }, reconnectBackoffMs)
    }
}
