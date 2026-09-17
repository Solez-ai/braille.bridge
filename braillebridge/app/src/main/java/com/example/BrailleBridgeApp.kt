package com.example

import android.app.Application
import android.content.Intent
import android.os.Build
import android.util.Log
import com.example.ble.BleProxyService
import com.example.data.AppDatabase

class BrailleBridgeApp : Application() {
    val database: AppDatabase by lazy { AppDatabase.getDatabase(this) }

    override fun onCreate() {
        super.onCreate()
        Log.d("BrailleBridgeApp", "Initializing BrailleBridge application and starting BleProxyService")
        try {
            val serviceIntent = Intent(this, BleProxyService::class.java)
            startService(serviceIntent)
        } catch (e: Exception) {
            Log.e("BrailleBridgeApp", "Could not start BleProxyService immediately", e)
        }
    }
}
