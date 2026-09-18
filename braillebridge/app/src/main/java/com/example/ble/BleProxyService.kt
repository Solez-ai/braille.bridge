package com.example.ble

import android.annotation.SuppressLint
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothManager
import android.bluetooth.BluetoothProfile
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanResult
import android.bluetooth.le.ScanSettings
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.ServiceInfo
import android.os.Binder
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.SystemClock
import android.util.Log
import androidx.core.app.NotificationCompat
import com.example.MainActivity
import com.example.data.SettingsStore
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import java.util.concurrent.ConcurrentHashMap

data class ScannedBleDevice(
    val device: BluetoothDevice,
    val name: String,
    val address: String,
    val rssi: Int
)

sealed class BleEvent {
    data class DeviceConnected(val address: String, val name: String?) : BleEvent()
    data class DeviceDisconnected(val address: String) : BleEvent()
    data class IncomingLine(val address: String, val line: String) : BleEvent()
    data class IncomingChars(val address: String, val chars: String) : BleEvent()
}

class BleProxyService : Service() {

    companion object {
        const val TAG = "BleProxyService"
        const val CHANNEL_ID = "bb_ble_service_channel"
        const val NOTIFICATION_ID = 101

        @Volatile
        var instance: BleProxyService? = null
            private set
    }

    private val binder = LocalBinder()
    inner class LocalBinder : Binder() {
        fun getService(): BleProxyService = this@BleProxyService
    }

    private val connections = ConcurrentHashMap<String, BleDeviceConn>()
    private lateinit var settingsStore: SettingsStore
    private var bluetoothAdapter: BluetoothAdapter? = null
    private var bluetoothManager: BluetoothManager? = null

    private val deviceMap = ConcurrentHashMap<String, ScannedBleDevice>()
    private var lastScanEmitTime = 0L

    private val _scannedDevices = MutableStateFlow<List<ScannedBleDevice>>(emptyList())
    val scannedDevices = _scannedDevices.asStateFlow()

    private val _events = MutableSharedFlow<BleEvent>(extraBufferCapacity = 64)
    val events = _events.asSharedFlow()

    private val _connectedCount = MutableStateFlow(0)
    val connectedCount = _connectedCount.asStateFlow()

    private val handler = Handler(Looper.getMainLooper())
    private var isScanning = false
    private var isHighDutyScan = false
    private var periodicScanRunnable: Runnable? = null

    // Native Bluetooth state and connection broadcast receiver
    private val nativeBluetoothReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            val action = intent.action ?: return
            Log.d(TAG, "Native Bluetooth broadcast received: $action")
            when (action) {
                BluetoothDevice.ACTION_ACL_CONNECTED -> {
                    val device: BluetoothDevice? = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                        intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE, BluetoothDevice::class.java)
                    } else {
                        @Suppress("DEPRECATION")
                        intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE)
                    }
                    device?.let { handleNativeConnectedDevice(it) }
                }
                BluetoothDevice.ACTION_BOND_STATE_CHANGED -> {
                    val bondState = intent.getIntExtra(BluetoothDevice.EXTRA_BOND_STATE, BluetoothDevice.BOND_NONE)
                    if (bondState == BluetoothDevice.BOND_BONDED) {
                        val device: BluetoothDevice? = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                            intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE, BluetoothDevice::class.java)
                        } else {
                            @Suppress("DEPRECATION")
                            intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE)
                        }
                        device?.let { handleNativeConnectedDevice(it) }
                    }
                }
                BluetoothAdapter.ACTION_CONNECTION_STATE_CHANGED -> {
                    val state = intent.getIntExtra(BluetoothAdapter.EXTRA_CONNECTION_STATE, BluetoothAdapter.STATE_DISCONNECTED)
                    if (state == BluetoothAdapter.STATE_CONNECTED) {
                        val device: BluetoothDevice? = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                            intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE, BluetoothDevice::class.java)
                        } else {
                            @Suppress("DEPRECATION")
                            intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE)
                        }
                        if (device != null) {
                            handleNativeConnectedDevice(device)
                        } else {
                            checkSystemConnectedDevices()
                        }
                    }
                }
                // API 33+: fires whenever any LE device enters/leaves the GATT-connected
                // set — including the OS's own HID-host connection to BrailleBridge.
                // ACTION_ACL_CONNECTED does NOT fire for that path (it is classic-BR/EDR
                // oriented), so this broadcast is the reliable trigger on modern phones.
                BluetoothManager.ACTION_GATT_CONNECTED_DEVICES_CHANGED -> {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                        checkSystemConnectedDevices()
                    }
                }
                BluetoothAdapter.ACTION_STATE_CHANGED -> {
                    val state = intent.getIntExtra(BluetoothAdapter.EXTRA_STATE, BluetoothAdapter.ERROR)
                    if (state == BluetoothAdapter.STATE_ON) {
                        checkSystemConnectedDevices()
                        startPeriodicScanner()
                    }
                }
            }
        }
    }

    private val scanCallback = object : ScanCallback() {
        @SuppressLint("MissingPermission")
        override fun onScanResult(callbackType: Int, result: ScanResult) {
            val device = result.device ?: return
            val name = result.scanRecord?.deviceName ?: device.name ?: "Unknown"
            val address = device.address
            val rssi = result.rssi

            val isNew = !deviceMap.containsKey(address)
            deviceMap[address] = ScannedBleDevice(device, name, address, rssi)

            val now = SystemClock.uptimeMillis()
            // Throttle UI emissions: only emit on new discovery or at most once every 1200ms
            if (isNew || now - lastScanEmitTime > 1200L) {
                lastScanEmitTime = now
                _scannedDevices.value = deviceMap.values.toList()
            }

            // Auto-connect when a scan reveals a BrailleBridge and nothing is connected yet
            if (isBrailleBridgeDevice(name) &&
                connections.values.none { it.isConnected } &&
                (connections[address]?.isConnected != true)) {
                Log.d(TAG, "Auto-connecting discovered device: '$name' ($address)")
                connectDevice(device)
            }
        }

        override fun onScanFailed(errorCode: Int) {
            Log.e(TAG, "BLE Scan failed: $errorCode")
            isScanning = false
        }
    }

    override fun onCreate() {
        super.onCreate()
        instance = this
        settingsStore = SettingsStore(this)

        bluetoothManager = getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager
        bluetoothAdapter = bluetoothManager?.adapter

        createNotificationChannel()
        promoteToForeground()

        // Register broadcast receiver for native phone Bluetooth connections
        val filter = IntentFilter().apply {
            addAction(BluetoothDevice.ACTION_ACL_CONNECTED)
            addAction(BluetoothDevice.ACTION_ACL_DISCONNECTED)
            addAction(BluetoothDevice.ACTION_BOND_STATE_CHANGED)
            addAction(BluetoothAdapter.ACTION_CONNECTION_STATE_CHANGED)
            addAction(BluetoothAdapter.ACTION_STATE_CHANGED)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                addAction(BluetoothManager.ACTION_GATT_CONNECTED_DEVICES_CHANGED)
            }
        }
        try {
            registerReceiver(nativeBluetoothReceiver, filter)
        } catch (e: Exception) {
            Log.e(TAG, "Failed to register nativeBluetoothReceiver", e)
        }

        // Check already connected / bonded devices natively on the phone
        checkSystemConnectedDevices()

        // Start low-power periodic scan
        startPeriodicScanner()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        updateNotification()
        checkSystemConnectedDevices()
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder = binder

    override fun onDestroy() {
        super.onDestroy()
        try {
            unregisterReceiver(nativeBluetoothReceiver)
        } catch (e: Exception) {
            // Ignore
        }
        stopScan()
        periodicScanRunnable?.let { handler.removeCallbacks(it) }
        handler.removeCallbacksAndMessages(null)
        connections.values.forEach { it.disconnect() }
        connections.clear()
        deviceMap.clear()
        instance = null
    }

    private fun isBrailleBridgeDevice(name: String?): Boolean {
        if (name.isNullOrBlank()) return false
        return name.contains("BrailleBridge", ignoreCase = true) ||
               name.contains("Braille", ignoreCase = true) ||
               name.contains("ESP32", ignoreCase = true)
    }

    @SuppressLint("MissingPermission")
    fun handleNativeConnectedDevice(device: BluetoothDevice) {
        val name = try { device.name ?: "" } catch (e: SecurityException) { "" }
        val address = device.address

        Log.d(TAG, "Native device connected: '$name' ($address)")

        // Recognition is NAME-based only — fresh HID bonds frequently report an
        // empty device.name, so address/assignment checks must never gate pickup.
        if (!isBrailleBridgeDevice(name)) {
            return
        }
        if (!connections.containsKey(address) || connections[address]?.isConnected != true) {
            Log.d(TAG, "Auto picking up native BrailleBridge connection: '$name' ($address)")
            connectDevice(device)
        }
    }

    @SuppressLint("MissingPermission")
    fun checkSystemConnectedDevices() {
        val adapter = bluetoothAdapter ?: return
        if (!adapter.isEnabled) return

        // 1. HIGHEST RELIABILITY: devices the system reports as GATT-connected right
        //    now (covers the OS's own HID-host connection to BrailleBridge, where
        //    device.name may still be blank on a fresh bond).
        try {
            val manager = bluetoothManager
            if (manager != null) {
                val connectedGatt = manager.getConnectedDevices(BluetoothProfile.GATT)
                for (dev in connectedGatt) {
                    val name = try { dev.name ?: "" } catch (e: SecurityException) { "" }
                    if (isBrailleBridgeDevice(name)) {
                        if (!connections.containsKey(dev.address) || connections[dev.address]?.isConnected != true) {
                            Log.d(TAG, "Auto-connecting system-connected GATT device: '$name' (${dev.address})")
                            connectDevice(dev)
                        }
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error checking connected GATT devices", e)
        }

        // 2. Fallback: bonded (paired) devices — picks BrailleBridge up again after
        //    an app restart or BT toggle when the OS has not yet reported it GATT-
        //    connected. connectGatt() is idempotent-ish: it joins the existing ACL
        //    link if one is already up.
        try {
            val bonded = adapter.bondedDevices
            if (bonded != null) {
                for (dev in bonded) {
                    val name = try { dev.name ?: "" } catch (e: SecurityException) { "" }
                    if (isBrailleBridgeDevice(name)) {
                        if (!connections.containsKey(dev.address) || connections[dev.address]?.isConnected != true) {
                            Log.d(TAG, "Auto-connecting bonded BrailleBridge device: '$name' (${dev.address})")
                            connectDevice(dev)
                        }
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error checking bonded devices", e)
        }
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "BrailleBridge BLE Service",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Keeps Bluetooth Low Energy bridge active in background"
            }
            val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            manager.createNotificationChannel(channel)
        }
    }

    private fun buildNotification(count: Int): Notification {
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        val contentText = if (count == 0) {
            "BrailleBridge BLE bridge active — Listening for devices"
        } else {
            "BrailleBridge BLE bridge active — $count device(s) connected"
        }

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("BrailleBridge")
            .setContentText(contentText)
            .setSmallIcon(android.R.drawable.stat_sys_data_bluetooth)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .build()
    }

    fun promoteToForeground() {
        try {
            val count = connections.values.count { it.isConnected }
            val notification = buildNotification(count)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                startForeground(
                    NOTIFICATION_ID,
                    notification,
                    ServiceInfo.FOREGROUND_SERVICE_TYPE_CONNECTED_DEVICE
                )
            } else {
                startForeground(NOTIFICATION_ID, notification)
            }
        } catch (e: SecurityException) {
            Log.w(TAG, "SecurityException starting foreground service: ${e.message}")
        } catch (e: Exception) {
            Log.e(TAG, "Error starting foreground service", e)
        }
    }

    private fun updateNotification() {
        val count = connections.values.count { it.isConnected }
        _connectedCount.value = count
        try {
            val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            manager.notify(NOTIFICATION_ID, buildNotification(count))
        } catch (e: Exception) {
            Log.w(TAG, "Error updating notification", e)
        }
    }

    @SuppressLint("MissingPermission")
    fun startScan(highDuty: Boolean = false) {
        val scanner = bluetoothAdapter?.bluetoothLeScanner ?: return
        if (isScanning) {
            if (isHighDutyScan == highDuty) return
            // Reconfigure mode
            try {
                scanner.stopScan(scanCallback)
            } catch (_: Exception) {}
            isScanning = false
        }
        try {
            val settings = ScanSettings.Builder()
                .setScanMode(if (highDuty) ScanSettings.SCAN_MODE_LOW_LATENCY else ScanSettings.SCAN_MODE_LOW_POWER)
                .build()
            scanner.startScan(null, settings, scanCallback)
            isScanning = true
            isHighDutyScan = highDuty
        } catch (e: Exception) {
            Log.e(TAG, "startScan error", e)
        }
    }

    @SuppressLint("MissingPermission")
    fun stopScan() {
        val scanner = bluetoothAdapter?.bluetoothLeScanner ?: return
        if (!isScanning) return
        try {
            scanner.stopScan(scanCallback)
        } catch (e: Exception) {
            Log.e(TAG, "stopScan error", e)
        }
        isScanning = false
        isHighDutyScan = false
    }

    fun startManualScan() {
        startScan(highDuty = true)
        // Automatically revert to low power scan after 7 seconds to prevent CPU & battery drain
        handler.postDelayed({
            if (isScanning && isHighDutyScan) {
                stopScan()
                startScan(highDuty = false)
            }
        }, 7000)
    }

    private fun startPeriodicScanner() {
        periodicScanRunnable?.let { handler.removeCallbacks(it) }
        val r = object : Runnable {
            override fun run() {
                try {
                    // Check if already connected - if connected, we do not need continuous aggressive scanning
                    val hasConnected = connections.values.any { it.isConnected }
                    if (!hasConnected) {
                        startScan(highDuty = false)
                        handler.postDelayed({
                            stopScan()
                        }, 4000)
                    }
                } catch (e: Exception) {
                    // Ignore
                }
                // Periodic scan cycle every 15 seconds to minimize CPU and radio usage
                handler.postDelayed(this, 15000)
            }
        }
        periodicScanRunnable = r
        handler.post(r)
    }

    @SuppressLint("MissingPermission")
    fun connectDevice(device: BluetoothDevice, studentName: String? = null) {
        val address = device.address
        if (connections.containsKey(address)) {
            val existing = connections[address]
            if (existing != null && existing.isConnected) {
                return
            }
        }

        val conn = BleDeviceConn(
            context = this,
            device = device,
            desiredName = studentName,
            onLine = { line ->
                _events.tryEmit(BleEvent.IncomingLine(address, line))
            },
            onChars = { chars ->
                _events.tryEmit(BleEvent.IncomingChars(address, chars))
            },
            onStateChange = { connected, devAddr ->
                updateNotification()
                if (connected) {
                    settingsStore.setLastDeviceAddress(devAddr)
                    _events.tryEmit(BleEvent.DeviceConnected(devAddr, device.name))
                } else {
                    _events.tryEmit(BleEvent.DeviceDisconnected(devAddr))
                }
            }
        )

        connections[address] = conn
        conn.connect()
    }

    fun disconnectDevice(address: String) {
        val conn = connections.remove(address)
        conn?.disconnect()
        updateNotification()
    }

    fun isDeviceConnected(address: String): Boolean {
        return connections[address]?.isConnected == true
    }
}

