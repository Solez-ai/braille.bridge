package com.example

import com.example.protocol.DecodedStep
import com.example.protocol.LearnerEngine
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class LearnerEngineTest {

    @Test
    fun `test english decoder`() {
        val steps = LearnerEngine.decodeText("ab", isBangla = false)
        assertEquals(2, steps.size)
        val s0 = steps[0] as DecodedStep.ChordStep
        val s1 = steps[1] as DecodedStep.ChordStep
        assertEquals("a", s0.char)
        assertEquals(listOf(1), s0.dots)
        assertEquals(false, s0.shift)
        assertEquals("b", s1.char)
        assertEquals(listOf(1, 2), s1.dots)
        assertEquals(false, s1.shift)

        val zSteps = LearnerEngine.decodeText("z", isBangla = false)
        val z0 = zSteps[0] as DecodedStep.ChordStep
        assertEquals(listOf(1, 3, 5, 6), z0.dots)
    }

    @Test
    fun `test uppercase english decoder`() {
        val steps = LearnerEngine.decodeText("Hi", isBangla = false)
        assertEquals(2, steps.size)
        val hStep = steps[0] as DecodedStep.ChordStep
        val iStep = steps[1] as DecodedStep.ChordStep

        assertEquals("H", hStep.char)
        assertEquals(19, hStep.chord)
        assertTrue(hStep.shift)

        assertEquals("i", iStep.char)
        assertEquals(8, iStep.chord)
        assertEquals(false, iStep.shift)
    }

    @Test
    fun `test digits decoder`() {
        val steps = LearnerEngine.decodeText("10", isBangla = false)
        assertEquals(2, steps.size)
        val one = steps[0] as DecodedStep.ChordStep
        val zero = steps[1] as DecodedStep.ChordStep

        assertEquals(listOf(1), one.dots)
        assertTrue(one.shift)

        assertEquals(listOf(2, 4, 5), zero.dots)
        assertTrue(zero.shift)
    }

    @Test
    fun `test shift symbols decoder`() {
        val steps = LearnerEngine.decodeText("+,.=", isBangla = false)
        assertEquals(4, steps.size)
        assertEquals(listOf(2, 3, 5), (steps[0] as DecodedStep.ChordStep).dots)
        assertEquals(listOf(2), (steps[1] as DecodedStep.ChordStep).dots)
        assertEquals(listOf(2, 5, 6), (steps[2] as DecodedStep.ChordStep).dots)
        assertEquals(listOf(2, 3, 5, 6), (steps[3] as DecodedStep.ChordStep).dots)
    }

    @Test
    fun `test space and newline steps`() {
        val spaceSteps = LearnerEngine.decodeText("a b", isBangla = false)
        assertEquals(3, spaceSteps.size)
        assertTrue(spaceSteps[0] is DecodedStep.ChordStep)
        assertTrue(spaceSteps[1] is DecodedStep.SpaceStep)
        assertTrue(spaceSteps[2] is DecodedStep.ChordStep)

        val nlSteps = LearnerEngine.decodeText("a\nb", isBangla = false)
        assertEquals(3, nlSteps.size)
        assertTrue(nlSteps[0] is DecodedStep.ChordStep)
        assertTrue(nlSteps[1] is DecodedStep.NewlineStep)
        assertTrue(nlSteps[2] is DecodedStep.ChordStep)
    }

    @Test
    fun `test bangla greedy multi-char matching`() {
        // 'ক্ষ' should match as single chord 0b011111 (dots 1, 2, 3, 4, 5)
        val ksh = LearnerEngine.decodeText("ক্ষ", isBangla = true)
        assertEquals(1, ksh.size)
        val step = ksh[0] as DecodedStep.ChordStep
        assertEquals("ক্ষ", step.char)
        assertEquals(listOf(1, 2, 3, 4, 5), step.dots)
        assertEquals(false, step.shift)

        // 'বাংলা' sequence
        val banglaSteps = LearnerEngine.decodeText("বাংলা", isBangla = true)
        assertEquals(5, banglaSteps.size)
        assertEquals(listOf(1, 2), (banglaSteps[0] as DecodedStep.ChordStep).dots)       // ব
        assertEquals(listOf(3, 4, 5), (banglaSteps[1] as DecodedStep.ChordStep).dots)    // া
        assertEquals(listOf(5, 6), (banglaSteps[2] as DecodedStep.ChordStep).dots)       // ং
        assertEquals(listOf(1, 2, 3), (banglaSteps[3] as DecodedStep.ChordStep).dots)    // ল
        assertEquals(listOf(3, 4, 5), (banglaSteps[4] as DecodedStep.ChordStep).dots)    // া
    }

    @Test
    fun `test bangla kar shift status`() {
        val aKar = LearnerEngine.decodeText("া", isBangla = true)[0] as DecodedStep.ChordStep
        assertEquals(listOf(3, 4, 5), aKar.dots)
        assertTrue(aKar.shift)

        val iKar = LearnerEngine.decodeText("ি", isBangla = true)[0] as DecodedStep.ChordStep
        assertEquals(listOf(2, 3, 6), iKar.dots)
        assertEquals(false, iKar.shift) // unshifted in Bharati Braille dictionary
    }
}
