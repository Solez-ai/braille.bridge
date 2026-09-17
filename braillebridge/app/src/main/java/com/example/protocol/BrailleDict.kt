package com.example.protocol

data class BrailleEntry(
    val chord: Int,
    val english: String?,
    val bangla: String?
)

data class ShiftSymbol(
    val chord: Int,
    val symbol: String
)

data class BanglaShiftEntry(
    val chord: Int,
    val kar: String?
)

object BrailleDict {

    val brailleDict: List<BrailleEntry> = listOf(
        BrailleEntry(0b000001, "a", "\u0985"),
        BrailleEntry(0b000011, "b", "\u09AC"),
        BrailleEntry(0b001001, "c", "\u099A"),
        BrailleEntry(0b011001, "d", "\u09A6"),
        BrailleEntry(0b010001, "e", "\u098F"),
        BrailleEntry(0b001011, "f", null),
        BrailleEntry(0b011011, "g", "\u0997"),
        BrailleEntry(0b010011, "h", "\u09B9"),
        BrailleEntry(0b001000, "i", "\u09CD"),
        BrailleEntry(0b011010, "j", "\u099C"),
        BrailleEntry(0b000101, "k", "\u0995"),
        BrailleEntry(0b000111, "l", "\u09B2"),
        BrailleEntry(0b001101, "m", "\u09AE"),
        BrailleEntry(0b011101, "n", "\u09A8"),
        BrailleEntry(0b010101, "o", "\u0993"),
        BrailleEntry(0b001111, "p", "\u09AA"),
        BrailleEntry(0b011111, "q", "\u0995\u09CD\u09B7"),
        BrailleEntry(0b010111, "r", "\u09B0"),
        BrailleEntry(0b001100, "s", "\u0990"),
        BrailleEntry(0b011100, "t", "\u0986"),
        BrailleEntry(0b100101, "u", "\u0989"),
        BrailleEntry(0b100111, "v", "\u09CB"),
        BrailleEntry(0b111010, "w", null),
        BrailleEntry(0b101101, "x", "\u09DF"),
        BrailleEntry(0b111101, "y", "\u09AF"),
        BrailleEntry(0b110101, "z", "\u09DC"),
        BrailleEntry(0b001010, null, "\u0987"),
        BrailleEntry(0b010010, null, "\u099E"),
        BrailleEntry(0b001110, null, "\u09B8"),
        BrailleEntry(0b111111, null, "\u09A2"),
        BrailleEntry(0b100001, null, "\u099B"),
        BrailleEntry(0b100011, null, "\u0998"),
        BrailleEntry(0b011000, null, "\u09AD"),
        BrailleEntry(0b111001, null, "\u09A5"),
        BrailleEntry(0b110110, null, "\u09A0"),
        BrailleEntry(0b101010, null, "\u0994"),
        BrailleEntry(0b010110, null, "\u09AB"),
        BrailleEntry(0b110100, null, "\u099D"),
        BrailleEntry(0b101011, null, "\u09A1"),
        BrailleEntry(0b010100, null, "\u0988"),
        BrailleEntry(0b011110, null, "\u09A4"),
        BrailleEntry(0b101000, null, "\u0996"),
        BrailleEntry(0b101100, null, "\u0999"),
        BrailleEntry(0b111110, null, "\u099F"),
        BrailleEntry(0b101110, null, "\u09A7"),
        BrailleEntry(0b111100, null, "\u09A3"),
        BrailleEntry(0b110011, null, "\u098A"),
        BrailleEntry(0b101111, null, "\u09B7"),
        BrailleEntry(0b110001, null, "\u09B6"),
        BrailleEntry(0b110000, null, "\u0982"),
        BrailleEntry(0b010000, null, "\u0981"),
        BrailleEntry(0b100110, null, "\u09BF"),
        BrailleEntry(0b110010, null, "\u09C2"),
        BrailleEntry(0b100010, null, "\u09B8")
    )

    val numberChords = listOf(
        0b000001, 0b000011, 0b001001, 0b011001, 0b010001,
        0b001011, 0b011011, 0b010011, 0b001000, 0b011010
    )
    val numberMap = listOf("1", "2", "3", "4", "5", "6", "7", "8", "9", "0")

    val shiftSymbols: List<ShiftSymbol> = listOf(
        ShiftSymbol(0b010110, "+"),
        ShiftSymbol(0b100100, "-"),
        ShiftSymbol(0b100110, "\u00D7"),
        ShiftSymbol(0b110110, "="),
        ShiftSymbol(0b001100, "\u00F7"),
        ShiftSymbol(0b000010, ","),
        ShiftSymbol(0b000110, ";"),
        ShiftSymbol(0b010010, ":"),
        ShiftSymbol(0b110010, ".")
    )

    val banglaShiftMap: List<BanglaShiftEntry> = listOf(
        BanglaShiftEntry(0b000001, null),
        BanglaShiftEntry(0b011100, "\u09BE"),
        BanglaShiftEntry(0b001010, "\u09BF"),
        BanglaShiftEntry(0b010100, "\u09C0"),
        BanglaShiftEntry(0b100101, "\u09C1"),
        BanglaShiftEntry(0b110011, "\u09C2"),
        BanglaShiftEntry(0b010001, "\u09C7"),
        BanglaShiftEntry(0b001100, "\u09C8"),
        BanglaShiftEntry(0b010101, "\u09CB"),
        BanglaShiftEntry(0b101010, "\u09CC")
    )

    val charToChord: Map<String, Int> = buildMap {
        for (e in brailleDict) {
            e.english?.let { put(it, e.chord); put(it.uppercase(), e.chord) }
            e.bangla?.let { put(it, e.chord) }
        }
        for (i in numberMap.indices) {
            put(numberMap[i], numberChords[i])
        }
        for (s in shiftSymbols) {
            put(s.symbol, s.chord)
        }
        for (s in banglaShiftMap) {
            s.kar?.let { put(it, s.chord) }
        }
    }

    fun lookupChord(chord: Int, isBangla: Boolean): String? {
        for (e in brailleDict) {
            if (e.chord == chord) {
                return if (isBangla && e.bangla != null) e.bangla
                else if (!isBangla && e.english != null) e.english
                else null
            }
        }
        return null
    }

    fun lookupNumber(chord: Int): String? {
        val i = numberChords.indexOf(chord)
        return if (i >= 0) numberMap[i] else null
    }

    fun lookupShiftSymbol(chord: Int): String? {
        for (s in shiftSymbols) {
            if (s.chord == chord) return s.symbol
        }
        return null
    }

    fun lookupBanglaShift(chord: Int): String? {
        for (s in banglaShiftMap) {
            if (s.chord == chord) return s.kar
        }
        return null
    }

    fun resolveChord(chord: Int, isBangla: Boolean, shiftActive: Boolean): String? {
        if (chord == 0) return null
        if (shiftActive) {
            // Priority: numbers -> math/punct -> uppercase EN -> kar BN -> fallback normal BN char -> else ignore
            val num = lookupNumber(chord)
            if (num != null) return num

            val sym = lookupShiftSymbol(chord)
            if (sym != null) return sym

            if (!isBangla) {
                val en = lookupChord(chord, false)
                if (en != null && en.length == 1 && en[0] in 'a'..'z') {
                    return en.uppercase()
                }
            } else {
                val kar = lookupBanglaShift(chord)
                if (kar != null) return kar
                val bn = lookupChord(chord, true)
                if (bn != null) return bn
            }
            return null
        } else {
            return lookupChord(chord, isBangla)
        }
    }
}
