package com.example.protocol

import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

data class TimedChar(
    val char: String,
    val time: Long
)

data class FormattedBlock(
    var type: String, // "title", "heading", "question", "answer", "math", "callout", "para", "bullet", "numbered"
    var text: String,
    val time: Long,
    val level: Int = 0 // for headings: 1, 2, 3, 4
)

data class FormattedLine(
    val time: Long,
    val text: String
)

object AutoFormatter {

    private val timeFormat = SimpleDateFormat("HH:mm:ss", Locale.US)

    fun formatTime(timestamp: Long): String {
        return timeFormat.format(Date(timestamp))
    }

    /**
     * Normalize incoming TimedChar stream so single-character packet newlines
     * (from Serial.println per character) are stripped and characters join
     * naturally into words and sentences.
     */
    private fun normalizeStream(chars: List<TimedChar>): List<TimedChar> {
        val out = ArrayList<TimedChar>(chars.size)
        var charsSinceNewline = 0
        for (entry in chars) {
            val raw = entry.char
            if (raw == "\n" || raw == "\r" || raw == "\r\n") {
                if (charsSinceNewline > 2) {
                    out.add(TimedChar("\n", entry.time))
                }
                charsSinceNewline = 0
                continue
            }
            val cleaned = if (raw.contains('\n') || raw.contains('\r')) {
                val stripped = raw.replace("\r", "").replace("\n", "")
                if (stripped.length <= 2) {
                    charsSinceNewline = 0
                    stripped
                } else {
                    raw.replace("\r\n", "\n").replace('\r', '\n')
                }
            } else {
                raw
            }
            if (cleaned.isEmpty()) continue
            for (ch in cleaned) {
                if (ch == '\n') {
                    if (charsSinceNewline > 2) {
                        out.add(TimedChar("\n", entry.time))
                    }
                    charsSinceNewline = 0
                } else {
                    charsSinceNewline++
                    out.add(TimedChar(ch.toString(), entry.time))
                }
            }
        }
        return out
    }

    /**
     * Group characters into readable wrapped lines of words and sentences.
     */
    fun buildReadableLog(chars: List<TimedChar>, maxLine: Int = 52): List<FormattedLine> {
        val normalized = normalizeStream(chars)
        val lines = mutableListOf<FormattedLine>()
        val words = mutableListOf<Pair<String, Long>>()
        var lineLen = 0
        var cur = ""
        var curTime: Long? = null

        fun flushWord() {
            if (cur.isEmpty()) return
            val add = cur.length + if (words.isNotEmpty()) 1 else 0
            if (lineLen + add > maxLine && words.isNotEmpty()) {
                lines.add(FormattedLine(time = words[0].second, text = words.joinToString(" ") { it.first }))
                words.clear()
                lineLen = 0
            }
            words.add(Pair(cur, curTime ?: System.currentTimeMillis()))
            lineLen += add
            cur = ""
            curTime = null
        }

        fun flushLine() {
            if (words.isEmpty()) return
            lines.add(FormattedLine(time = words[0].second, text = words.joinToString(" ") { it.first }))
            words.clear()
            lineLen = 0
        }

        for (entry in normalized) {
            val ch = entry.char
            if (ch == " ") {
                flushWord()
            } else if (ch == "\n" || ch == "\r") {
                flushWord()
                flushLine()
            } else {
                if (cur.isEmpty()) {
                    curTime = entry.time
                }
                cur += ch
            }
        }
        flushWord()
        flushLine()
        return lines
    }

    /**
     * Splits normalized char stream into logical lines where space is a word boundary.
     */
    private fun toLines(chars: List<TimedChar>): List<FormattedLine> {
        val normalized = normalizeStream(chars)
        val lines = mutableListOf<FormattedLine>()
        var cur = ""
        var curTime: Long? = null

        fun push() {
            val t = cur.replace('\u00a0', ' ').trimEnd()
            if (t.isNotEmpty()) {
                lines.add(FormattedLine(time = curTime ?: System.currentTimeMillis(), text = t))
            }
            cur = ""
            curTime = null
        }

        for (entry in normalized) {
            val ch = entry.char
            if (ch == " ") {
                if (cur.isNotEmpty() && !cur.endsWith(" ")) {
                    cur += " "
                }
            } else if (ch == "\n" || ch == "\r") {
                push()
            } else {
                if (cur.isEmpty()) {
                    curTime = entry.time
                }
                cur += ch
            }
        }
        push()
        return lines
    }

    private fun headingLevel(text: String): Int {
        val t = text.trim()
        val lower = t.lowercase(Locale.ROOT)
        if (Regex("^(chapter|অধ্যায়)\\b", RegexOption.IGNORE_CASE).containsMatchIn(lower)) return 1
        if (Regex("^(section|unit|topic|অনুচ্ছেদ)\\b", RegexOption.IGNORE_CASE).containsMatchIn(lower)) return 2
        if (Regex("^(lesson|পাঠ)\\b", RegexOption.IGNORE_CASE).containsMatchIn(lower)) return 3
        if (Regex("^(exercise|অনুশীলন)\\b", RegexOption.IGNORE_CASE).containsMatchIn(lower)) return 4
        return 0
    }

    private fun looksLikeTitle(lineText: String, isFirst: Boolean, total: Int): Boolean {
        if (!isFirst || total < 2) return false
        val t = lineText.trim()
        if (t.isEmpty() || t.length > 60) return false
        if (t.split("\\s+".toRegex()).size > 6) return false
        if (Regex("[.,;:!?।]$").containsMatchIn(t)) return false
        return true
    }

    private fun classifySentence(sentence: String): String {
        val s = sentence.trim()
        val lower = s.lowercase(Locale.ROOT)
        if (s.endsWith("?") || Regex("^(q:|question\\b|প্রশ্ন|what\\b|why\\b|how\\b|when\\b|where\\b|who\\b|which\\b)").containsMatchIn(lower)) {
            return "question"
        }
        if (Regex("^(a:|ans:|answer\\b|উত্তর|solution\\b)").containsMatchIn(lower)) {
            return "answer"
        }
        if (Regex("\\d").containsMatchIn(s) && Regex("[+\\-*/=×÷]").containsMatchIn(s)) {
            return "math"
        }
        if (s.endsWith("!") || Regex("^(note:|important:|remember:|key:|সতর্কতা|দ্রষ্টব্য)").containsMatchIn(lower)) {
            return "callout"
        }
        return "para"
    }

    fun fixPunctuation(text: String): String {
        var t = text.replace('\u00a0', ' ')
        // No space before punctuation
        t = t.replace(Regex(" +([.,;:!?।])"), "$1")
        // Exactly one space after punctuation
        t = t.replace(Regex("([.,;:!?।])(?=[^\\s\\d.,;:!?।])"), "$1 ")
        // Normalize ellipses
        t = t.replace(Regex("\\.{4,}"), "...")
        // Collapse multiple spaces
        t = t.replace(Regex(" {2,}"), " ")
        return t.trim()
    }

    /**
     * Smartly organizes student character stream into conditional formatting blocks:
     * "title", "heading", "question", "answer", "math", "callout", "bullet", "numbered", "para"
     */
    fun format(chars: List<TimedChar>): List<FormattedBlock> {
        val rawLines = toLines(chars)
        val blocks = mutableListOf<FormattedBlock>()

        val paraSentences = mutableListOf<String>()
        var paraStartTime: Long = System.currentTimeMillis()

        fun flushPara() {
            if (paraSentences.isEmpty()) return
            val joined = fixPunctuation(paraSentences.joinToString(" "))
            if (joined.isNotEmpty()) {
                blocks.add(FormattedBlock(type = "para", text = joined, time = paraStartTime))
            }
            paraSentences.clear()
        }

        for (line in rawLines) {
            val t = fixPunctuation(line.text)
            if (t.isEmpty()) {
                flushPara()
                continue
            }

            val bullet = Regex("^[-*•·→]\\s+").containsMatchIn(t)
            val numbered = Regex("^\\d+[.)]\\s+").containsMatchIn(t)
            val head = headingLevel(t)

            if (bullet || numbered) {
                flushPara()
                val cleanText = fixPunctuation(t.replace(Regex("^([-*•·→]|\\d+[.)])\\s+"), ""))
                blocks.add(
                    FormattedBlock(
                        type = if (bullet) "bullet" else "numbered",
                        text = cleanText,
                        time = line.time
                    )
                )
                continue
            }

            if (head > 0) {
                flushPara()
                blocks.add(
                    FormattedBlock(
                        type = "heading",
                        level = head,
                        text = t,
                        time = line.time
                    )
                )
                continue
            }

            // Split line into sentences so questions, answers, math, and callouts get smart conditional cards
            val sentences = t.split(Regex("(?<=[.!?।])\\s+")).map { it.trim() }.filter { it.isNotEmpty() }
            for (s in sentences) {
                val kind = classifySentence(s)
                if (kind == "para") {
                    if (paraSentences.isEmpty()) {
                        paraStartTime = line.time
                    }
                    paraSentences.add(s)
                    if (paraSentences.size >= 3) {
                        flushPara()
                    }
                } else {
                    flushPara()
                    blocks.add(
                        FormattedBlock(
                            type = kind,
                            text = fixPunctuation(s),
                            time = line.time
                        )
                    )
                }
            }
        }
        flushPara()

        val first = blocks.firstOrNull { it.type == "para" || it.type == "heading" }
        if (first != null && first.type == "para" && looksLikeTitle(first.text, true, blocks.size)) {
            first.type = "title"
        }
        return blocks
    }

    fun toText(blocks: List<FormattedBlock>): String {
        val out = mutableListOf<String>()
        var n = 0
        for (b in blocks) {
            when (b.type) {
                "title" -> {
                    out.add(b.text.uppercase(Locale.ROOT))
                    out.add("")
                    n = 0
                }
                "heading" -> {
                    out.add("")
                    out.add(b.text)
                    out.add("")
                    n = 0
                }
                "question" -> {
                    out.add("[Question] ${b.text}")
                    out.add("")
                    n = 0
                }
                "answer" -> {
                    out.add("[Answer] ${b.text}")
                    out.add("")
                    n = 0
                }
                "math" -> {
                    out.add("[Math] ${b.text}")
                    out.add("")
                    n = 0
                }
                "callout" -> {
                    out.add("[Important] ${b.text}")
                    out.add("")
                    n = 0
                }
                "bullet" -> {
                    out.add("• ${b.text}")
                }
                "numbered" -> {
                    n += 1
                    out.add("$n. ${b.text}")
                }
                else -> {
                    out.add(b.text)
                    out.add("")
                    n = 0
                }
            }
        }
        return out.joinToString("\n").replace(Regex("\n{3,}"), "\n\n").trim() + "\n"
    }
}
