package com.example

import com.example.ble.LineFeed
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class LineFeedTest {

    @Test
    fun `test control lines with newline`() {
        val lines = mutableListOf<String>()
        val chars = mutableListOf<String>()
        val feed = LineFeed(onLine = { lines.add(it) }, onChars = { chars.add(it) })

        feed.feed("SYSTEM:BKSP\n")
        feed.feed("LANG:bn\n")
        feed.feed("SYSTEM:CAP_ONCE\n")
        feed.feed("SYSTEM:CAP_LOCK\n")
        feed.feed("SYSTEM:CAP_OFF\n")

        assertEquals(listOf("SYSTEM:BKSP", "LANG:bn", "SYSTEM:CAP_ONCE", "SYSTEM:CAP_LOCK", "SYSTEM:CAP_OFF"), lines)
        assertTrue(chars.isEmpty())
    }

    @Test
    fun `test control lines without newline`() {
        val lines = mutableListOf<String>()
        val chars = mutableListOf<String>()
        val feed = LineFeed(onLine = { lines.add(it) }, onChars = { chars.add(it) })

        feed.feed("SYSTEM:CAP_ONCE")
        feed.feed("LANG:en")

        assertEquals(listOf("SYSTEM:CAP_ONCE", "LANG:en"), lines)
        assertTrue(chars.isEmpty())
    }

    @Test
    fun `test typed character stream`() {
        val lines = mutableListOf<String>()
        val chars = mutableListOf<String>()
        val feed = LineFeed(onLine = { lines.add(it) }, onChars = { chars.add(it) })

        feed.feed("h")
        feed.feed("e")
        feed.feed("l")
        feed.feed("l")
        feed.feed("o")

        assertTrue(lines.isEmpty())
        assertEquals(listOf("h", "e", "l", "l", "o"), chars)
    }

    @Test
    fun `test esp32 boot preamble suppressed`() {
        val lines = mutableListOf<String>()
        val chars = mutableListOf<String>()
        val feed = LineFeed(onLine = { lines.add(it) }, onChars = { chars.add(it) })

        feed.feed("ets Jul 29 2019 12:21:46\n")
        feed.feed("rst:0x1 (POWERON_RESET),boot:0x13 (SPI_FAST_FLASH_BOOT)\n")
        feed.feed("configsip: 0, SPIWP:0xee\n")
        feed.feed("clk_drv:0x00,q_drv:0x00,d_drv:0x00,cs0_drv:0x00,hd_drv:0x00,wp_drv:0x00\n")
        feed.feed("mode:DIO, clock div:2\n")
        feed.feed("load:0x3fff0018,len:4\n")
        feed.feed("load:0x3fff001c,len:1044\n")
        feed.feed("entry 0x400804f0\n")

        // Once entry is reached, firmware banner appears
        feed.feed("SYSTEM: BrailleBridge Connected.\n")
        feed.feed("a")

        assertEquals(listOf("SYSTEM: BrailleBridge Connected."), lines)
        assertEquals(listOf("a"), chars)
    }
}
