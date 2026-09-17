package com.example.protocol

import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

data class TimedChar(
    val char: String,
    val time: Long
)

data class FormattedBlock(
    var type: String, // "title", "heading", "para", "bullet", "numbered"
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
     * Group characters into readable wrapped lines.
     * Each line is prefixed with the timestamp of the first character typed on it.
     */
    fun buildReadableLog(chars: List<TimedChar>, maxLine: Int = 52): List<FormattedLine> {
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

        for (entry in chars) {
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
     * Splits raw char stream into logical lines where space is a word boundary.
     */
    private fun toLines(chars: List<TimedChar>): List<FormattedLine> {
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

        for (entry in chars) {
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
        if (Regex("^(section|অনুচ্ছেদ)\\b", RegexOption.IGNORE_CASE).containsMatchIn(lower)) return 2
        if (Regex("^(lesson|পাঠ)\\b", RegexOption.IGNORE_CASE).containsMatchIn(lower)) return 3
        if (Regex("^(exercise|অনুশীলন|question|প্রশ্ন)\\b", RegexOption.IGNORE_CASE).containsMatchIn(lower)) return 4
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

    fun format(chars: List<TimedChar>): List<FormattedBlock> {
        val rawLines = toLines(chars)
        val blocks = mutableListOf<FormattedBlock>()

        var paraLines = mutableListOf<FormattedLine>()

        fun flushPara() {
            if (paraLines.isEmpty()) return
            val joined = paraLines.joinToString(" ") { it.text.trim() }
            val text = fixPunctuation(joined)
            blocks.add(FormattedBlock(type = "para", text = text, time = paraLines[0].time))
            paraLines.clear()
        }

        for (idx in rawLines.indices) {
            val line = rawLines[idx]
            val t = line.text.trim()
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
                blocks.add(FormattedBlock(
                    type = if (bullet) "bullet" else "numbered",
                    text = cleanText,
                    time = line.time
                ))
                continue
            }

            if (head > 0) {
                flushPara()
                blocks.add(FormattedBlock(
                    type = "heading",
                    level = head,
                    text = fixPunctuation(t),
                    time = line.time
                ))
                continue
            }

            paraLines.add(line)
            if (idx == rawLines.size - 1) {
                flushPara()
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
