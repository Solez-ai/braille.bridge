package com.example.ui.exports

import android.content.Intent
import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Code
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.data.ExportEntity
import com.example.protocol.AutoFormatter
import com.example.protocol.BBTranslate
import com.example.protocol.FormattedBlock
import com.example.protocol.Translate
import com.example.ui.MainViewModel
import com.example.ui.components.LanguageDropdown
import com.example.ui.theme.Gold
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch

@Composable
fun ReviewScreen(
    export: ExportEntity,
    viewModel: MainViewModel,
    onBack: () -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    val originalBlocks = remember(export.id) {
        viewModel.parseBlocks(export.blocksJson)
    }

    var isRawMode by remember { mutableStateOf(false) }
    var selectedLanguage by remember { mutableStateOf("en") }
    var translatedBlocks by remember { mutableStateOf<List<FormattedBlock>?>(null) }
    var isTranslating by remember { mutableStateOf(false) }
    var showingTranslation by remember { mutableStateOf(false) }
    var translationFeedback by remember { mutableStateOf<String?>(null) }
    var translationError by remember { mutableStateOf<String?>(null) }
    var inFlightJob by remember { mutableStateOf<Job?>(null) }

    val translatedCache = remember { mutableMapOf<String, Pair<List<FormattedBlock>, String>>() }

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

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        // Toolbar: Back · Actions & Multi-language Translate Bar
        Surface(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(12.dp),
            color = MaterialTheme.colorScheme.surface,
            border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(10.dp)
            ) {
                // Top row: Back button, title, and raw/download actions
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        IconButton(onClick = onBack) {
                            Icon(
                                imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                                contentDescription = "Back",
                                tint = MaterialTheme.colorScheme.onSurface
                            )
                        }
                        Text(
                            text = "Document Review",
                            fontWeight = FontWeight.SemiBold,
                            fontSize = 14.sp,
                            color = MaterialTheme.colorScheme.onSurface
                        )
                    }

                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalAlignment = Alignment.CenterVertically) {
                        // Raw toggle button
                        OutlinedButton(
                            onClick = { isRawMode = !isRawMode },
                            shape = RoundedCornerShape(8.dp)
                        ) {
                            Icon(
                                imageVector = Icons.Default.Code,
                                contentDescription = null,
                                modifier = Modifier.size(15.dp)
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                            Text(if (isRawMode) "Formatted" else "Raw", fontSize = 11.sp)
                        }

                        // Download / Share button
                        Button(
                            onClick = {
                                val textToExport = AutoFormatter.toText(currentBlocks)
                                val shareIntent = Intent(Intent.ACTION_SEND).apply {
                                    type = "text/plain"
                                    putExtra(Intent.EXTRA_SUBJECT, export.title)
                                    putExtra(Intent.EXTRA_TEXT, textToExport)
                                }
                                context.startActivity(Intent.createChooser(shareIntent, "Download/Share Export"))
                            },
                            colors = ButtonDefaults.buttonColors(
                                containerColor = MaterialTheme.colorScheme.primary
                            ),
                            shape = RoundedCornerShape(8.dp)
                        ) {
                            Icon(
                                imageVector = Icons.Default.Download,
                                contentDescription = null,
                                modifier = Modifier.size(15.dp)
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                            Text(".txt", fontSize = 11.sp)
                        }
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))

                // Bottom row: Multi-language Google Translate Bar
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
                            shape = RoundedCornerShape(8.dp),
                            enabled = !isTranslating
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
                                    text = if (showingTranslation) "Original" else "Translate",
                                    fontSize = 11.sp
                                )
                            }
                        }
                    }

                    // Detected language feedback
                    if (showingTranslation && !translationFeedback.isNullOrEmpty()) {
                        Text(
                            text = translationFeedback!!,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Medium,
                            color = MaterialTheme.colorScheme.primary
                        )
                    }
                }

                // Inline error notice
                translationError?.let { err ->
                    Spacer(modifier = Modifier.height(6.dp))
                    Surface(
                        modifier = Modifier.fillMaxWidth(),
                        color = MaterialTheme.colorScheme.error.copy(alpha = 0.1f),
                        shape = RoundedCornerShape(8.dp),
                        border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.error.copy(alpha = 0.4f))
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

        // Main Document View Window
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f),
            shape = RoundedCornerShape(14.dp),
            color = MaterialTheme.colorScheme.surface,
            border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
        ) {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(currentBlocks) { block ->
                    if (isRawMode) {
                        // Monospace raw timestamped block
                        Row(modifier = Modifier.fillMaxWidth()) {
                            Text(
                                text = "[${AutoFormatter.formatTime(block.time)}] ",
                                fontFamily = FontFamily.Monospace,
                                fontSize = 11.sp,
                                color = MaterialTheme.colorScheme.primary,
                                fontWeight = FontWeight.Bold
                            )
                            Text(
                                text = block.text,
                                fontFamily = FontFamily.Monospace,
                                fontSize = 12.sp,
                                color = MaterialTheme.colorScheme.onSurface
                            )
                        }
                    } else {
                        // Formatted typography
                        when (block.type) {
                            "title" -> {
                                Column(modifier = Modifier.padding(bottom = 6.dp)) {
                                    Text(
                                        text = block.text,
                                        style = MaterialTheme.typography.headlineMedium.copy(
                                            fontSize = 22.sp,
                                            fontWeight = FontWeight.Bold
                                        ),
                                        color = MaterialTheme.colorScheme.onSurface
                                    )
                                    Spacer(modifier = Modifier.height(6.dp))
                                    // Gold rule under title
                                    Box(
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .height(2.dp)
                                            .background(Gold)
                                    )
                                }
                            }
                            "heading" -> {
                                val hSize = when (block.level) {
                                    1 -> 19.sp
                                    2 -> 17.sp
                                    3 -> 15.sp
                                    else -> 14.sp
                                }
                                Text(
                                    text = block.text,
                                    fontSize = hSize,
                                    fontWeight = FontWeight.Bold,
                                    fontFamily = FontFamily.Serif,
                                    color = MaterialTheme.colorScheme.primary,
                                    modifier = Modifier.padding(top = 6.dp)
                                )
                            }
                            "bullet" -> {
                                Row(modifier = Modifier.padding(start = 12.dp)) {
                                    Text(
                                        text = "• ",
                                        fontWeight = FontWeight.Bold,
                                        color = MaterialTheme.colorScheme.primary
                                    )
                                    Text(
                                        text = block.text,
                                        fontSize = 14.sp,
                                        lineHeight = 20.sp,
                                        fontFamily = FontFamily.Serif,
                                        color = MaterialTheme.colorScheme.onSurface
                                    )
                                }
                            }
                            "numbered" -> {
                                Row(modifier = Modifier.padding(start = 12.dp)) {
                                    Text(
                                        text = "· ",
                                        fontWeight = FontWeight.Bold,
                                        color = MaterialTheme.colorScheme.primary
                                    )
                                    Text(
                                        text = block.text,
                                        fontSize = 14.sp,
                                        lineHeight = 20.sp,
                                        fontFamily = FontFamily.Serif,
                                        color = MaterialTheme.colorScheme.onSurface
                                    )
                                }
                            }
                            else -> {
                                Text(
                                    text = block.text,
                                    fontSize = 14.sp,
                                    lineHeight = 22.sp,
                                    fontFamily = FontFamily.Serif,
                                    color = MaterialTheme.colorScheme.onSurface
                                )
                            }
                        }
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(10.dp))

        // Footer: title · char count · formatted block count
        Surface(
            modifier = Modifier.fillMaxWidth(),
            color = MaterialTheme.colorScheme.surfaceVariant,
            shape = RoundedCornerShape(8.dp)
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 12.dp, vertical = 6.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = export.title,
                    fontWeight = FontWeight.SemiBold,
                    fontSize = 11.sp,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Text(
                    text = "${export.charsCount} characters · ${currentBlocks.size} blocks",
                    fontSize = 11.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}
