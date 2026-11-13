package com.example.ui.learn

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
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
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
import androidx.compose.material.icons.automirrored.filled.RotateLeft
import androidx.compose.material.icons.automirrored.filled.VolumeOff
import androidx.compose.material.icons.automirrored.filled.VolumeUp
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.Bluetooth
import androidx.compose.material.icons.filled.BluetoothConnected
import androidx.compose.material.icons.filled.Clear
import androidx.compose.material.icons.filled.Download
import androidx.compose.material.icons.filled.KeyboardReturn
import androidx.compose.material.icons.filled.SpaceBar
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.protocol.DecodedStep
import com.example.ui.MainViewModel
import com.example.ui.theme.AccentBlue
import com.example.ui.theme.AccentGreen
import com.example.ui.theme.AccentRed
import com.example.ui.theme.Gold
import com.example.ui.theme.GoldDark
import com.example.ui.theme.GoldLight
import com.example.ui.theme.TextMuted

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun LearnScreen(
    viewModel: MainViewModel,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val isBangla by viewModel.learnerLangIsBangla.collectAsState()
    val inputText by viewModel.learnerInputText.collectAsState()
    val spokenWords by viewModel.learnerSpokenWords.collectAsState()
    val decoderInput by viewModel.learnerDecoderInput.collectAsState()
    val decoderIsBangla by viewModel.learnerDecoderIsBangla.collectAsState()
    val decodedSteps by viewModel.learnerDecodedSteps.collectAsState()
    val isConnected by viewModel.isStudentDeviceConnected.collectAsState()
    val isAudioEnabled by viewModel.isAudioFeedbackEnabled.collectAsState()

    val ttsReady by viewModel.ttsManager.isTtsReady.collectAsState()
    val banglaAvailable by viewModel.ttsManager.isBanglaAvailable.collectAsState()

    val scrollState = rememberScrollState()
    var selectedLearnTab by remember { mutableStateOf(0) }

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(scrollState)
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Dedicated sub-tab selector to avoid vertically stacking and peeking cards
        Surface(
            color = MaterialTheme.colorScheme.surfaceVariant,
            shape = RoundedCornerShape(50),
            border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
            modifier = Modifier.fillMaxWidth()
        ) {
            Row(
                modifier = Modifier.padding(4.dp),
                horizontalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                Surface(
                    color = if (selectedLearnTab == 0) MaterialTheme.colorScheme.primary else Color.Transparent,
                    shape = RoundedCornerShape(50),
                    modifier = Modifier
                        .weight(1f)
                        .clickable { selectedLearnTab = 0 }
                ) {
                    Text(
                        text = "Freeplay Playground",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.SemiBold,
                        textAlign = TextAlign.Center,
                        color = if (selectedLearnTab == 0) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.padding(vertical = 8.dp)
                    )
                }
                Surface(
                    color = if (selectedLearnTab == 1) MaterialTheme.colorScheme.primary else Color.Transparent,
                    shape = RoundedCornerShape(50),
                    modifier = Modifier
                        .weight(1f)
                        .clickable { selectedLearnTab = 1 }
                ) {
                    Text(
                        text = "Chord Trainer",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.SemiBold,
                        textAlign = TextAlign.Center,
                        color = if (selectedLearnTab == 1) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.padding(vertical = 8.dp)
                    )
                }
            }
        }

        if (selectedLearnTab == 0) {
            // ─────────────────────────────────────────────────────────────────────
            // 1. FREEPLAY PLAYGROUND CARD
            // ─────────────────────────────────────────────────────────────────────
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                color = MaterialTheme.colorScheme.surface,
                border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    // Header with Overline & Language Toggle
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "BRAILLEBRIDGE · LEARNER",
                            fontSize = 11.sp,
                            fontFamily = FontFamily.Monospace,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.primary
                        )

                        // Language Toggle Pills
                        Surface(
                            color = MaterialTheme.colorScheme.surfaceVariant,
                            shape = RoundedCornerShape(20.dp),
                            border = BorderStroke(1.dp, Color(0xFFD0CCC4))
                        ) {
                            Row(modifier = Modifier.padding(3.dp)) {
                                Surface(
                                    color = if (!isBangla) MaterialTheme.colorScheme.primary else Color.Transparent,
                                    shape = RoundedCornerShape(16.dp),
                                    modifier = Modifier.clickable { viewModel.setLearnerLang(false) }
                                ) {
                                    Text(
                                        text = "English",
                                        fontSize = 11.sp,
                                        fontWeight = FontWeight.Medium,
                                        color = if (!isBangla) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurfaceVariant,
                                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                                    )
                                }
                                Surface(
                                    color = if (isBangla) AccentGreen else Color.Transparent,
                                    shape = RoundedCornerShape(16.dp),
                                    modifier = Modifier.clickable { viewModel.setLearnerLang(true) }
                                ) {
                                    Text(
                                        text = "বাংলা",
                                        fontSize = 11.sp,
                                        fontWeight = FontWeight.Medium,
                                        color = if (isBangla) Color.White else MaterialTheme.colorScheme.onSurfaceVariant,
                                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                                    )
                                }
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(8.dp))

                    Text(
                        text = "Freeplay Playground",
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Serif,
                        color = MaterialTheme.colorScheme.onSurface,
                        modifier = Modifier.fillMaxWidth()
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "Type on the BrailleBridge or your keyboard — every character is spoken aloud. Finish a word with SPACE and the whole word is spoken.",
                        fontSize = 12.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.fillMaxWidth()
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    // Connect & Voice Status Chips
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(IntrinsicSize.Min),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Surface(
                            color = if (isConnected) AccentGreen.copy(alpha = 0.15f) else MaterialTheme.colorScheme.surfaceVariant,
                            shape = RoundedCornerShape(12.dp),
                            border = BorderStroke(1.dp, Color(0xFFD6D1C7)),
                            modifier = Modifier
                                .weight(1f)
                                .fillMaxHeight()
                                .clickable { viewModel.showBleScanDialog.value = true }
                        ) {
                            Row(
                                modifier = Modifier.padding(horizontal = 10.dp, vertical = 8.dp),
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
                                    text = if (isConnected) "Connected" else "Connect BrailleBridge",
                                    fontSize = 11.sp,
                                    maxLines = 1,
                                    overflow = TextOverflow.Ellipsis,
                                    color = if (isConnected) AccentGreen else MaterialTheme.colorScheme.onSurface
                                )
                            }
                        }

                        // Voice status chip
                        val voiceText = when {
                            !ttsReady -> "Speech initializing…"
                            isBangla && !banglaAvailable -> "Bangla TTS unavailable"
                            isBangla -> "Bangla Voice Ready"
                            else -> "English Voice Ready"
                        }
                        val voiceColor = when {
                            !ttsReady -> TextMuted
                            isBangla && !banglaAvailable -> AccentRed
                            else -> AccentGreen
                        }
                        Surface(
                            color = voiceColor.copy(alpha = 0.12f),
                            shape = RoundedCornerShape(12.dp),
                            border = BorderStroke(1.dp, voiceColor.copy(alpha = 0.35f)),
                            modifier = Modifier
                                .weight(1f)
                                .fillMaxHeight()
                        ) {
                            Row(
                                modifier = Modifier.padding(horizontal = 10.dp, vertical = 8.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Icon(
                                    imageVector = if (isAudioEnabled) Icons.AutoMirrored.Filled.VolumeUp else Icons.AutoMirrored.Filled.VolumeOff,
                                    contentDescription = null,
                                    tint = voiceColor,
                                    modifier = Modifier.size(16.dp)
                                )
                                Spacer(modifier = Modifier.width(6.dp))
                                Text(
                                    text = voiceText,
                                    fontSize = 11.sp,
                                    maxLines = 1,
                                    overflow = TextOverflow.Ellipsis,
                                    color = voiceColor
                                )
                            }
                        }
                    }

                Spacer(modifier = Modifier.height(12.dp))

                // Interactive Text Display / Input Area
                Surface(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(min = 100.dp),
                    shape = RoundedCornerShape(10.dp),
                    color = MaterialTheme.colorScheme.surfaceVariant,
                    border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
                ) {
                    Box(modifier = Modifier.padding(14.dp)) {
                        if (inputText.isEmpty()) {
                            Text(
                                text = "Type any letter on keyboard or BrailleBridge — it will be spoken aloud…",
                                fontSize = 14.sp,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        } else {
                            val caretColor = MaterialTheme.colorScheme.primary
                            val caretAlpha by rememberInfiniteTransition(label = "caret").animateFloat(
                                initialValue = 0.2f,
                                targetValue = 1f,
                                animationSpec = infiniteRepeatable(
                                    animation = tween(500, easing = FastOutSlowInEasing),
                                    repeatMode = RepeatMode.Reverse
                                ),
                                label = "caret"
                            )
                            Text(
                                text = buildAnnotatedString {
                                    append(inputText)
                                    withStyle(SpanStyle(background = caretColor.copy(alpha = caretAlpha))) {
                                        append("▏")
                                    }
                                },
                                fontSize = 20.sp,
                                fontFamily = FontFamily.Serif,
                                color = MaterialTheme.colorScheme.onSurface
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(10.dp))

                // Spoken Words History Box
                Surface(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(min = 60.dp),
                    shape = RoundedCornerShape(8.dp),
                    color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f),
                    border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.5f))
                ) {
                    Box(modifier = Modifier.padding(8.dp)) {
                        if (spokenWords.isEmpty()) {
                            Text(
                                text = "Spoken words appear here as you type spaces",
                                fontSize = 12.sp,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                modifier = Modifier.align(Alignment.Center)
                            )
                        } else {
                            FlowRow(
                                horizontalArrangement = Arrangement.spacedBy(6.dp),
                                verticalArrangement = Arrangement.spacedBy(6.dp)
                            ) {
                                spokenWords.forEach { word ->
                                    Surface(
                                        color = MaterialTheme.colorScheme.primary.copy(alpha = 0.15f),
                                        shape = RoundedCornerShape(6.dp),
                                        modifier = Modifier.clickable {
                                            viewModel.ttsManager.speakWord(word, isBangla)
                                        }
                                    ) {
                                        Text(
                                            text = word,
                                            fontSize = 13.sp,
                                            fontFamily = FontFamily.Serif,
                                            fontWeight = FontWeight.Medium,
                                            color = MaterialTheme.colorScheme.primary,
                                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp)
                                        )
                                    }
                                }
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(12.dp))

                // Actions: Repeat Last Word, Export Progress, Clear
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    OutlinedButton(
                        onClick = { viewModel.repeatLastLearnerWord() },
                        enabled = spokenWords.isNotEmpty(),
                        shape = RoundedCornerShape(10.dp),
                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 8.dp),
                        border = BorderStroke(
                            1.dp,
                            if (spokenWords.isNotEmpty()) Color(0xFFD0CCC4) else Color(0xFFE8E5DF)
                        ),
                        modifier = Modifier
                            .weight(1f)
                            .height(44.dp)
                    ) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.RotateLeft,
                            contentDescription = null,
                            modifier = Modifier.size(15.dp)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("Repeat", fontSize = 12.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                    }

                    OutlinedButton(
                        onClick = { viewModel.exportLearnerProgress(context) },
                        shape = RoundedCornerShape(10.dp),
                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 8.dp),
                        border = BorderStroke(1.dp, Color(0xFFD0CCC4)),
                        modifier = Modifier
                            .weight(1f)
                            .height(44.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.Download,
                            contentDescription = null,
                            modifier = Modifier.size(15.dp)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("Export", fontSize = 12.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                    }

                    OutlinedButton(
                        onClick = { viewModel.clearLearnerPlayground() },
                        shape = RoundedCornerShape(10.dp),
                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 8.dp),
                        border = BorderStroke(1.dp, Color(0xFFD0CCC4)),
                        modifier = Modifier
                            .weight(0.9f)
                            .height(44.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.Clear,
                            contentDescription = null,
                            modifier = Modifier.size(15.dp)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("Clear", fontSize = 12.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                    }
                }
            }
        }
    } else {
        // ─────────────────────────────────────────────────────────────────────
        // 2. SEE WHAT CODES YOU NEED (TRAINER TOOL) CARD
        // ─────────────────────────────────────────────────────────────────────
        Surface(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
            color = MaterialTheme.colorScheme.surface,
            border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                // Header with Overline & Language Toggle
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "BRAILLEBRIDGE · FOR TRAINERS",
                        fontSize = 11.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary
                    )

                    // Decoder Language Toggle
                    Surface(
                        color = MaterialTheme.colorScheme.surfaceVariant,
                        shape = RoundedCornerShape(20.dp),
                        border = BorderStroke(1.dp, Color(0xFFD0CCC4))
                    ) {
                        Row(modifier = Modifier.padding(3.dp)) {
                            Surface(
                                color = if (!decoderIsBangla) MaterialTheme.colorScheme.primary else Color.Transparent,
                                shape = RoundedCornerShape(16.dp),
                                modifier = Modifier.clickable { viewModel.setLearnerDecoderLang(false) }
                            ) {
                                Text(
                                    text = "English",
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Medium,
                                    color = if (!decoderIsBangla) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurfaceVariant,
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                                )
                            }
                            Surface(
                                color = if (decoderIsBangla) AccentGreen else Color.Transparent,
                                shape = RoundedCornerShape(16.dp),
                                modifier = Modifier.clickable { viewModel.setLearnerDecoderLang(true) }
                            ) {
                                Text(
                                    text = "বাংলা",
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Medium,
                                    color = if (decoderIsBangla) Color.White else MaterialTheme.colorScheme.onSurfaceVariant,
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                                )
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = "See What Codes You Need",
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Serif,
                    color = MaterialTheme.colorScheme.onSurface,
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Type any word or sentence — get the exact chord sequence a student must press, in order.",
                    fontSize = 12.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.fillMaxWidth()
                )

                Spacer(modifier = Modifier.height(14.dp))

                // Decoder Input Row
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    OutlinedTextField(
                        value = decoderInput,
                        onValueChange = { viewModel.setLearnerDecoderInput(it) },
                        placeholder = {
                            Text(
                                text = if (decoderIsBangla) "যেমনঃ বাংলা অথবা ধন্যবাদ" else "e.g. Hello world",
                                fontSize = 13.sp
                            )
                        },
                        singleLine = true,
                        modifier = Modifier.weight(1f),
                        shape = RoundedCornerShape(10.dp),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = MaterialTheme.colorScheme.primary,
                            unfocusedBorderColor = MaterialTheme.colorScheme.outlineVariant
                        )
                    )

                    Button(
                        onClick = { viewModel.generateLearnerCodes() },
                        shape = RoundedCornerShape(10.dp),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = MaterialTheme.colorScheme.primary
                        )
                    ) {
                        Icon(
                            imageVector = Icons.Default.AutoAwesome,
                            contentDescription = null,
                            modifier = Modifier.size(16.dp)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("Show codes", fontSize = 12.sp)
                    }
                }

                Spacer(modifier = Modifier.height(14.dp))

                // Decoded Chord Sequence
                if (decodedSteps.isEmpty()) {
                    Surface(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(80.dp),
                        shape = RoundedCornerShape(10.dp),
                        color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
                    ) {
                        Box(modifier = Modifier.fillMaxSize()) {
                            Text(
                                text = "Enter text above and tap 'Show codes' to view chord sequence",
                                fontSize = 12.sp,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                modifier = Modifier.align(Alignment.Center)
                            )
                        }
                    }
                } else {
                    LazyRow(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        items(decodedSteps) { step ->
                            when (step) {
                                is DecodedStep.ChordStep -> {
                                    ChordStepCard(
                                        step = step,
                                        isBangla = decoderIsBangla,
                                        onSpeak = {
                                            viewModel.ttsManager.speakChar(step.char, decoderIsBangla)
                                        }
                                    )
                                }
                                is DecodedStep.SpaceStep -> {
                                    SpecialStepCard(
                                        label = "SPACE",
                                        icon = Icons.Default.SpaceBar,
                                        description = "Word break"
                                    )
                                }
                                is DecodedStep.NewlineStep -> {
                                    SpecialStepCard(
                                        label = "ENTER",
                                        icon = Icons.Default.KeyboardReturn,
                                        description = "Line break"
                                    )
                                }
                                is DecodedStep.UnknownStep -> {
                                    Surface(
                                        modifier = Modifier.size(width = 80.dp, height = 120.dp),
                                        shape = RoundedCornerShape(10.dp),
                                        color = MaterialTheme.colorScheme.surfaceVariant,
                                        border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
                                    ) {
                                        Column(
                                            modifier = Modifier.padding(6.dp),
                                            horizontalAlignment = Alignment.CenterHorizontally,
                                            verticalArrangement = Arrangement.Center
                                        ) {
                                            Text(
                                                text = step.char,
                                                fontSize = 20.sp,
                                                fontFamily = FontFamily.Serif,
                                                fontWeight = FontWeight.Bold,
                                                color = MaterialTheme.colorScheme.error
                                            )
                                            Spacer(modifier = Modifier.height(4.dp))
                                            Text(
                                                text = "No chord",
                                                fontSize = 9.sp,
                                                color = MaterialTheme.colorScheme.onSurfaceVariant
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
}

@Composable
private fun ChordStepCard(
    step: DecodedStep.ChordStep,
    isBangla: Boolean,
    onSpeak: () -> Unit
) {
    Surface(
        modifier = Modifier
            .size(width = 96.dp, height = 145.dp)
            .clickable(onClick = onSpeak),
        shape = RoundedCornerShape(12.dp),
        color = MaterialTheme.colorScheme.surfaceVariant,
        border = androidx.compose.foundation.BorderStroke(1.dp, Gold.copy(alpha = 0.5f))
    ) {
        Column(
            modifier = Modifier.padding(6.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            // Character display + Shift pill
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = step.char,
                    fontSize = 20.sp,
                    fontFamily = FontFamily.Serif,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.onSurface
                )
                if (step.shift) {
                    Surface(
                        color = Gold,
                        shape = RoundedCornerShape(4.dp)
                    ) {
                        Text(
                            text = "Shift",
                            fontSize = 8.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color.Black,
                            modifier = Modifier.padding(horizontal = 4.dp, vertical = 1.dp)
                        )
                    }
                }
            }

            // Mini 6-dot Braille Cell (2 columns x 3 rows)
            MiniBrailleCell(activeDots = step.dots.toSet())

            // Dot numbers & binary
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    text = "Dots " + step.dots.joinToString(","),
                    fontSize = 9.sp,
                    fontWeight = FontWeight.Medium,
                    color = MaterialTheme.colorScheme.primary,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
                Text(
                    text = "0b" + step.chord.toString(2).padStart(6, '0'),
                    fontSize = 8.sp,
                    fontFamily = FontFamily.Monospace,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

@Composable
private fun MiniBrailleCell(activeDots: Set<Int>) {
    Row(
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Column 1: dots 1, 2, 3
        Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
            MiniDot(isPressed = activeDots.contains(1))
            MiniDot(isPressed = activeDots.contains(2))
            MiniDot(isPressed = activeDots.contains(3))
        }
        // Column 2: dots 4, 5, 6
        Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
            MiniDot(isPressed = activeDots.contains(4))
            MiniDot(isPressed = activeDots.contains(5))
            MiniDot(isPressed = activeDots.contains(6))
        }
    }
}

@Composable
private fun MiniDot(isPressed: Boolean) {
    val bg = if (isPressed) {
        Brush.linearGradient(listOf(GoldLight, GoldDark))
    } else {
        Brush.linearGradient(listOf(Color(0xFF4A4D5E), Color(0xFF383A4A)))
    }
    Box(
        modifier = Modifier
            .size(10.dp)
            .clip(CircleShape)
            .background(bg)
            .border(
                width = if (isPressed) 1.dp else 0.5.dp,
                color = if (isPressed) Gold else Color.Transparent,
                shape = CircleShape
            )
    )
}

@Composable
private fun SpecialStepCard(
    label: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    description: String
) {
    Surface(
        modifier = Modifier.size(width = 86.dp, height = 145.dp),
        shape = RoundedCornerShape(12.dp),
        color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.7f),
        border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
    ) {
        Column(
            modifier = Modifier.padding(6.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary,
                modifier = Modifier.size(24.dp)
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = label,
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                fontFamily = FontFamily.Monospace,
                color = MaterialTheme.colorScheme.primary
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = description,
                fontSize = 8.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}
