package com.example.ui.student

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
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
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Backspace
import androidx.compose.material.icons.filled.Bluetooth
import androidx.compose.material.icons.filled.BluetoothConnected
import androidx.compose.material.icons.filled.Clear
import androidx.compose.material.icons.filled.GTranslate
import androidx.compose.material.icons.filled.Language
import androidx.compose.material.icons.filled.KeyboardReturn
import androidx.compose.material.icons.filled.ScreenShare
import androidx.compose.material.icons.filled.SpaceBar
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
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import com.example.ui.components.LanguageDropdown
import androidx.compose.ui.unit.sp
import com.example.protocol.BrailleDict
import com.example.protocol.TimedChar
import com.example.ui.MainViewModel
import com.example.ui.theme.AccentBlue
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
    val connectedAddress by viewModel.activeStudentDeviceAddress.collectAsState()

    val currentText = remember(chars) { chars.joinToString("") { it.char } }
    val resolvedChar = remember(chord, isBangla, shiftActive) {
        BrailleDict.resolveChord(chord, isBangla, shiftActive)
    }

    // Outer page scroll + inner text-area scroll (each needs its own state)
    val pageScrollState = rememberScrollState()
    val textScrollState = rememberScrollState()

    // Auto-follow the caret as new characters stream in
    LaunchedEffect(currentText) {
        textScrollState.animateScrollTo(textScrollState.maxValue)
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(pageScrollState)
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Top status row: Connection status + Mode LED indicators
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            // BLE connection badge
            Surface(
                color = if (isConnected) AccentGreen.copy(alpha = 0.15f)
                else MaterialTheme.colorScheme.surfaceVariant,
                shape = RoundedCornerShape(16.dp),
                modifier = Modifier.clickable { viewModel.showBleScanDialog.value = true }
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = if (isConnected) Icons.Default.BluetoothConnected else Icons.Default.Bluetooth,
                        contentDescription = "Bluetooth",
                        tint = if (isConnected) AccentGreen else MaterialTheme.colorScheme.primary,
                        modifier = Modifier.size(16.dp)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = if (isConnected) "BrailleBridge Connected" else "Connect BLE Device",
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Medium,
                        color = if (isConnected) AccentGreen else MaterialTheme.colorScheme.onSurface
                    )
                }
            }

            // Language & Shift LEDs
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                // English / বাংলা LED
                Surface(
                    color = if (isBangla) AccentGreen.copy(alpha = 0.2f) else AccentRed.copy(alpha = 0.2f),
                    shape = RoundedCornerShape(12.dp),
                    modifier = Modifier.clickable { viewModel.toggleLanguage() }
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Box(
                            modifier = Modifier
                                .size(8.dp)
                                .clip(CircleShape)
                                .background(if (isBangla) AccentGreen else AccentRed)
                        )
                        Spacer(modifier = Modifier.width(5.dp))
                        Text(
                            text = if (isBangla) "বাংলা (BN)" else "English (EN)",
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold,
                            color = if (isBangla) AccentGreen else AccentRed
                        )
                    }
                }

                // Shift LED
                Surface(
                    color = if (shiftActive) Gold.copy(alpha = 0.25f) else MaterialTheme.colorScheme.surfaceVariant,
                    shape = RoundedCornerShape(12.dp),
                    modifier = Modifier.clickable { viewModel.toggleShift() }
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Box(
                            modifier = Modifier
                                .size(8.dp)
                                .clip(CircleShape)
                                .background(if (shiftActive) Gold else TextMuted)
                        )
                        Spacer(modifier = Modifier.width(5.dp))
                        Text(
                            text = "Shift",
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold,
                            color = if (shiftActive) Gold else TextMuted
                        )
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Live Output Display Card
        Surface(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(14.dp),
            color = MaterialTheme.colorScheme.surface,
            border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "LIVE OUTPUT",
                        fontSize = 12.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary
                    )
                    Text(
                        text = "${chars.size} chars",
                        fontSize = 12.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }

                Spacer(modifier = Modifier.height(10.dp))

                // Live output — a real text area: wrapping, scrolling, auto-follow caret
                Surface(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(190.dp),
                    shape = RoundedCornerShape(10.dp),
                    color = MaterialTheme.colorScheme.surfaceVariant,
                    border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
                ) {
                    if (currentText.isEmpty()) {
                        Box(modifier = Modifier.fillMaxSize()) {
                            Text(
                                text = "Waiting for input — type chords on the BrailleBridge or tap the dots below…",
                                modifier = Modifier.align(Alignment.Center),
                                fontSize = 15.sp,
                                lineHeight = 22.sp,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    } else {
                        Column(
                            modifier = Modifier
                                .fillMaxSize()
                                .verticalScroll(textScrollState)
                                .padding(14.dp)
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
                                fontFamily = FontFamily.Serif,
                                fontSize = 20.sp,
                                lineHeight = 28.sp,
                                color = MaterialTheme.colorScheme.onSurface
                            )
                        }
                    }
                }

                // Google Translate Bar (appears whenever stream has content)
                AnimatedVisibility(visible = currentText.isNotBlank()) {
                    Column(modifier = Modifier.padding(top = 10.dp)) {
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
                                    selectedCode = translateTarget,
                                    onLanguageSelected = { newCode ->
                                        viewModel.setStudentTranslateTarget(newCode)
                                    },
                                    enabled = !isTranslating
                                )

                                OutlinedButton(
                                    onClick = { viewModel.translateStudentStream() },
                                    shape = RoundedCornerShape(8.dp),
                                    enabled = !isTranslating
                                ) {
                                    Icon(
                                        imageVector = Icons.Default.GTranslate,
                                        contentDescription = "Translate",
                                        modifier = Modifier.size(16.dp)
                                    )
                                    Spacer(modifier = Modifier.width(6.dp))
                                    Text(
                                        text = if (translateResult == null) "Translate" else "Translate",
                                        fontSize = 13.sp
                                    )
                                }
                            }

                            if (isTranslating) {
                                CircularProgressIndicator(
                                    modifier = Modifier.size(18.dp),
                                    strokeWidth = 2.dp,
                                    color = MaterialTheme.colorScheme.primary
                                )
                            }
                        }

                        // Detected language feedback
                        translateResult?.let { tr ->
                            if (tr.feedback.isNotEmpty()) {
                                Spacer(modifier = Modifier.height(6.dp))
                                Text(
                                    text = tr.feedback,
                                    fontSize = 13.sp,
                                    fontWeight = FontWeight.SemiBold,
                                    color = MaterialTheme.colorScheme.primary,
                                    modifier = Modifier.padding(horizontal = 2.dp)
                                )
                            }
                            Spacer(modifier = Modifier.height(4.dp))
                            Surface(
                                modifier = Modifier.fillMaxWidth(),
                                color = MaterialTheme.colorScheme.primary.copy(alpha = 0.08f),
                                shape = RoundedCornerShape(8.dp),
                                border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.3f))
                            ) {
                                Text(
                                    text = tr.text,
                                    modifier = Modifier.padding(10.dp),
                                    fontSize = 14.sp,
                                    fontFamily = FontFamily.Serif,
                                    color = MaterialTheme.colorScheme.onSurface
                                )
                            }
                        }

                        // Inline error message
                        translateError?.let { err ->
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
                                    fontSize = 13.sp,
                                    color = MaterialTheme.colorScheme.error
                                )
                            }
                        }
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        // Recent Characters Strip (rolling 80-char window)
        Surface(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(10.dp),
            color = MaterialTheme.colorScheme.surface
        ) {
            Column(modifier = Modifier.padding(8.dp)) {
                Text(
                    text = "RECENT CHARACTERS",
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(4.dp))
                if (recentChars.isEmpty()) {
                    Text(
                        text = "—",
                        fontSize = 13.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                } else {
                    LazyRow(
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
                                    fontFamily = FontFamily.Serif,
                                    fontSize = 15.sp,
                                    modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                                    color = if (ch.char == " ") MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface
                                )
                            }
                        }
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // 6-Dot Clickable Braille Cell
        // Layout: 2 columns x 3 rows
        // Left Column: Dot 1 (top), Dot 2 (mid), Dot 3 (bottom)
        // Right Column: Dot 4 (top), Dot 5 (mid), Dot 6 (bottom)
        Surface(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
            color = MaterialTheme.colorScheme.surface,
            border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
        ) {
            Column(
                modifier = Modifier.padding(16.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // Chord readout & mapping line
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "0b${chord.toString(2).padStart(6, '0')}",
                        fontFamily = FontFamily.Monospace,
                        fontSize = 13.sp,
                        color = MaterialTheme.colorScheme.primary,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = if (pressedDots.isEmpty()) "No dots active" else "Dots: ${pressedDots.sorted().joinToString(", ")}",
                        fontSize = 13.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Text(
                        text = "→ ${resolvedChar ?: "—"}",
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold,
                        color = if (resolvedChar != null) MaterialTheme.colorScheme.primary else TextMuted
                    )
                }

                Spacer(modifier = Modifier.height(14.dp))

                // The 6-dot cell
                Row(
                    horizontalArrangement = Arrangement.spacedBy(44.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    // Left Column (Dots 1, 2, 3)
                    Column(verticalArrangement = Arrangement.spacedBy(20.dp)) {
                        BrailleDotButton(dotIndex = 1, isPressed = pressedDots.contains(1)) {
                            viewModel.toggleDot(1)
                        }
                        BrailleDotButton(dotIndex = 2, isPressed = pressedDots.contains(2)) {
                            viewModel.toggleDot(2)
                        }
                        BrailleDotButton(dotIndex = 3, isPressed = pressedDots.contains(3)) {
                            viewModel.toggleDot(3)
                        }
                    }

                    // Right Column (Dots 4, 5, 6)
                    Column(verticalArrangement = Arrangement.spacedBy(20.dp)) {
                        BrailleDotButton(dotIndex = 4, isPressed = pressedDots.contains(4)) {
                            viewModel.toggleDot(4)
                        }
                        BrailleDotButton(dotIndex = 5, isPressed = pressedDots.contains(5)) {
                            viewModel.toggleDot(5)
                        }
                        BrailleDotButton(dotIndex = 6, isPressed = pressedDots.contains(6)) {
                            viewModel.toggleDot(6)
                        }
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Cell control bar: Commit, Space, Backspace
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
                        shape = RoundedCornerShape(10.dp),
                        modifier = Modifier.weight(1.2f)
                    ) {
                        Icon(
                            imageVector = Icons.Default.KeyboardReturn,
                            contentDescription = "Commit",
                            modifier = Modifier.size(18.dp)
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("Commit", fontSize = 14.sp)
                    }

                    OutlinedButton(
                        onClick = { viewModel.addSpace() },
                        shape = RoundedCornerShape(10.dp),
                        modifier = Modifier.weight(1f)
                    ) {
                        Icon(
                            imageVector = Icons.Default.SpaceBar,
                            contentDescription = "Space",
                            modifier = Modifier.size(18.dp)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("Space", fontSize = 14.sp)
                    }

                    OutlinedButton(
                        onClick = { viewModel.handleBackspace() },
                        shape = RoundedCornerShape(10.dp),
                        modifier = Modifier.weight(1f)
                    ) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.Backspace,
                            contentDescription = "Backspace",
                            modifier = Modifier.size(18.dp)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("Bksp", fontSize = 14.sp)
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Lower action toolbar: Clear, Send to Teacher, Connect
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            OutlinedButton(
                onClick = { viewModel.clearStudentStream() },
                shape = RoundedCornerShape(10.dp),
                modifier = Modifier.weight(1f)
            ) {
                Icon(
                    imageVector = Icons.Default.Clear,
                    contentDescription = "Clear",
                    modifier = Modifier.size(18.dp)
                )
                Spacer(modifier = Modifier.width(6.dp))
                Text("Clear", fontSize = 14.sp)
            }

            Button(
                onClick = { viewModel.sendModalOpen.value = true },
                shape = RoundedCornerShape(10.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant,
                    contentColor = MaterialTheme.colorScheme.onSurface
                ),
                modifier = Modifier.weight(1.2f)
            ) {
                Icon(
                    imageVector = Icons.Default.ScreenShare,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.size(18.dp)
                )
                Spacer(modifier = Modifier.width(6.dp))
                Text("Send to Teacher", fontSize = 14.sp)
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
    // Replicates 145deg gradient with hard drop-shadow from style.css
    val bgBrush = if (isPressed) {
        Brush.linearGradient(
            colors = listOf(GoldLight, GoldDark)
        )
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
            .size(64.dp)
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
            fontWeight = FontWeight.Bold,
            fontSize = 18.sp,
            color = if (isPressed) Color.White else MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}


