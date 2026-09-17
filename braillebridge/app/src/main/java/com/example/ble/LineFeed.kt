package com.example.ble

class LineFeed(
    private val onLine: (String) -> Unit,
    private val onChars: (String) -> Unit
) {
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
            if (!bootFilter.dropChunk(rest)) {
                onChars(rest)
            }
        }
    }
}
