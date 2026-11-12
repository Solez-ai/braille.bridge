package com.example

import com.example.protocol.AutoFormatter
import com.example.protocol.TimedChar
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class AutoFormatterTest {

    @Test
    fun `test punctuation fixing`() {
        assertEquals("Hello, world!", AutoFormatter.fixPunctuation("Hello , world !"))
        assertEquals("One... two.", AutoFormatter.fixPunctuation("One..... two."))
        assertEquals("একটি বাক্য। দ্বিতীয় বাক্য।", AutoFormatter.fixPunctuation("একটি বাক্য ।দ্বিতীয় বাক্য।"))
    }

    @Test
    fun `test build readable log word wrapping`() {
        val now = System.currentTimeMillis()
        val chars = "The quick brown fox jumps over the lazy dog".map {
            TimedChar(it.toString(), now)
        }
        val lines = AutoFormatter.buildReadableLog(chars, maxLine = 20)
        assertTrue(lines.size > 1)
        val joined = lines.joinToString(" ") { it.text }
        assertEquals("The quick brown fox jumps over the lazy dog", joined)
    }

    @Test
    fun `test single char packet newlines stripped into sentences`() {
        val now = System.currentTimeMillis()
        // Simulate hardware sending Serial.println per character
        val raw = listOf("h", "\n", "e", "\n", "l", "\n", "l", "\n", "o", "\n", " ", "\n", "w", "\n", "o", "\n", "r", "\n", "l", "\n", "d")
        val chars = raw.map { TimedChar(it, now) }
        val blocks = AutoFormatter.format(chars)
        assertEquals(1, blocks.size)
        assertEquals("hello world", blocks[0].text)
    }

    @Test
    fun `test conditional formatting blocks question answer math callout`() {
        val now = System.currentTimeMillis()
        val input = "Chapter 1: Physics\nWhat is velocity? Ans: Velocity is speed with direction. 10 + 20 = 30. Remember: Always include units!\n"
        val chars = input.map { TimedChar(it.toString(), now) }
        val blocks = AutoFormatter.format(chars)
        val types = blocks.map { it.type }
        assertTrue(types.contains("heading"))
        assertTrue(types.contains("question"))
        assertTrue(types.contains("answer"))
        assertTrue(types.contains("math"))
        assertTrue(types.contains("callout"))
    }

    @Test
    fun `test auto format structure and toText`() {
        val now = System.currentTimeMillis()
        val input = "Chapter 1: Introduction\nThis is a paragraph.\n* First bullet\n* Second bullet\n1. Numbered item\n"
        val chars = input.map { TimedChar(it.toString(), now) }

        val blocks = AutoFormatter.format(chars)
        assertTrue(blocks.any { it.type == "heading" && it.level == 1 })
        assertTrue(blocks.any { it.type == "para" })
        assertTrue(blocks.any { it.type == "bullet" })
        assertTrue(blocks.any { it.type == "numbered" })

        val text = AutoFormatter.toText(blocks)
        assertTrue(text.contains("Chapter 1: Introduction"))
        assertTrue(text.contains("This is a paragraph."))
        assertTrue(text.contains("• First bullet"))
        assertTrue(text.contains("1. Numbered item"))
    }
}
