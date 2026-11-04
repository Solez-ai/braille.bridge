package com.example.ui.student

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.animateContentSize
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Backspace
import androidx.compose.material.icons.automirrored.filled.VolumeOff
import androidx.compose.material.icons.automirrored.filled.VolumeUp
import androidx.compose.material.icons.filled.Bluetooth
import androidx.compose.material.icons.filled.BluetoothConnected
import androidx.compose.material.icons.filled.Clear
import androidx.compose.material.icons.filled.ExpandLess
import androidx.compose.material.icons.filled.ExpandMore
import androidx.compose.material.icons.filled.GTranslate
import androidx.compose.material.icons.filled.KeyboardReturn
import androidx.compose.material.icons.filled.ScreenShare
import androidx.compose.material.icons.filled.SpaceBar
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults

import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import com.example.protocol.BrailleDict
import com.example.protocol.TimedChar
import com.example.ui.MainViewModel
import com.example.ui.components.LanguageDropdown
import com.example.ui.theme.AccentGreen
import com.example.ui.theme.AccentRed
import com.example.ui.theme.Gold
import com.example.ui.theme.GoldDark
import com.example.ui.theme.GoldLight
import com.example.ui.theme.TextMuted

@Composable
fun StudentScreen(
    viewModel: MainViewModel,
    modifier: Modifier = Modifier
) {
    val pressedDots by viewModel.studentPressedDots.collectAsState()
    val chord by viewModel.studentChord.collectAsState()
    val isBangla by viewModel.isBangla.collectAsState()
    val shiftActive by viewModel.shiftActive.collectAsState()
    val chars by viewModel.studentChars.collectAsState()
    val recentChars by viewModel.studentRecentChars.collectAsState()
    val isTranslating by viewModel.isStudentTranslating.collectAsState()
    val translateResult by viewModel.studentTranslateResult.collectAsState()
    val translateTarget by viewModel.studentTranslateTarget.collectAsState()
    val translateError by viewModel.studentTranslateError.collectAsState()
    val isConnected by viewModel.isStudentDeviceConnected.collectAsState()
    val debugLog by viewModel.debugLog.collectAsState()
    val isAudioEnabled by viewModel.isAudioFeedbackEnabled.collectAsState()
    val capsMode by viewModel.capsMode.collectAsState()

    val currentText = remember(chars) { chars.joinToString("") { it.char } }
    val resolvedChar = remember(chord, isBangla, shiftActive, capsMode) {
        if (chord == 0b100000 && !shiftActive && !isBangla) "⇪"
        else BrailleDict.resolveChord(chord, isBangla, shiftActive, capsMode)
    }

    // Inner text-area scroll (auto-follows the caret) + diagnostics scroll
    val textScrollState = rememberScrollState()
    val debugScrollState = rememberScrollState()
    var showDiagnostics by remember { mutableStateOf(false) }

    LaunchedEffect(currentText) {
        textScrollState.animateScrollTo(textScrollState.maxValue)
    }
    LaunchedEffect(debugLog.size, showDiagnostics) {
        if (showDiagnostics) debugScrollState.animateScrollTo(debugScrollState.maxValue)
    }

    val screenScrollState = rememberScrollState()
    var isOutputExpanded by remember { mutableStateOf(true) }

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(screenScrollState)
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // ── Top status row: connection badge + mode LEDs ──────────────────────
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Surface(
                color = if (isConnected) AccentGreen.copy(alpha = 0.15f)
                else MaterialTheme.colorScheme.surfaceVariant,
                shape = RoundedCornerShape(16.dp),
                border = BorderStroke(1.dp, Color(0xFFD6D1C7)),
                modifier = Modifier
                    .weight(1f, fill = false)
                    .clickable { viewModel.showBleScanDialog.value = true }
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = if (isConnected) Icons.Default.BluetoothConnected else Icons.Default.Bluetooth,
                        contentDescription = null,
                        tint = if (isConnected) AccentGreen else MaterialTheme.colorScheme.primary,
                        modifier = Modifier.size(16.dp)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = if (isConnected) "Connected" else "Connect BLE",
                        style = MaterialTheme.typography.labelMedium,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        color = if (isConnected) AccentGreen else MaterialTheme.colorScheme.onSurface
                    )
                }
            }

            Spacer(modifier = Modifier.width(8.dp))

            // Audio feedback toggle + Language & Shift & Caps LEDs
            Row(
                horizontalArrangement = Arrangement.spacedBy(6.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Audio Feedback toggle
                Surface(
                    color = if (isAudioEnabled) AccentGreen.copy(alpha = 0.15f) else MaterialTheme.colorScheme.surfaceVariant,
                    shape = RoundedCornerShape(12.dp),
                    border = BorderStroke(1.dp, Color(0xFFD6D1C7)),
                    modifier = Modifier.clickable { viewModel.toggleAudioFeedback() }
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 6.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            imageVector = if (isAudioEnabled) Icons.AutoMirrored.Filled.VolumeUp else Icons.AutoMirrored.Filled.VolumeOff,
                            contentDescription = "Toggle Speech Feedback",
                            tint = if (isAudioEnabled) AccentGreen else TextMuted,
                            modifier = Modifier.size(16.dp)
                        )
                    }
                }

                // Language LED
                Surface(
                    color = if (isBangla) AccentGreen.copy(alpha = 0.2f) else AccentRed.copy(alpha = 0.2f),
                    shape = RoundedCornerShape(12.dp),
                    border = BorderStroke(1.dp, Color(0xFFD6D1C7)),
                    modifier = Modifier.clickable { viewModel.toggleLanguage() }
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 6.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Box(
                            modifier = Modifier
                                .size(8.dp)
                                .clip(CircleShape)
                                .background(if (isBangla) AccentGreen else AccentRed)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text(
                            text = if (isBangla) "বাংলা" else "EN",
                            style = MaterialTheme.typography.labelMedium,
                            color = if (isBangla) AccentGreen else AccentRed
                        )
                    }
                }

                // Caps Indicator LED (visible or highlighted when active)
                if (capsMode != BrailleDict.CapsMode.OFF) {
                    Surface(
                        color = Gold.copy(alpha = 0.25f),
                        shape = RoundedCornerShape(12.dp),
                        border = BorderStroke(1.dp, Gold),
                        modifier = Modifier.clickable {
                            viewModel.capsMode.value = BrailleDict.CapsMode.OFF
                        }
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 6.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Box(
                                modifier = Modifier
                                    .size(8.dp)
                                    .clip(CircleShape)
                                    .background(Gold)
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                            Text(
                                text = if (capsMode == BrailleDict.CapsMode.LOCK) "CAPS" else "CAP",
                                style = MaterialTheme.typography.labelMedium,
                                color = Gold
                            )
                        }
                    }
                }

                // Shift LED
                Surface(
                    color = if (shiftActive) Gold.copy(alpha = 0.25f) else MaterialTheme.colorScheme.surfaceVariant,
                    shape = RoundedCornerShape(12.dp),
                    border = BorderStroke(1.dp, Color(0xFFD6D1C7)),
                    modifier = Modifier.clickable { viewModel.toggleShift() }
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 6.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Box(
                            modifier = Modifier
                                .size(8.dp)
                                .clip(CircleShape)
                                .background(if (shiftActive) Gold else TextMuted)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text(
                            text = "Shift",
                            style = MaterialTheme.typography.labelMedium,
                            color = if (shiftActive) Gold else TextMuted
                        )
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        // ── Live Output card — expandable without fixed height clipping ──────
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .animateContentSize(),
            shape = RoundedCornerShape(14.dp),
            color = MaterialTheme.colorScheme.surface,
            border = BorderStroke(1.dp, Color(0xFFD0CCC4))
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "LIVE OUTPUT",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.primary
                    )
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            text = "${chars.size} chars",
                            style = MaterialTheme.typography.labelSmall,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        IconButton(
                            onClick = { isOutputExpanded = !isOutputExpanded },
                            modifier = Modifier.size(32.dp)
                        ) {
                            Icon(
                                imageVector = if (isOutputExpanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore,
                                contentDescription = if (isOutputExpanded) "Collapse output" else "Expand output",
                                tint = MaterialTheme.colorScheme.onSurfaceVariant,
                                modifier = Modifier.size(18.dp)
                            )
                        }
                    }
                }

                if (isOutputExpanded) {
                    HorizontalDivider(
                        modifier = Modifier.padding(vertical = 12.dp),
                        color = MaterialTheme.colorScheme.outlineVariant
                    )

                    // The text area itself — wraps, scrolls, auto-follows caret
                    Surface(
                        modifier = Modifier
                            .fillMaxWidth()
                            .heightIn(min = 90.dp, max = 220.dp),
                        shape = RoundedCornerShape(10.dp),
                        color = MaterialTheme.colorScheme.surfaceVariant,
                        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
                    ) {
                        if (currentText.isEmpty()) {
                            Box(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height(90.dp)
                                    .padding(12.dp),
                                contentAlignment = Alignment.Center
                            ) {
                                Text(
                                    text = "No output yet. Start typing...",
                                    style = MaterialTheme.typography.bodyMedium,
                                    textAlign = TextAlign.Center,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        } else {
                            Column(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .verticalScroll(textScrollState)
                                    .padding(12.dp)
                            ) {
                                val caretColor = MaterialTheme.colorScheme.primary
                                val caretAlpha by rememberInfiniteTransition(label = "caret").animateFloat(
                                    initialValue = 0.15f,
                                    targetValue = 1f,
                                    animationSpec = infiniteRepeatable(
                                        animation = tween(500, easing = FastOutSlowInEasing),
                                        repeatMode = RepeatMode.Reverse
                                    ),
                                    label = "caret_alpha"
                                )
                                Text(
                                    text = buildAnnotatedString {
                                        append(currentText)
                                        withStyle(SpanStyle(background = caretColor.copy(alpha = caretAlpha))) {
                                            append("▏")
                                        }
                                    },
                                    style = MaterialTheme.typography.titleMedium.copy(
                                        fontFamily = FontFamily.Serif
                                    ),
                                    color = MaterialTheme.colorScheme.onSurface
                                )
                            }
                        }
                    }

                    // Google Translate bar (only when there is content)
                    AnimatedVisibility(visible = currentText.isNotBlank()) {
                        Column(modifier = Modifier.padding(top = 10.dp)) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                LanguageDropdown(
                                    selectedCode = translateTarget,
                                    onLanguageSelected = { newCode ->
                                        viewModel.setStudentTranslateTarget(newCode)
                                    },
                                    enabled = !isTranslating
                                )

                                OutlinedButton(
                                    onClick = { viewModel.translateStudentStream() },
                                    shape = RoundedCornerShape(8.dp),
                                    enabled = !isTranslating,
                                    contentPadding = PaddingValues(horizontal = 12.dp, vertical = 6.dp)
                                ) {
                                    Icon(
                                        imageVector = Icons.Default.GTranslate,
                                        contentDescription = null,
                                        modifier = Modifier.size(16.dp)
                                    )
                                    Spacer(modifier = Modifier.width(6.dp))
                                    Text(text = "Translate", style = MaterialTheme.typography.labelLarge)
                                }
                            }

                            translateResult?.let { tr ->
                                if (tr.feedback.isNotEmpty()) {
                                    Spacer(modifier = Modifier.height(6.dp))
                                    Text(
                                        text = tr.feedback,
                                        style = MaterialTheme.typography.labelMedium,
                                        maxLines = 2,
                                        overflow = TextOverflow.Ellipsis,
                                        color = MaterialTheme.colorScheme.primary,
                                        modifier = Modifier.padding(horizontal = 2.dp)
                                    )
                                }
                                Spacer(modifier = Modifier.height(4.dp))
                                Surface(
                                    modifier = Modifier.fillMaxWidth(),
                                    color = MaterialTheme.colorScheme.primary.copy(alpha = 0.08f),
                                    shape = RoundedCornerShape(8.dp),
                                    border = BorderStroke(1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.3f))
                                ) {
                                    Text(
                                        text = tr.text,
                                        modifier = Modifier.padding(10.dp),
                                        style = MaterialTheme.typography.bodyLarge.copy(fontFamily = FontFamily.Serif),
                                        color = MaterialTheme.colorScheme.onSurface
                                    )
                                }
                            }

                            translateError?.let { err ->
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
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.error
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        // ── Recent characters strip ───────────────────────────────────────────
        Surface(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(10.dp),
            color = MaterialTheme.colorScheme.surface,
            border = BorderStroke(1.dp, Color(0xFFD0CCC4))
        ) {
            Column(modifier = Modifier.padding(10.dp)) {
                Text(
                    text = "RECENT CHARACTERS",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(4.dp))
                if (recentChars.isEmpty()) {
                    Text(
                        text = "—",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                } else {
                    val listState = rememberLazyListState()
                    LaunchedEffect(recentChars.size) {
                        if (recentChars.isNotEmpty()) listState.animateScrollToItem(recentChars.size - 1)
                    }
                    LazyRow(
                        state = listState,
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(4.dp)
                    ) {
                        items(recentChars) { ch ->
                            Surface(
                                color = MaterialTheme.colorScheme.surfaceVariant,
                                shape = RoundedCornerShape(4.dp)
                            ) {
                                Text(
                                    text = if (ch.char == " ") "␣" else ch.char,
                                    style = MaterialTheme.typography.bodyLarge.copy(fontFamily = FontFamily.Serif),
                                    modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                                    color = if (ch.char == " ") MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface
                                )
                            }
                        }
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        // ── 6-dot braille cell ────────────────────────────────────────────────
        Surface(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
            color = MaterialTheme.colorScheme.surface,
            border = BorderStroke(1.dp, Color(0xFFD0CCC4))
        ) {
            Column(
                modifier = Modifier.padding(16.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = if (pressedDots.isEmpty()) "Pattern: None" else "Pattern: Dots ${pressedDots.sorted().joinToString(",")}",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.primary
                    )
                    Row(
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "→ ",
                            style = MaterialTheme.typography.titleMedium,
                            color = if (resolvedChar != null) MaterialTheme.colorScheme.primary else TextMuted
                        )
                        Text(
                            text = resolvedChar ?: "—",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = if (resolvedChar != null) MaterialTheme.colorScheme.primary else TextMuted
                        )
                    }
                }

                Spacer(modifier = Modifier.height(14.dp))

                Row(
                    horizontalArrangement = Arrangement.spacedBy(36.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                        BrailleDotButton(dotIndex = 1, isPressed = pressedDots.contains(1)) { viewModel.toggleDot(1) }
                        BrailleDotButton(dotIndex = 2, isPressed = pressedDots.contains(2)) { viewModel.toggleDot(2) }
                        BrailleDotButton(dotIndex = 3, isPressed = pressedDots.contains(3)) { viewModel.toggleDot(3) }
                    }
                    Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                        BrailleDotButton(dotIndex = 4, isPressed = pressedDots.contains(4)) { viewModel.toggleDot(4) }
                        BrailleDotButton(dotIndex = 5, isPressed = pressedDots.contains(5)) { viewModel.toggleDot(5) }
                        BrailleDotButton(dotIndex = 6, isPressed = pressedDots.contains(6)) { viewModel.toggleDot(6) }
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Button(
                        onClick = { viewModel.commitChord() },
                        enabled = chord > 0,
                        colors = ButtonDefaults.buttonColors(
                            containerColor = MaterialTheme.colorScheme.primary
                        ),
                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 8.dp),
                        shape = RoundedCornerShape(10.dp),
                        modifier = Modifier
                            .weight(1f)
                            .height(44.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.KeyboardReturn,
                            contentDescription = null,
                            modifier = Modifier.size(16.dp)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("Commit", maxLines = 1, fontSize = 13.sp, overflow = TextOverflow.Ellipsis)
                    }

                    OutlinedButton(
                        onClick = { viewModel.addSpace() },
                        shape = RoundedCornerShape(10.dp),
                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 8.dp),
                        modifier = Modifier
                            .weight(1f)
                            .height(44.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.SpaceBar,
                            contentDescription = null,
                            modifier = Modifier.size(16.dp)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("Space", maxLines = 1, fontSize = 13.sp, overflow = TextOverflow.Ellipsis)
                    }

                    OutlinedButton(
                        onClick = { viewModel.handleBackspace() },
                        shape = RoundedCornerShape(10.dp),
                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 8.dp),
                        modifier = Modifier
                            .weight(1f)
                            .height(44.dp)
                    ) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.Backspace,
                            contentDescription = "Backspace",
                            modifier = Modifier.size(16.dp)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("Backspace", maxLines = 1, fontSize = 13.sp, overflow = TextOverflow.Ellipsis)
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        // ── Lower toolbar ─────────────────────────────────────────────────────
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            OutlinedButton(
                onClick = { viewModel.clearStudentStream() },
                shape = RoundedCornerShape(10.dp),
                modifier = Modifier
                    .weight(1f)
                    .height(48.dp)
            ) {
                Icon(
                    imageVector = Icons.Default.Clear,
                    contentDescription = null,
                    modifier = Modifier.size(18.dp)
                )
                Spacer(modifier = Modifier.width(6.dp))
                Text("Clear", style = MaterialTheme.typography.labelLarge, maxLines = 1)
            }

            Button(
                onClick = { viewModel.sendModalOpen.value = true },
                shape = RoundedCornerShape(10.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFFB58D3D),
                    contentColor = Color.White
                ),
                modifier = Modifier
                    .weight(1.4f)
                    .height(48.dp)
            ) {
                Icon(
                    imageVector = Icons.Default.ScreenShare,
                    contentDescription = null,
                    tint = Color.White,
                    modifier = Modifier.size(18.dp)
                )
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    "Send to Teacher",
                    style = MaterialTheme.typography.labelLarge,
                    color = Color.White,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
            }
        }
    }
}

@Composable
private fun BrailleDotButton(
    dotIndex: Int,
    isPressed: Boolean,
    onClick: () -> Unit
) {
    val bgBrush = if (isPressed) {
        Brush.linearGradient(colors = listOf(GoldLight, GoldDark))
    } else {
        Brush.linearGradient(
            colors = listOf(
                MaterialTheme.colorScheme.surfaceVariant,
                MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.7f)
            )
        )
    }

    Box(
        modifier = Modifier
            .size(56.dp)
            .clip(CircleShape)
            .background(bgBrush)
            .border(
                width = if (isPressed) 2.dp else 1.dp,
                color = if (isPressed) Gold else MaterialTheme.colorScheme.outlineVariant,
                shape = CircleShape
            )
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = dotIndex.toString(),
            style = MaterialTheme.typography.titleMedium,
            color = if (isPressed) Color.White else MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}
