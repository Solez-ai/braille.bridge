package com.example

import com.example.protocol.BrailleDict
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Test

class BrailleDictTest {

    @Test
    fun `test english unshifted letters`() {
        assertEquals("a", BrailleDict.resolveChord(0b000001, isBangla = false, shiftActive = false))
        assertEquals("b", BrailleDict.resolveChord(0b000011, isBangla = false, shiftActive = false))
        assertEquals("c", BrailleDict.resolveChord(0b001001, isBangla = false, shiftActive = false))
        assertEquals("z", BrailleDict.resolveChord(0b110101, isBangla = false, shiftActive = false))
    }

    @Test
    fun `test dot 6 capital indicator`() {
        // Unshifted 'a' with CAPS_ONCE produces uppercase 'A'
        val capitalA = BrailleDict.resolveChord(0b000001, isBangla = false, shiftActive = false, capsMode = BrailleDict.CapsMode.ONCE)
        assertEquals("A", capitalA)

        // Unshifted 'z' with CAPS_LOCK produces uppercase 'Z'
        val capitalZ = BrailleDict.resolveChord(0b110101, isBangla = false, shiftActive = false, capsMode = BrailleDict.CapsMode.LOCK)
        assertEquals("Z", capitalZ)

        // Unshifted 'a' with CAPS_OFF produces lowercase 'a'
        val lowerA = BrailleDict.resolveChord(0b000001, isBangla = false, shiftActive = false, capsMode = BrailleDict.CapsMode.OFF)
        assertEquals("a", lowerA)
    }

    @Test
    fun `test numbers via shift`() {
        // Shift + a-j chords produce digits 1-0
        assertEquals("1", BrailleDict.resolveChord(0b000001, isBangla = false, shiftActive = true))
        assertEquals("2", BrailleDict.resolveChord(0b000011, isBangla = false, shiftActive = true))
        assertEquals("3", BrailleDict.resolveChord(0b001001, isBangla = false, shiftActive = true))
        assertEquals("4", BrailleDict.resolveChord(0b011001, isBangla = false, shiftActive = true))
        assertEquals("5", BrailleDict.resolveChord(0b010001, isBangla = false, shiftActive = true))
        assertEquals("6", BrailleDict.resolveChord(0b001011, isBangla = false, shiftActive = true))
        assertEquals("7", BrailleDict.resolveChord(0b011011, isBangla = false, shiftActive = true))
        assertEquals("8", BrailleDict.resolveChord(0b010011, isBangla = false, shiftActive = true))
        assertEquals("9", BrailleDict.resolveChord(0b001000, isBangla = false, shiftActive = true))
        assertEquals("0", BrailleDict.resolveChord(0b011010, isBangla = false, shiftActive = true))
    }

    @Test
    fun `test shift symbols`() {
        assertEquals("+", BrailleDict.resolveChord(0b010110, isBangla = false, shiftActive = true))
        assertEquals("-", BrailleDict.resolveChord(0b100100, isBangla = false, shiftActive = true))
        assertEquals("×", BrailleDict.resolveChord(0b100110, isBangla = false, shiftActive = true))
        assertEquals("=", BrailleDict.resolveChord(0b110110, isBangla = false, shiftActive = true))
        assertEquals("÷", BrailleDict.resolveChord(0b001100, isBangla = false, shiftActive = true))
        assertEquals(",", BrailleDict.resolveChord(0b000010, isBangla = false, shiftActive = true))
        assertEquals(";", BrailleDict.resolveChord(0b000110, isBangla = false, shiftActive = true))
        assertEquals(":", BrailleDict.resolveChord(0b010010, isBangla = false, shiftActive = true))
        assertEquals(".", BrailleDict.resolveChord(0b110010, isBangla = false, shiftActive = true))
    }

    @Test
    fun `test bangla bharati characters`() {
        assertEquals("অ", BrailleDict.resolveChord(0b000001, isBangla = true, shiftActive = false))
        assertEquals("ব", BrailleDict.resolveChord(0b000011, isBangla = true, shiftActive = false))
        assertEquals("ক", BrailleDict.resolveChord(0b000101, isBangla = true, shiftActive = false))
        assertEquals("ক্ষ", BrailleDict.resolveChord(0b011111, isBangla = true, shiftActive = false))
        assertEquals("ৱ", BrailleDict.resolveChord(0b100111, isBangla = true, shiftActive = false))
    }

    @Test
    fun `test bangla shift kar signs`() {
        assertEquals("া", BrailleDict.resolveChord(0b011100, isBangla = true, shiftActive = true))
        assertEquals("ি", BrailleDict.resolveChord(0b001010, isBangla = true, shiftActive = true))
        assertEquals("ী", BrailleDict.resolveChord(0b010100, isBangla = true, shiftActive = true))
        assertEquals("ু", BrailleDict.resolveChord(0b100101, isBangla = true, shiftActive = true))
        assertEquals("ূ", BrailleDict.resolveChord(0b110011, isBangla = true, shiftActive = true))
        assertEquals("ে", BrailleDict.resolveChord(0b010001, isBangla = true, shiftActive = true))
        assertEquals("ৈ", BrailleDict.resolveChord(0b001100, isBangla = true, shiftActive = true))
        assertEquals("ো", BrailleDict.resolveChord(0b010101, isBangla = true, shiftActive = true))
        assertEquals("ৌ", BrailleDict.resolveChord(0b101010, isBangla = true, shiftActive = true))
    }
}
