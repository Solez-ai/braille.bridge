package com.example.ui.exports

import android.content.Intent
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Download
import androidx.compose.material.icons.filled.GTranslate
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.data.ExportEntity
import com.example.data.getInitials
import com.example.protocol.AutoFormatter
import com.example.protocol.BBTranslate
import com.example.protocol.FormattedBlock
import com.example.ui.MainViewModel
import com.example.ui.components.LanguageDropdown
import com.example.ui.theme.AccentGreen
import com.example.ui.theme.Gold
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Composable
fun ReviewScreen(
    studentGroup: StudentLogGroup,
    initialExport: ExportEntity? = null,
    viewModel: MainViewModel,
    onBack: () -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val timeFormat = remember { SimpleDateFormat("MMM dd · HH:mm", Locale.US) }

    // Allow viewing all sessions combined ("ALL") or a specific session ID
    var selectedSessionId by remember(initialExport) {
        mutableStateOf(initialExport?.id ?: "ALL")
    }

    val originalBlocks = remember(studentGroup.sessions, selectedSessionId) {
        val rawBlocks = if (selectedSessionId == "ALL") {
            studentGroup.sessions
                .sortedBy { it.created }
                .flatMap { viewModel.parseBlocks(it.blocksJson) }
        } else {
            val found = studentGroup.sessions.find { it.id == selectedSessionId }
            if (found != null) viewModel.parseBlocks(found.blocksJson) else emptyList()
        }
        // Re-run through AutoFormatter if legacy single-char blocks exist so text is always sentences/words
        if (rawBlocks.size > 3 && rawBlocks.all { it.text.length <= 2 }) {
            val chars = rawBlocks.map { com.example.protocol.TimedChar(it.text, it.time) }
            AutoFormatter.format(chars)
        } else {
            rawBlocks
        }
    }

    var selectedLanguage by remember { mutableStateOf("en") }
    var translatedBlocks by remember { mutableStateOf<List<FormattedBlock>?>(null) }
    var isTranslating by remember { mutableStateOf(false) }
    var showingTranslation by remember { mutableStateOf(false) }
    var translationFeedback by remember { mutableStateOf<String?>(null) }
    var translationError by remember { mutableStateOf<String?>(null) }
    var inFlightJob by remember { mutableStateOf<Job?>(null) }

    val translatedCache = remember(selectedSessionId) {
        mutableMapOf<String, Pair<List<FormattedBlock>, String>>()
    }

    fun performTranslation(targetCode: String) {
        selectedLanguage = targetCode
        translationError = null

        if (originalBlocks.isEmpty() || originalBlocks.all { it.text.isBlank() }) {
            translationError = "Nothing to translate"
            return
        }

        val cached = translatedCache[targetCode]
        if (cached != null) {
            translatedBlocks = cached.first
            translationFeedback = cached.second
            showingTranslation = true
            return
        }

        inFlightJob?.cancel()
        isTranslating = true
        inFlightJob = scope.launch {
            val combined = originalBlocks.joinToString("\n\n") { it.text }
            val res = BBTranslate.translate(combined, targetCode)
            isTranslating = false
            if (res.ok) {
                val transLines = res.text.split("\n\n")
                val newBlocks = originalBlocks.mapIndexed { idx, blk ->
                    val transText = transLines.getOrNull(idx) ?: blk.text
                    blk.copy(text = transText)
                }
                translatedCache[targetCode] = Pair(newBlocks, res.feedback)
                translatedBlocks = newBlocks
                translationFeedback = res.feedback
                translationError = null
                showingTranslation = true
            } else {
                translationError = res.error
            }
        }
    }

    val currentBlocks = if (showingTranslation && translatedBlocks != null) translatedBlocks!! else originalBlocks
    val fullPlainText = remember(currentBlocks) { currentBlocks.joinToString(" ") { it.text }.trim() }
    val wordCount = remember(fullPlainText) {
        if (fullPlainText.isBlank()) 0 else fullPlainText.split(Regex("\\s+")).size
    }

    val colorParsed = try {
        Color(android.graphics.Color.parseColor(studentGroup.colorHex))
    } catch (e: Exception) {
        MaterialTheme.colorScheme.primary
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        // Top Header Card: Student identity + Back + Share + Translate
        Surface(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(14.dp),
            color = MaterialTheme.colorScheme.surface,
            border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(12.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier.weight(1f)
                    ) {
                        IconButton(onClick = onBack, modifier = Modifier.size(36.dp)) {
                            Icon(
                                imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                                contentDescription = "Back to Students",
                                tint = MaterialTheme.colorScheme.onSurface
                            )
                        }
                        Spacer(modifier = Modifier.width(6.dp))
                        Box(
                            modifier = Modifier
                                .size(34.dp)
                                .clip(CircleShape)
                                .background(colorParsed),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = getInitials(studentGroup.studentName),
                                color = Color.White,
                                fontWeight = FontWeight.Bold,
                                fontSize = 12.sp
                            )
                        }
                        Spacer(modifier = Modifier.width(10.dp))
                        Column {
                            Text(
                                text = studentGroup.studentName,
                                fontWeight = FontWeight.Bold,
                                fontSize = 16.sp,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis,
                                color = MaterialTheme.colorScheme.onSurface
                            )
                            Text(
                                text = "$wordCount words · ${studentGroup.totalChars} chars",
                                fontSize = 11.sp,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }

                    Button(
                        onClick = {
                            val textToExport = AutoFormatter.toText(currentBlocks)
                            val shareIntent = Intent(Intent.ACTION_SEND).apply {
                                type = "text/plain"
                                putExtra(Intent.EXTRA_SUBJECT, "${studentGroup.studentName} — Writing Log")
                                putExtra(Intent.EXTRA_TEXT, textToExport)
                            }
                            context.startActivity(Intent.createChooser(shareIntent, "Share Student Document"))
                        },
                        colors = ButtonDefaults.buttonColors(
                            containerColor = MaterialTheme.colorScheme.primary
                        ),
                        shape = RoundedCornerShape(10.dp),
                        contentPadding = PaddingValues(horizontal = 12.dp, vertical = 8.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.Download,
                            contentDescription = null,
                            modifier = Modifier.size(15.dp)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("Export .txt", fontSize = 11.sp)
                    }
                }

                // Session Filter Chips if student has multiple saved exports
                if (studentGroup.sessions.size > 1) {
                    Spacer(modifier = Modifier.height(10.dp))
                    LazyRow(
                        horizontalArrangement = Arrangement.spacedBy(6.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        item {
                            val isSelected = selectedSessionId == "ALL"
                            Surface(
                                color = if (isSelected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.surfaceVariant,
                                shape = RoundedCornerShape(16.dp),
                                modifier = Modifier.clickable {
                                    selectedSessionId = "ALL"
                                    showingTranslation = false
                                }
                            ) {
                                Text(
                                    text = "All Combined (${studentGroup.sessions.size})",
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.SemiBold,
                                    color = if (isSelected) Color.White else MaterialTheme.colorScheme.onSurfaceVariant,
                                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 5.dp)
                                )
                            }
                        }
                        items(studentGroup.sessions) { sess ->
                            val isSelected = selectedSessionId == sess.id
                            Surface(
                                color = if (isSelected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.surfaceVariant,
                                shape = RoundedCornerShape(16.dp),
                                modifier = Modifier.clickable {
                                    selectedSessionId = sess.id
                                    showingTranslation = false
                                }
                            ) {
                                Text(
                                    text = timeFormat.format(Date(sess.created)),
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Medium,
                                    color = if (isSelected) Color.White else MaterialTheme.colorScheme.onSurfaceVariant,
                                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 5.dp)
                                )
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(10.dp))

                // Multi-language Google Translate Bar
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        LanguageDropdown(
                            selectedCode = selectedLanguage,
                            onLanguageSelected = { newLang ->
                                performTranslation(newLang)
                            },
                            enabled = !isTranslating
                        )

                        OutlinedButton(
                            onClick = {
                                if (showingTranslation) {
                                    showingTranslation = false
                                } else {
                                    performTranslation(selectedLanguage)
                                }
                            },
                            shape = RoundedCornerShape(10.dp),
                            enabled = !isTranslating,
                            contentPadding = PaddingValues(horizontal = 12.dp, vertical = 6.dp)
                        ) {
                            if (isTranslating) {
                                CircularProgressIndicator(
                                    modifier = Modifier.size(14.dp),
                                    strokeWidth = 2.dp,
                                    color = MaterialTheme.colorScheme.primary
                                )
                            } else {
                                Icon(
                                    imageVector = Icons.Default.GTranslate,
                                    contentDescription = null,
                                    modifier = Modifier.size(15.dp)
                                )
                                Spacer(modifier = Modifier.width(4.dp))
                                Text(
                                    text = if (showingTranslation) "Show Original" else "Translate",
                                    fontSize = 11.sp
                                )
                            }
                        }
                    }

                    if (showingTranslation && !translationFeedback.isNullOrEmpty()) {
                        Text(
                            text = translationFeedback!!,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Medium,
                            color = MaterialTheme.colorScheme.primary
                        )
                    }
                }

                translationError?.let { err ->
                    Spacer(modifier = Modifier.height(6.dp))
                    Surface(
                        modifier = Modifier.fillMaxWidth(),
                        color = MaterialTheme.colorScheme.error.copy(alpha = 0.1f),
                        shape = RoundedCornerShape(8.dp),
                        border = BorderStroke(1.dp, MaterialTheme.colorScheme.error.copy(alpha = 0.4f))
                    ) {
                        Text(
                            text = err,
                            modifier = Modifier.padding(8.dp),
                            fontSize = 12.sp,
                            color = MaterialTheme.colorScheme.error
                        )
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(14.dp))

        // Main Big Editorial Document Reader with Smart Conditional Formatting
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f),
            shape = RoundedCornerShape(16.dp),
            color = MaterialTheme.colorScheme.surface,
            border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
        ) {
            if (currentBlocks.isEmpty()) {
                Box(
                    modifier = Modifier.fillMaxSize().padding(24.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "No writing recorded in this session.",
                        fontSize = 15.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            } else {
                LazyColumn(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(22.dp),
                    verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    val numberedIndices = mutableMapOf<FormattedBlock, Int>()
                    var numCount = 0
                    for (b in currentBlocks) {
                        if (b.type == "title" || b.type == "heading" || b.type == "para") {
                            numCount = 0
                        } else if (b.type == "numbered") {
                            numCount++
                            numberedIndices[b] = numCount
                        }
                    }

                    items(currentBlocks) { block ->
                        when (block.type) {
                            "title" -> {
                                Column(modifier = Modifier.padding(bottom = 8.dp)) {
                                    Text(
                                        text = block.text,
                                        fontFamily = FontFamily.Serif,
                                        fontSize = 26.sp,
                                        lineHeight = 34.sp,
                                        fontWeight = FontWeight.Bold,
                                        color = MaterialTheme.colorScheme.onSurface
                                    )
                                    Spacer(modifier = Modifier.height(8.dp))
                                    Box(
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .height(2.5.dp)
                                            .background(Gold)
                                    )
                                }
                            }
                            "heading" -> {
                                val hSize = when (block.level) {
                                    1 -> 23.sp
                                    2 -> 21.sp
                                    else -> 19.sp
                                }
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    modifier = Modifier.padding(top = 6.dp)
                                ) {
                                    Box(
                                        modifier = Modifier
                                            .width(4.dp)
                                            .height(24.dp)
                                            .background(Gold, RoundedCornerShape(2.dp))
                                    )
                                    Spacer(modifier = Modifier.width(10.dp))
                                    Text(
                                        text = block.text,
                                        fontSize = hSize,
                                        lineHeight = 28.sp,
                                        fontWeight = FontWeight.Bold,
                                        fontFamily = FontFamily.Serif,
                                        color = MaterialTheme.colorScheme.primary
                                    )
                                }
                            }
                            "question" -> {
                                val qBlue = Color(0xFF4F8EF7)
                                Surface(
                                    modifier = Modifier.fillMaxWidth(),
                                    color = qBlue.copy(alpha = 0.10f),
                                    shape = RoundedCornerShape(12.dp),
                                    border = BorderStroke(1.5.dp, qBlue.copy(alpha = 0.65f))
                                ) {
                                    Column(modifier = Modifier.padding(14.dp)) {
                                        Text(
                                            text = "QUESTION",
                                            fontSize = 10.sp,
                                            fontFamily = FontFamily.Monospace,
                                            fontWeight = FontWeight.Bold,
                                            color = qBlue
                                        )
                                        Spacer(modifier = Modifier.height(4.dp))
                                        Text(
                                            text = block.text,
                                            fontSize = 20.sp,
                                            lineHeight = 30.sp,
                                            fontWeight = FontWeight.SemiBold,
                                            fontFamily = FontFamily.Serif,
                                            color = MaterialTheme.colorScheme.onSurface
                                        )
                                    }
                                }
                            }
                            "answer" -> {
                                Surface(
                                    modifier = Modifier.fillMaxWidth(),
                                    color = AccentGreen.copy(alpha = 0.10f),
                                    shape = RoundedCornerShape(12.dp),
                                    border = BorderStroke(1.5.dp, AccentGreen.copy(alpha = 0.65f))
                                ) {
                                    Column(modifier = Modifier.padding(14.dp)) {
                                        Text(
                                            text = "ANSWER",
                                            fontSize = 10.sp,
                                            fontFamily = FontFamily.Monospace,
                                            fontWeight = FontWeight.Bold,
                                            color = AccentGreen
                                        )
                                        Spacer(modifier = Modifier.height(4.dp))
                                        Text(
                                            text = block.text,
                                            fontSize = 20.sp,
                                            lineHeight = 30.sp,
                                            fontFamily = FontFamily.Serif,
                                            color = MaterialTheme.colorScheme.onSurface
                                        )
                                    }
                                }
                            }
                            "math" -> {
                                val tealAccent = Color(0xFF26A69A)
                                Surface(
                                    modifier = Modifier.fillMaxWidth(),
                                    color = tealAccent.copy(alpha = 0.10f),
                                    shape = RoundedCornerShape(12.dp),
                                    border = BorderStroke(1.5.dp, tealAccent.copy(alpha = 0.65f))
                                ) {
                                    Column(modifier = Modifier.padding(14.dp)) {
                                        Text(
                                            text = "MATH & CALCULATION",
                                            fontSize = 10.sp,
                                            fontFamily = FontFamily.Monospace,
                                            fontWeight = FontWeight.Bold,
                                            color = tealAccent
                                        )
                                        Spacer(modifier = Modifier.height(4.dp))
                                        Text(
                                            text = block.text,
                                            fontSize = 21.sp,
                                            lineHeight = 30.sp,
                                            fontWeight = FontWeight.Bold,
                                            fontFamily = FontFamily.Monospace,
                                            color = MaterialTheme.colorScheme.onSurface
                                        )
                                    }
                                }
                            }
                            "callout" -> {
                                Surface(
                                    modifier = Modifier.fillMaxWidth(),
                                    color = Gold.copy(alpha = 0.12f),
                                    shape = RoundedCornerShape(12.dp),
                                    border = BorderStroke(1.5.dp, Gold)
                                ) {
                                    Column(modifier = Modifier.padding(14.dp)) {
                                        Text(
                                            text = "KEY HIGHLIGHT",
                                            fontSize = 10.sp,
                                            fontFamily = FontFamily.Monospace,
                                            fontWeight = FontWeight.Bold,
                                            color = Gold
                                        )
                                        Spacer(modifier = Modifier.height(4.dp))
                                        Text(
                                            text = block.text,
                                            fontSize = 20.sp,
                                            lineHeight = 30.sp,
                                            fontWeight = FontWeight.Medium,
                                            fontFamily = FontFamily.Serif,
                                            color = MaterialTheme.colorScheme.onSurface
                                        )
                                    }
                                }
                            }
                            "bullet" -> {
                                Row(modifier = Modifier.padding(start = 8.dp)) {
                                    Text(
                                        text = "•  ",
                                        fontSize = 20.sp,
                                        fontWeight = FontWeight.Bold,
                                        color = MaterialTheme.colorScheme.primary
                                    )
                                    Text(
                                        text = block.text,
                                        fontSize = 20.sp,
                                        lineHeight = 30.sp,
                                        fontFamily = FontFamily.Serif,
                                        color = MaterialTheme.colorScheme.onSurface
                                    )
                                }
                            }
                            "numbered" -> {
                                val itemNum = numberedIndices[block] ?: 1
                                Row(modifier = Modifier.padding(start = 8.dp)) {
                                    Text(
                                        text = "$itemNum.  ",
                                        fontSize = 20.sp,
                                        fontWeight = FontWeight.Bold,
                                        color = MaterialTheme.colorScheme.primary
                                    )
                                    Text(
                                        text = block.text,
                                        fontSize = 20.sp,
                                        lineHeight = 30.sp,
                                        fontFamily = FontFamily.Serif,
                                        color = MaterialTheme.colorScheme.onSurface
                                    )
                                }
                            }
                            else -> {
                                Text(
                                    text = block.text,
                                    fontSize = 20.sp,
                                    lineHeight = 32.sp,
                                    fontFamily = FontFamily.Serif,
                                    color = MaterialTheme.colorScheme.onSurface
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}
