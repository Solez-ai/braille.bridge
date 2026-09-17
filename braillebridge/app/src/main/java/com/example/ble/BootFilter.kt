package com.example.ble

class BootFilter {
    private var suppress = false

    companion object {
        val BOOT_PREFIXES = listOf(
            "ets ", "rst:0x", "boot:0x", "configSPIWP", "clk_drv:",
            "q_drv:", "d_drv:", "cs0_drv:", "hd_drv:", "wp_drv:",
            "mode:DIO", "load:0x", "entry 0x"
        )
    }

    fun isBootLine(line: String): Boolean {
        return BOOT_PREFIXES.any { line.startsWith(it) }
    }

    fun dropLine(line: String): Boolean {
        if (line.startsWith("ets ")) {
            suppress = true
            return true
        }
        if (suppress) {
            if (line.startsWith("entry 0x") || line.startsWith("SYSTEM:")) {
                suppress = false
            } else {
                return true
            }
        }
        return isBootLine(line)
    }

    fun dropChunk(chunk: String): Boolean {
        if (chunk.startsWith("ets ")) {
            suppress = true
            return true
        }
        return suppress || isBootLine(chunk)
    }
}
