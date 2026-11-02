package com.example.ble

class LineFeed(
    private val onLine: (String) -> Unit,
    private val onChars: (String) -> Unit
) {
    companion object {
        // Device control lines — must NEVER appear as typed characters.
        // Matches the Python relay: CONTROL_PREFIXES = ('SYSTEM:', 'LANG:', 'Invalid', 'SHIFT')
        val CONTROL_PREFIXES = listOf("SYSTEM:", "LANG:", "Invalid", "SHIFT")

        fun isControlLine(text: String): Boolean {
            val t = text.trim { it <= ' ' || it == '\r' }
            return CONTROL_PREFIXES.any { t.startsWith(it) }
        }
    }

    private var buffer = StringBuilder()
    private val bootFilter = BootFilter()

    @Synchronized
    fun feed(chunk: String) {
        buffer.append(chunk)
        var nlIndex = buffer.indexOf("\n")
        while (nlIndex >= 0) {
            val rawLine = buffer.substring(0, nlIndex)
            val line = rawLine.trim { it <= ' ' || it == '\r' }
            buffer.delete(0, nlIndex + 1)
            if (line.isNotEmpty() && !bootFilter.dropLine(line)) {
                onLine(line)
            }
            nlIndex = buffer.indexOf("\n")
        }
        if (buffer.isNotEmpty()) {
            val rest = buffer.toString()
            buffer.setLength(0)
            // Defensive: a newline-less chunk that IS a control line (firmware
            // split text/newline across notifications) gets handled as a control
            // line — so backspace and language toggles still work and nothing
            // control-ish is ever shown as typed text.
            val trimmed = rest.trim { it <= ' ' || it == '\r' }
            if (isControlLine(trimmed)) {
                onLine(trimmed)
                return
            }
            if (!bootFilter.dropChunk(rest)) {
                onChars(rest)
            }
        }
    }
}
