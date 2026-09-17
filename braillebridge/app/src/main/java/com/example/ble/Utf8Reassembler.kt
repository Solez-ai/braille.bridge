package com.example.ble

import java.nio.ByteBuffer
import java.nio.CharBuffer
import java.nio.charset.CharsetDecoder
import java.nio.charset.CodingErrorAction
import java.nio.charset.StandardCharsets

class Utf8Reassembler {
    private val decoder: CharsetDecoder = StandardCharsets.UTF_8.newDecoder()
        .onMalformedInput(CodingErrorAction.REPLACE)
        .onUnmappableCharacter(CodingErrorAction.REPLACE)

    private var pendingBytes = ByteArray(0)

    @Synchronized
    fun feed(bytes: ByteArray): String {
        val combined = ByteArray(pendingBytes.size + bytes.size)
        System.arraycopy(pendingBytes, 0, combined, 0, pendingBytes.size)
        System.arraycopy(bytes, 0, combined, pendingBytes.size, bytes.size)

        val byteBuffer = ByteBuffer.wrap(combined)
        val charBuffer = CharBuffer.allocate(combined.size * 2 + 16)

        val result = decoder.decode(byteBuffer, charBuffer, false)
        charBuffer.flip()
        val decoded = charBuffer.toString()

        if (byteBuffer.hasRemaining()) {
            pendingBytes = ByteArray(byteBuffer.remaining())
            byteBuffer.get(pendingBytes)
        } else {
            pendingBytes = ByteArray(0)
        }

        return decoded
    }

    @Synchronized
    fun flush(): String {
        if (pendingBytes.isEmpty()) return ""
        val byteBuffer = ByteBuffer.wrap(pendingBytes)
        val charBuffer = CharBuffer.allocate(pendingBytes.size * 2 + 16)
        decoder.decode(byteBuffer, charBuffer, true)
        decoder.flush(charBuffer)
        charBuffer.flip()
        pendingBytes = ByteArray(0)
        return charBuffer.toString()
    }
}
