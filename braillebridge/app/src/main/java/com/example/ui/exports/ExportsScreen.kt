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
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ClearAll
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Download
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material.icons.filled.Person
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.data.ExportEntity
import com.example.data.getColorForIndex
import com.example.data.getInitials
import com.example.protocol.AutoFormatter
import com.example.ui.MainViewModel
import com.example.ui.theme.AccentGreen
import com.example.ui.theme.AccentRed
import com.example.ui.theme.Gold
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

data class StudentLogGroup(
    val studentName: String,
    val colorHex: String,
    val sessions: List<ExportEntity>,
    val latestTimestamp: Long,
    val totalChars: Int,
    val connInfo: String
)

@Composable
fun ExportsScreen(
    viewModel: MainViewModel,
    modifier: Modifier = Modifier
) {
    val exports by viewModel.exportsList.collectAsState()
    val rosterStudents by viewModel.students.collectAsState()
    val reviewExport by viewModel.reviewExport.collectAsState()
    val selectedStudentName by viewModel.selectedLogStudentName.collectAsState()
    val context = LocalContext.current

    var studentToDelete by remember { mutableStateOf<String?>(null) }
    var showClearAllConfirm by remember { mutableStateOf(false) }

    val dateFormat = remember { SimpleDateFormat("MMM dd, yyyy · HH:mm", Locale.US) }

    // Group all saved exports by student name
    val studentGroups = remember(exports, rosterStudents) {
        val grouped = exports.groupBy { (it.studentName ?: it.title).ifBlank { "Student 1" } }
        val allNames = linkedSetOf<String>()
        grouped.keys.forEach { allNames.add(it) }
        rosterStudents.forEach { if (it.chars.isNotEmpty()) allNames.add(it.name) }

        allNames.mapIndexed { idx, name ->
            val sessions = grouped[name]?.sortedByDescending { it.created } ?: emptyList()
            val rosterMatch = rosterStudents.find { it.name == name }
            val colorHex = rosterMatch?.color ?: getColorForIndex(idx)
            val totalChars = if (sessions.isNotEmpty()) {
                sessions.sumOf { it.charsCount }
            } else {
                rosterMatch?.chars?.size ?: 0
            }
            val latestTime = sessions.firstOrNull()?.created ?: System.currentTimeMillis()
            val conn = sessions.firstOrNull()?.connInfo
                ?: rosterMatch?.let { "Bluetooth · ${it.deviceAddress ?: "Live"}" }
                ?: "Bluetooth"
            StudentLogGroup(
                studentName = name,
                colorHex = colorHex,
                sessions = sessions,
                latestTimestamp = latestTime,
                totalChars = totalChars,
                connInfo = conn
            )
        }.sortedByDescending { it.latestTimestamp }
    }

    // If a specific student or export is selected, show the big editorial ReviewScreen
    val activeGroup = remember(selectedStudentName, reviewExport, studentGroups) {
        when {
            selectedStudentName != null -> studentGroups.find { it.studentName == selectedStudentName }
            reviewExport != null -> {
                val sName = (reviewExport!!.studentName ?: reviewExport!!.title).ifBlank { "Student 1" }
                studentGroups.find { it.studentName == sName } ?: StudentLogGroup(
                    studentName = sName,
                    colorHex = getColorForIndex(0),
                    sessions = listOf(reviewExport!!),
                    latestTimestamp = reviewExport!!.created,
                    totalChars = reviewExport!!.charsCount,
                    connInfo = reviewExport!!.connInfo ?: "Bluetooth"
                )
            }
            else -> null
        }
    }

    if (activeGroup != null) {
        ReviewScreen(
            studentGroup = activeGroup,
            initialExport = reviewExport,
            viewModel = viewModel,
            onBack = {
                viewModel.selectedLogStudentName.value = null
                viewModel.reviewExport.value = null
            }
        )
        return
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        // Header Banner: Student Writing Logs Directory
        Surface(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(14.dp),
            color = MaterialTheme.colorScheme.surface,
            border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = "STUDENT WRITING LOGS",
                            fontSize = 11.sp,
                            fontFamily = FontFamily.Monospace,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.primary
                        )
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = "${studentGroups.size} Student(s) · ${exports.size} Saved Session(s)",
                            fontSize = 12.sp,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }

                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        Button(
                            onClick = { viewModel.exportAllStudents(context) },
                            colors = ButtonDefaults.buttonColors(
                                containerColor = MaterialTheme.colorScheme.primary
                            ),
                            shape = RoundedCornerShape(10.dp),
                            contentPadding = PaddingValues(horizontal = 10.dp, vertical = 8.dp)
                        ) {
                            Icon(
                                imageVector = Icons.Default.Download,
                                contentDescription = null,
                                modifier = Modifier.size(15.dp)
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                            Text("Export All", fontSize = 11.sp, maxLines = 1)
                        }

                        if (exports.isNotEmpty()) {
                            OutlinedButton(
                                onClick = { showClearAllConfirm = true },
                                shape = RoundedCornerShape(10.dp),
                                contentPadding = PaddingValues(horizontal = 10.dp, vertical = 8.dp)
                            ) {
                                Icon(
                                    imageVector = Icons.Default.ClearAll,
                                    contentDescription = null,
                                    modifier = Modifier.size(15.dp)
                                )
                                Spacer(modifier = Modifier.width(4.dp))
                                Text("Clear", fontSize = 11.sp, maxLines = 1)
                            }
                        }
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(14.dp))

        if (studentGroups.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                contentAlignment = Alignment.Center
            ) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    modifier = Modifier.padding(24.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.MenuBook,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.primary.copy(alpha = 0.6f),
                        modifier = Modifier.size(48.dp)
                    )
                    Spacer(modifier = Modifier.height(14.dp))
                    Text(
                        text = "No Student Writing Logs Yet",
                        fontSize = 16.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(
                        text = "Tap 'Export All' in the Student or Teacher tab to save student writing. Each student will appear here so you can tap their name and read what they wrote.",
                        fontSize = 13.sp,
                        textAlign = TextAlign.Center,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        } else {
            Text(
                text = "SELECT A STUDENT TO READ THEIR WRITING",
                fontSize = 11.sp,
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(bottom = 8.dp, start = 2.dp)
            )

            LazyColumn(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(studentGroups, key = { it.studentName }) { group ->
                    val colorParsed = try {
                        Color(android.graphics.Color.parseColor(group.colorHex))
                    } catch (e: Exception) {
                        MaterialTheme.colorScheme.primary
                    }

                    val combinedBlocks = remember(group.sessions) {
                        group.sessions.flatMap { viewModel.parseBlocks(it.blocksJson) }
                    }
                    val previewText = remember(combinedBlocks) {
                        combinedBlocks.joinToString(" ") { it.text }.trim()
                    }
                    val wordCount = remember(previewText) {
                        if (previewText.isBlank()) 0 else previewText.split(Regex("\\s+")).size
                    }

                    Surface(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable {
                                viewModel.selectedLogStudentName.value = group.studentName
                            },
                        shape = RoundedCornerShape(20.dp),
                        color = MaterialTheme.colorScheme.surface,
                        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    modifier = Modifier.weight(1f)
                                ) {
                                    Box(
                                        modifier = Modifier
                                            .size(44.dp)
                                            .clip(CircleShape)
                                            .background(colorParsed),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        Text(
                                            text = getInitials(group.studentName),
                                            color = Color.White,
                                            fontWeight = FontWeight.Bold,
                                            fontSize = 15.sp
                                        )
                                    }
                                    Spacer(modifier = Modifier.width(12.dp))
                                    Column {
                                        Text(
                                            text = group.studentName,
                                            fontWeight = FontWeight.Bold,
                                            fontSize = 16.sp,
                                            color = MaterialTheme.colorScheme.onSurface
                                        )
                                        Text(
                                            text = "Last updated ${dateFormat.format(Date(group.latestTimestamp))}",
                                            fontSize = 11.sp,
                                            color = MaterialTheme.colorScheme.onSurfaceVariant
                                        )
                                    }
                                }

                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Surface(
                                        color = Gold.copy(alpha = 0.16f),
                                        shape = RoundedCornerShape(50),
                                        border = BorderStroke(1.dp, Gold.copy(alpha = 0.5f))
                                    ) {
                                        Text(
                                            text = "${group.sessions.size} session${if (group.sessions.size == 1) "" else "s"}",
                                            fontSize = 11.sp,
                                            fontWeight = FontWeight.SemiBold,
                                            color = MaterialTheme.colorScheme.primary,
                                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                                        )
                                    }

                                    IconButton(
                                        onClick = { studentToDelete = group.studentName },
                                        modifier = Modifier.size(32.dp)
                                    ) {
                                        Icon(
                                            imageVector = Icons.Default.Delete,
                                            contentDescription = "Delete Student Logs",
                                            tint = AccentRed,
                                            modifier = Modifier.size(17.dp)
                                        )
                                    }
                                }
                            }

                            if (previewText.isNotEmpty()) {
                                Spacer(modifier = Modifier.height(10.dp))
                                Surface(
                                    modifier = Modifier.fillMaxWidth(),
                                    color = MaterialTheme.colorScheme.surfaceVariant,
                                    shape = RoundedCornerShape(14.dp)
                                ) {
                                    Text(
                                        text = previewText,
                                        fontFamily = FontFamily.Serif,
                                        fontSize = 16.sp,
                                        lineHeight = 23.sp,
                                        maxLines = 2,
                                        overflow = TextOverflow.Ellipsis,
                                        color = MaterialTheme.colorScheme.onSurface,
                                        modifier = Modifier.padding(12.dp)
                                    )
                                }
                            }

                            Spacer(modifier = Modifier.height(10.dp))

                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    text = "$wordCount words · ${group.totalChars} chars · ${combinedBlocks.size} smart blocks",
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Medium,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }

                            Spacer(modifier = Modifier.height(10.dp))

                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                Button(
                                    onClick = {
                                        viewModel.selectedLogStudentName.value = group.studentName
                                    },
                                    colors = ButtonDefaults.buttonColors(
                                        containerColor = MaterialTheme.colorScheme.primary
                                    ),
                                    shape = RoundedCornerShape(10.dp),
                                    modifier = Modifier.weight(1.4f)
                                ) {
                                    Icon(
                                        imageVector = Icons.Default.MenuBook,
                                        contentDescription = null,
                                        modifier = Modifier.size(16.dp)
                                    )
                                    Spacer(modifier = Modifier.width(6.dp))
                                    Text("Read Writing Log", fontSize = 12.sp)
                                }

                                OutlinedButton(
                                    onClick = {
                                        val text = AutoFormatter.toText(combinedBlocks)
                                        val shareIntent = Intent(Intent.ACTION_SEND).apply {
                                            type = "text/plain"
                                            putExtra(Intent.EXTRA_SUBJECT, "${group.studentName} — Writing Log")
                                            putExtra(Intent.EXTRA_TEXT, text)
                                        }
                                        context.startActivity(Intent.createChooser(shareIntent, "Share Student Log"))
                                    },
                                    shape = RoundedCornerShape(10.dp),
                                    modifier = Modifier.weight(0.8f)
                                ) {
                                    Icon(
                                        imageVector = Icons.Default.Download,
                                        contentDescription = null,
                                        modifier = Modifier.size(15.dp)
                                    )
                                    Spacer(modifier = Modifier.width(4.dp))
                                    Text(".txt", fontSize = 12.sp)
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Delete student's logs confirmation
    studentToDelete?.let { name ->
        AlertDialog(
            onDismissRequest = { studentToDelete = null },
            title = { Text("Delete Logs for $name?") },
            text = { Text("Are you sure you want to remove all saved writing logs for '$name'?") },
            confirmButton = {
                Button(
                    onClick = {
                        viewModel.deleteStudentLogs(name)
                        studentToDelete = null
                    },
                    shape = RoundedCornerShape(10.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = AccentRed)
                ) {
                    Text("Delete")
                }
            },
            dismissButton = {
                OutlinedButton(
                    onClick = { studentToDelete = null },
                    shape = RoundedCornerShape(10.dp)
                ) {
                    Text("Cancel")
                }
            }
        )
    }

    // Clear all logs confirmation
    if (showClearAllConfirm) {
        AlertDialog(
            onDismissRequest = { showClearAllConfirm = false },
            title = { Text("Clear All Student Writing Logs?") },
            text = { Text("This will permanently remove all saved student writing logs.") },
            confirmButton = {
                Button(
                    onClick = {
                        viewModel.clearAllExports()
                        showClearAllConfirm = false
                    },
                    shape = RoundedCornerShape(10.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = AccentRed)
                ) {
                    Text("Clear All")
                }
            },
            dismissButton = {
                OutlinedButton(
                    onClick = { showClearAllConfirm = false },
                    shape = RoundedCornerShape(10.dp)
                ) {
                    Text("Cancel")
                }
            }
        )
    }
}
