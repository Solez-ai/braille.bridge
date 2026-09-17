package com.example.data

import android.content.Context
import android.content.SharedPreferences
import org.json.JSONObject

class SettingsStore(context: Context) {
    private val prefs: SharedPreferences = context.getSharedPreferences("bb_settings", Context.MODE_PRIVATE)

    fun getTheme(): String {
        return prefs.getString("theme", "dark") ?: "dark"
    }

    fun setTheme(theme: String) {
        prefs.edit().putString("theme", theme).apply()
    }

    fun getLastDeviceAddress(): String? {
        return prefs.getString("last_device_address", null)
    }

    fun setLastDeviceAddress(address: String?) {
        prefs.edit().putString("last_device_address", address).apply()
    }

    fun getAssignments(): Map<String, String> {
        val json = prefs.getString("assignments", "{}") ?: "{}"
        val map = mutableMapOf<String, String>()
        try {
            val obj = JSONObject(json)
            val keys = obj.keys()
            while (keys.hasNext()) {
                val k = keys.next()
                map[k] = obj.getString(k)
            }
        } catch (e: Exception) {
            // Ignore
        }
        return map
    }

    fun setAssignment(studentName: String, deviceAddress: String?) {
        val map = getAssignments().toMutableMap()
        if (deviceAddress.isNullOrEmpty()) {
            map.remove(studentName)
        } else {
            map[studentName] = deviceAddress
        }
        val obj = JSONObject(map as Map<*, *>)
        prefs.edit().putString("assignments", obj.toString()).apply()
    }
}
