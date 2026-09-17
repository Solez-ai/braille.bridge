package com.example

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.view.KeyEvent
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Bluetooth
import androidx.compose.material.icons.filled.BluetoothConnected
import androidx.compose.material.icons.filled.DarkMode
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.Group
import androidx.compose.material.icons.filled.LightMode
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.School
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import com.example.ble.BleProxyService
import com.example.ui.AppMode
import com.example.ui.MainViewModel
import com.example.ui.account.AccountDialog
import com.example.ui.account.TeacherAccountChip
import com.example.ui.components.AddStudentDialog
import com.example.ui.components.BleScanDialog
import com.example.ui.components.ExpandModal
import com.example.ui.components.PreviewModal
import com.example.ui.components.SendModal
import com.example.ui.exam.ExamScreen
import com.example.ui.exports.ExportsScreen
import com.example.ui.student.StudentScreen
import com.example.ui.teacher.TeacherScreen
import com.example.ui.theme.AccentGreen
import com.example.ui.theme.BrailleBridgeTheme
import com.example.ui.theme.Gold

class MainActivity : ComponentActivity() {

    private val viewModel: MainViewModel by viewModels()

    override fun onResume() {
        super.onResume()
        // Pick up any Bluetooth devices connected natively in phone settings
        BleProxyService.instance?.checkSystemConnectedDevices()
    }

    @OptIn(ExperimentalMaterial3Api::class)
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        setContent {
            val isDarkTheme by viewModel.isDarkTheme.collectAsState()
            val currentMode by viewModel.currentMode.collectAsState()

            // Request Bluetooth & Notification runtime permissions
            RequestPermissionsEffect()

            BrailleBridgeTheme(darkTheme = isDarkTheme) {
                val showAccount by viewModel.showAccountDialog.collectAsState()
                val showAddStudent by viewModel.showAddStudentDialog.collectAsState()
                val showBleScan by viewModel.showBleScanDialog.collectAsState()
                val previewStudent by viewModel.previewStudent.collectAsState()
                val expandStudent by viewModel.expandStudent.collectAsState()
                val sendModalOpen by viewModel.sendModalOpen.collectAsState()

                val connectedCount by BleProxyService.instance?.connectedCount?.collectAsState() ?: remember { androidx.compose.runtime.mutableStateOf(0) }
                val students by viewModel.students.collectAsState()
                val exports by viewModel.exportsList.collectAsState()
                val totalChars by viewModel.totalCharsAllStudents.collectAsState()

                Scaffold(
                    topBar = {
                        TopAppBar(
                            title = {
                                Text(
                                    text = "BrailleBridge",
                                    fontFamily = FontFamily.Serif,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 19.sp,
                                    color = MaterialTheme.colorScheme.onSurface
                                )
                            },
                            actions = {
                                // Teacher Account Chip (Samin Yeasar)
                                TeacherAccountChip(
                                    onClick = { viewModel.showAccountDialog.value = true }
                                )

                                // BLE quick connect button
                                IconButton(onClick = { viewModel.showBleScanDialog.value = true }) {
                                    Icon(
                                        imageVector = if (connectedCount > 0) Icons.Default.BluetoothConnected else Icons.Default.Bluetooth,
                                        contentDescription = "Bluetooth Status",
                                        tint = if (connectedCount > 0) AccentGreen else MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                }

                                // Dark / Light theme toggle
                                IconButton(onClick = { viewModel.toggleTheme() }) {
                                    Icon(
                                        imageVector = if (isDarkTheme) Icons.Default.LightMode else Icons.Default.DarkMode,
                                        contentDescription = "Toggle Theme",
                                        tint = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                }
                            },
                            colors = TopAppBarDefaults.topAppBarColors(
                                containerColor = MaterialTheme.colorScheme.surface
                            )
                        )
                    },
                    bottomBar = {
                        NavigationBar(
                            containerColor = MaterialTheme.colorScheme.surface
                        ) {
                            NavigationBarItem(
                                selected = currentMode == AppMode.STUDENT,
                                onClick = { viewModel.currentMode.value = AppMode.STUDENT },
                                icon = {
                                    Icon(
                                        imageVector = Icons.Default.School,
                                        contentDescription = "Student View"
                                    )
                                },
                                label = { Text("Student", fontSize = 11.sp) }
                            )

                            NavigationBarItem(
                                selected = currentMode == AppMode.TEACHER,
                                onClick = { viewModel.currentMode.value = AppMode.TEACHER },
                                icon = {
                                    Icon(
                                        imageVector = Icons.Default.Group,
                                        contentDescription = "Teacher View"
                                    )
                                },
                                label = { Text("Teacher", fontSize = 11.sp) }
                            )

                            NavigationBarItem(
                                selected = currentMode == AppMode.EXAM,
                                onClick = { viewModel.currentMode.value = AppMode.EXAM },
                                icon = {
                                    Icon(
                                        imageVector = Icons.Default.Lock,
                                        contentDescription = "Exam View"
                                    )
                                },
                                label = { Text("Exam", fontSize = 11.sp) }
                            )

                            NavigationBarItem(
                                selected = currentMode == AppMode.EXPORTS,
                                onClick = { viewModel.currentMode.value = AppMode.EXPORTS },
                                icon = {
                                    Icon(
                                        imageVector = Icons.Default.Description,
                                        contentDescription = "Exports Library"
                                    )
                                },
                                label = { Text("Exports", fontSize = 11.sp) }
                            )
                        }
                    }
                ) { innerPadding ->
                    Box(modifier = Modifier.padding(innerPadding)) {
                        when (currentMode) {
                            AppMode.STUDENT -> StudentScreen(viewModel = viewModel)
                            AppMode.TEACHER -> TeacherScreen(viewModel = viewModel)
                            AppMode.EXAM -> ExamScreen(viewModel = viewModel)
                            AppMode.EXPORTS -> ExportsScreen(viewModel = viewModel)
                        }
                    }
                }

                // Global Modals
                if (showAccount) {
                    AccountDialog(
                        studentCount = students.size,
                        exportCount = exports.size,
                        characterCount = totalChars,
                        onDismiss = { viewModel.showAccountDialog.value = false }
                    )
                }

                if (showBleScan) {
                    val scannedDevices by viewModel.scannedDevices.collectAsState()
                    val activeAddr by viewModel.activeStudentDeviceAddress.collectAsState()
                    val isConn by viewModel.isStudentDeviceConnected.collectAsState()
                    BleScanDialog(
                        scannedDevices = scannedDevices,
                        connectedAddress = activeAddr,
                        isConnected = isConn,
                        onConnect = { dev -> viewModel.connectScannedDevice(dev) },
                        onDisconnect = { viewModel.disconnectStudentDevice() },
                        onDismiss = { viewModel.showBleScanDialog.value = false }
                    )
                }

                if (showAddStudent) {
                    val scannedDevices by viewModel.scannedDevices.collectAsState()
                    AddStudentDialog(
                        scannedDevices = scannedDevices,
                        onAdd = { name, baud, devAddr ->
                            viewModel.addStudent(name, baud, devAddr)
                        },
                        onDismiss = { viewModel.showAddStudentDialog.value = false }
                    )
                }

                previewStudent?.let { st ->
                    val ctx = LocalContext.current
                    PreviewModal(
                        student = st,
                        onExport = {
                            viewModel.exportSingleStudent(st, ctx)
                            viewModel.previewStudent.value = null
                        },
                        onSaveToExports = {
                            viewModel.savePreviewToExports(st, ctx)
                            viewModel.previewStudent.value = null
                        },
                        onDismiss = { viewModel.previewStudent.value = null }
                    )
                }

                expandStudent?.let { st ->
                    ExpandModal(
                        student = st,
                        onClear = { viewModel.clearStudent(st) },
                        onPreviewHandOff = {
                            viewModel.expandStudent.value = null
                            viewModel.previewStudent.value = st
                        },
                        onDismiss = { viewModel.expandStudent.value = null }
                    )
                }

                if (sendModalOpen) {
                    val hasMirror = students.any { it.isMirror }
                    SendModal(
                        hasMirrorAlready = hasMirror,
                        onConfirmMirror = { viewModel.createMirrorStudent() },
                        onDismiss = { viewModel.sendModalOpen.value = false }
                    )
                }
            }
        }
    }

    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean {
        // Support physical keyboard shortcuts: 1-6 for dots, Space, Enter commit, Esc clear, L language, S shift
        when (keyCode) {
            KeyEvent.KEYCODE_1 -> { viewModel.toggleDot(1); return true }
            KeyEvent.KEYCODE_2 -> { viewModel.toggleDot(2); return true }
            KeyEvent.KEYCODE_3 -> { viewModel.toggleDot(3); return true }
            KeyEvent.KEYCODE_4 -> { viewModel.toggleDot(4); return true }
            KeyEvent.KEYCODE_5 -> { viewModel.toggleDot(5); return true }
            KeyEvent.KEYCODE_6 -> { viewModel.toggleDot(6); return true }
            KeyEvent.KEYCODE_SPACE -> { viewModel.addSpace(); return true }
            KeyEvent.KEYCODE_ENTER -> { viewModel.commitChord(); return true }
            KeyEvent.KEYCODE_DEL -> { viewModel.handleBackspace(); return true }
            KeyEvent.KEYCODE_ESCAPE -> { viewModel.clearStudentStream(); return true }
            KeyEvent.KEYCODE_L -> { viewModel.toggleLanguage(); return true }
            KeyEvent.KEYCODE_S -> { viewModel.toggleShift(); return true }
        }
        return super.onKeyDown(keyCode, event)
    }
}

@Composable
fun RequestPermissionsEffect() {
    val context = LocalContext.current
    val permissionsToRequest = mutableListOf<String>()

    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.BLUETOOTH_SCAN) != PackageManager.PERMISSION_GRANTED) {
            permissionsToRequest.add(Manifest.permission.BLUETOOTH_SCAN)
        }
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.BLUETOOTH_CONNECT) != PackageManager.PERMISSION_GRANTED) {
            permissionsToRequest.add(Manifest.permission.BLUETOOTH_CONNECT)
        }
    } else {
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            permissionsToRequest.add(Manifest.permission.ACCESS_FINE_LOCATION)
        }
    }

    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            permissionsToRequest.add(Manifest.permission.POST_NOTIFICATIONS)
        }
    }

    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestMultiplePermissions()
    ) {
        BleProxyService.instance?.promoteToForeground()
        BleProxyService.instance?.checkSystemConnectedDevices()
        BleProxyService.instance?.startScan()
    }

    LaunchedEffect(Unit) {
        if (permissionsToRequest.isNotEmpty()) {
            launcher.launch(permissionsToRequest.toTypedArray())
        } else {
            BleProxyService.instance?.promoteToForeground()
            BleProxyService.instance?.checkSystemConnectedDevices()
            BleProxyService.instance?.startScan()
        }
    }
}
