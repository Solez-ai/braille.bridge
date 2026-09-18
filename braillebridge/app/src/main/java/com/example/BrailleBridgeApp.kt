package com.example

import android.app.Application
import android.content.Intent
import android.os.Build
import android.util.Log
import androidx.core.content.ContextCompat
import com.example.ble.BleProxyService
import com.example.data.AppDatabase

class BrailleBridgeApp : Application() {
    val database: AppDatabase by lazy { AppDatabase.getDatabase(this) }

    override fun onCreate() {
        super.onCreate()
        Log.d("BrailleBridgeApp", "Initializing BrailleBridge application and starting BleProxyService")
        try {
            val serviceIntent = Intent(this, BleProxyService::class.java)
            // Android 12+ requires startForegroundService whenever the app is not in
            // a foreground state at start time; ContextCompat picks the right call.
            ContextCompat.startForegroundService(this, serviceIntent)
        } catch (e: Exception) {
            Log.e("BrailleBridgeApp", "Could not start BleProxyService immediately", e)
        }
    }
}
