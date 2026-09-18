package com.example.ble

class BootFilter {
    private var suppress = false
    private var suppressAtMs = 0L

    companion object {
        /** Boot spam never legitimately lasts longer than this — a latch beyond it means
         *  the boot banner was truncated (e.g. app connected mid-boot) and suppressing
         *  further would eat real typed characters forever. */
        private const val SUPPRESS_TIMEOUT_MS = 2000L

        val BOOT_PREFIXES = listOf(
            "ets ", "rst:0x", "boot:0x", "configSPIWP", "clk_drv:",
            "q_drv:", "d_drv:", "cs0_drv:", "hd_drv:", "wp_drv:",
            "mode:DIO", "load:0x", "entry 0x"
        )
    }

    private fun suppressExpired(): Boolean {
        if (!suppress) return false
        if (System.currentTimeMillis() - suppressAtMs > SUPPRESS_TIMEOUT_MS) {
            suppress = false
        }
        return !suppress
    }

    fun isBootLine(line: String): Boolean {
        return BOOT_PREFIXES.any { line.startsWith(it) }
    }

    fun dropLine(line: String): Boolean {
        if (line.startsWith("ets ")) {
            if (!suppress) {
                suppress = true
                suppressAtMs = System.currentTimeMillis()
            }
            return true
        }
        if (suppress) {
            if (line.startsWith("entry 0x") || line.startsWith("SYSTEM:") ||
                line.startsWith("LANG:") || suppressExpired()) {
                suppress = false
            } else {
                return true
            }
        }
        return isBootLine(line)
    }

    fun dropChunk(chunk: String): Boolean {
        if (chunk.startsWith("ets ")) {
            if (!suppress) {
                suppress = true
                suppressAtMs = System.currentTimeMillis()
            }
            return true
        }
        return suppress && !suppressExpired() || isBootLine(chunk)
    }
}
