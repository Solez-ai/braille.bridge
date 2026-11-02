package com.example.protocol

sealed class DecodedStep {
    data class ChordStep(
        val char: String,
        val chord: Int,
        val shift: Boolean,
        val dots: List<Int>
    ) : DecodedStep()

    data object SpaceStep : DecodedStep()
    data object NewlineStep : DecodedStep()
    data class UnknownStep(val char: String) : DecodedStep()
}

object LearnerEngine {

    data class ReverseEntry(val chord: Int, val shift: Boolean)

    val reverseEn = mutableMapOf<String, ReverseEntry>()
    val reverseBn = mutableMapOf<String, ReverseEntry>()

    private val banglaMulti: List<Pair<String, Int>>

    init {
        fun putEn(ch: String, chord: Int, shift: Boolean) {
            if (!reverseEn.containsKey(ch)) reverseEn[ch] = ReverseEntry(chord, shift)
        }
        fun putBn(ch: String, chord: Int, shift: Boolean) {
            if (!reverseBn.containsKey(ch)) reverseBn[ch] = ReverseEntry(chord, shift)
        }

        // Unshifted entries
        for (e in BrailleDict.brailleDict) {
            e.english?.let { putEn(it, e.chord, false) }
            e.bangla?.let { putBn(it, e.chord, false) }
        }

        // Shift numbers (1-0 map to a-j chords)
        for (i in BrailleDict.numberMap.indices) {
            putEn(BrailleDict.numberMap[i], BrailleDict.numberChords[i], true)
        }

        // Shift uppercase English letters
        for (i in 0 until 26) {
            val lc = ('a'.code + i).toChar().toString()
            reverseEn[lc]?.let {
                putEn(lc.uppercase(), it.chord, true)
            }
        }

        // Shift math & punctuation symbols
        for (s in BrailleDict.shiftSymbols) {
            putEn(s.symbol, s.chord, true)
        }

        // Shift Bangla vowel signs (kar)
        for (s in BrailleDict.banglaShiftMap) {
            s.kar?.let { putBn(it, s.chord, true) }
        }

        // Multi-character Bangla strings (e.g. ক্ষ) matched greedily
        val multi = mutableListOf<Pair<String, Int>>()
        for (e in BrailleDict.brailleDict) {
            if (e.bangla != null && e.bangla.length > 1) {
                multi.add(Pair(e.bangla, e.chord))
            }
        }
        multi.sortByDescending { it.first.length }
        banglaMulti = multi
    }

    fun chordDotsList(chord: Int): List<Int> {
        val dots = mutableListOf<Int>()
        for (d in 0 until 6) {
            if ((chord and (1 shl d)) != 0) {
                dots.add(d + 1)
            }
        }
        return dots
    }

    fun decodeText(text: String, isBangla: Boolean): List<DecodedStep> {
        val steps = mutableListOf<DecodedStep>()
        val map = if (isBangla) reverseBn else reverseEn
        var p = 0
        val chars = text

        while (p < chars.length) {
            val c = chars[p]
            if (c == ' ') {
                steps.add(DecodedStep.SpaceStep)
                p++
                continue
            }
            if (c == '\n' || c == '\r' || c == '\t') {
                steps.add(DecodedStep.NewlineStep)
                p++
                continue
            }

            if (isBangla) {
                // Greedy multi-character conjunct match first
                var hit: Pair<String, Int>? = null
                for (m in banglaMulti) {
                    if (chars.startsWith(m.first, p)) {
                        hit = m
                        break
                    }
                }
                if (hit != null) {
                    steps.add(
                        DecodedStep.ChordStep(
                            char = hit.first,
                            chord = hit.second,
                            shift = false,
                            dots = chordDotsList(hit.second)
                        )
                    )
                    p += hit.first.length
                    continue
                }
            }

            val cStr = c.toString()
            val direct = map[cStr]
            if (direct != null) {
                steps.add(
                    DecodedStep.ChordStep(
                        char = cStr,
                        chord = direct.chord,
                        shift = direct.shift,
                        dots = chordDotsList(direct.chord)
                    )
                )
                p++
                continue
            }

            steps.add(DecodedStep.UnknownStep(cStr))
            p++
        }

        return steps
    }
}
