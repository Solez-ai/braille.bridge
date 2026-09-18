package com.example.ui

import android.app.Application
import android.bluetooth.BluetoothDevice
import android.content.Context
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.widget.Toast
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.ble.BleEvent
import com.example.ble.BleProxyService
import com.example.ble.ScannedBleDevice
import com.example.data.AppDatabase
import com.example.data.ExportEntity
import com.example.data.SettingsStore
import com.example.data.StudentEntity
import com.example.data.StudentModel
import com.example.data.getColorForIndex
import com.example.protocol.AutoFormatter
import com.example.protocol.BBTranslate
import com.example.protocol.BrailleDict
import com.example.protocol.TranslateResult
import kotlinx.coroutines.Job
import com.example.protocol.FormattedBlock
import com.example.protocol.TimedChar
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import org.json.JSONArray
import org.json.JSONObject
import java.util.UUID

enum class AppMode {
    STUDENT,
    TEACHER,
    EXAM,
    EXPORTS
}

class MainViewModel(application: Application) : AndroidViewModel(application) {

    private val db = AppDatabase.getDatabase(application)
    private val studentDao = db.studentDao()
    private val exportDao = db.exportDao()
    val settingsStore = SettingsStore(application)

    val exportsList = exportDao.getAllExports().stateIn(
        viewModelScope,
        SharingStarted.WhileSubscribed(5000),
        emptyList()
    )

    // Navigation & Appearance
    val currentMode = MutableStateFlow(AppMode.STUDENT)
    val isDarkTheme = MutableStateFlow(settingsStore.getTheme() == "dark")

    // Student View State
    val studentPressedDots = MutableStateFlow<Set<Int>>(emptySet())
    val studentChord = MutableStateFlow(0)
    val isBangla = MutableStateFlow(false)
    val shiftActive = MutableStateFlow(false)
    val studentChars = MutableStateFlow<List<TimedChar>>(emptyList())
    val studentRecentChars = MutableStateFlow<List<TimedChar>>(emptyList())
    val studentTranslateResult = MutableStateFlow<TranslateResult?>(null)
    val isStudentTranslating = MutableStateFlow(false)
    val studentTranslateTarget = MutableStateFlow("en") // defaults to "en"
    val studentTranslateError = MutableStateFlow<String?>(null)
    private var translateJob: Job? = null

    // Teacher View State
    val students = MutableStateFlow<List<StudentModel>>(emptyList())
    val totalCharsAllStudents = MutableStateFlow(0)

    // Active Dialogs & Modals
    val showAccountDialog = MutableStateFlow(false)
    val showAddStudentDialog = MutableStateFlow(false)
    val showBleScanDialog = MutableStateFlow(false)
    val previewStudent = MutableStateFlow<StudentModel?>(null)
    val expandStudent = MutableStateFlow<StudentModel?>(null)
    val sendModalOpen = MutableStateFlow(false)
    val reviewExport = MutableStateFlow<ExportEntity?>(null)

    // Active BLE Connection for Student View
    val activeStudentDeviceAddress = MutableStateFlow<String?>(null)
    val isStudentDeviceConnected = MutableStateFlow(false)

    // Scanned BLE Devices
    val scannedDevices = MutableStateFlow<List<ScannedBleDevice>>(emptyList())

    // Connection diagnostics console (most recent last, capped)
    val debugLog = MutableStateFlow<List<String>>(emptyList())
    private fun emitDebug(message: String) {
        val stamped = java.text.SimpleDateFormat("HH:mm:ss", java.util.Locale.US)
            .format(java.util.Date()) + "  " + message
        val next = debugLog.value.toMutableList()
        next.add(stamped)
        while (next.size > 60) next.removeAt(0)
        debugLog.value = next
    }

    private val handler = Handler(Looper.getMainLooper())

    init {
        // Load initial students from Room DB
        viewModelScope.launch {
            studentDao.getAllStudents().collect { entities ->
                val existing = students.value.associateBy { it.id }
                val updated = entities.mapIndexed { idx, entity ->
                    val prev = existing[entity.id]
                    val model = StudentModel(
                        id = entity.id,
                        name = entity.name,
                        connType = entity.connType,
                        baud = entity.baud,
                        deviceAddress = entity.deviceAddress,
                        isMirror = entity.isMirror,
                        color = getColorForIndex(idx),
                        chars = prev?.chars ?: mutableListOf(),
                        isConnected = prev?.isConnected ?: false,
                        lastChord = prev?.lastChord ?: 0
                    )
                    model
                }
                students.value = updated
                updateTotalChars()
            }
        }

        // Connect to BLE Proxy Service events
        viewModelScope.launch {
            while (true) {
                val service = BleProxyService.instance
                if (service != null) {
                    launch {
                        service.scannedDevices.collect {
                            scannedDevices.value = it
                        }
                    }
                    launch {
                        service.events.collect { event ->
                            handleBleEvent(event)
                        }
                    }
                    break
                }
                delay(200)
            }
        }

        // Periodic 500ms failsafe refresh for teacher feeds
        startFailsafeRefresh()
    }

    private fun startFailsafeRefresh() {
        handler.post(object : Runnable {
            override fun run() {
                updateTotalChars()
                handler.postDelayed(this, 2000)
            }
        })
    }

    private fun handleBleEvent(event: BleEvent) {
        when (event) {
            is BleEvent.DeviceConnected -> {
                if (activeStudentDeviceAddress.value == null || !isStudentDeviceConnected.value || activeStudentDeviceAddress.value == event.address) {
                    activeStudentDeviceAddress.value = event.address
                    isStudentDeviceConnected.value = true
                }
                updateStudentConnectionStatus(event.address, true)
            }
            is BleEvent.DeviceDisconnected -> {
                if (activeStudentDeviceAddress.value == event.address) {
                    isStudentDeviceConnected.value = false
                }
                updateStudentConnectionStatus(event.address, false)
            }
            is BleEvent.IncomingLine -> {
                handleIncomingLine(event.address, event.line)
            }
            is BleEvent.IncomingChars -> {
                handleIncomingChars(event.address, event.chars)
            }
            is BleEvent.Debug -> {
                emitDebug(event.message)
            }
        }
    }

    private fun updateStudentConnectionStatus(address: String, connected: Boolean) {
        val list = students.value
        var changed = false
        for (s in list) {
            if (s.deviceAddress == address) {
                if (s.isConnected != connected) {
                    s.isConnected = connected
                    changed = true
                }
            }
        }
        if (changed) {
            students.value = list.toList()
        }
    }

    private fun handleIncomingLine(address: String, line: String) {
        val trimmed = line.trim()
        if (trimmed == "SYSTEM:BKSP") {
            handleBackspace(address)
        } else if (trimmed == "LANG:en") {
            isBangla.value = false
        } else if (trimmed == "LANG:bn") {
            isBangla.value = true
        } else if (trimmed == "Invalid" || trimmed == "SHIFT" || trimmed.startsWith("SYSTEM:")) {
            // Drop control line
        } else {
            handleIncomingChars(address, trimmed)
        }
    }

    private fun handleIncomingChars(address: String, chars: String) {
        if (chars.isEmpty()) return
        val now = System.currentTimeMillis()
        val list = students.value
        var targetStudent: StudentModel? = null
        for (s in list) {
            if (s.deviceAddress == address || (s.isMirror && address == activeStudentDeviceAddress.value)) {
                targetStudent = s
                break
            }
        }

        val timedList = ArrayList<TimedChar>(chars.length)
        for (c in chars) {
            val timed = TimedChar(char = c.toString(), time = now)
            timedList.add(timed)
            // Push to teacher student
            targetStudent?.let {
                it.chars.add(timed)
                it.lastChord = BrailleDict.charToChord[c.toString()] ?: 0
            }
        }

        // Push batch to student view if matching or active
        if (address == activeStudentDeviceAddress.value || activeStudentDeviceAddress.value == null) {
            appendStudentChars(timedList)
        } else {
            updateTotalChars()
        }
    }

    fun handleBackspace(address: String? = null) {
        // Remove last character from student view
        val curList = studentChars.value.toMutableList()
        if (curList.isNotEmpty()) {
            curList.removeAt(curList.size - 1)
            studentChars.value = curList
        }
        val curRecent = studentRecentChars.value.toMutableList()
        if (curRecent.isNotEmpty()) {
            curRecent.removeAt(curRecent.size - 1)
            studentRecentChars.value = curRecent
        }

        // Also remove from matching teacher student feed
        val list = students.value
        for (s in list) {
            if (address == null || s.deviceAddress == address || (s.isMirror && address == activeStudentDeviceAddress.value)) {
                if (s.chars.isNotEmpty()) {
                    s.chars.removeAt(s.chars.size - 1)
                }
            }
        }
        students.value = list.toList()
        updateTotalChars()
    }

    fun appendStudentChar(timed: TimedChar) {
        appendStudentChars(listOf(timed))
    }

    fun appendStudentChars(timedList: List<TimedChar>) {
        if (timedList.isEmpty()) return
        val curList = studentChars.value.toMutableList()
        curList.addAll(timedList)
        studentChars.value = curList

        val curRecent = studentRecentChars.value.toMutableList()
        curRecent.addAll(timedList)
        while (curRecent.size > 80) {
            curRecent.removeAt(0)
        }
        studentRecentChars.value = curRecent
        if (studentTranslateResult.value != null) {
            studentTranslateResult.value = null
        }
        if (studentTranslateError.value != null) {
            studentTranslateError.value = null
        }
        updateTotalChars()
    }

    fun toggleTheme() {
        val newDark = !isDarkTheme.value
        isDarkTheme.value = newDark
        settingsStore.setTheme(if (newDark) "dark" else "light")
    }

    fun toggleDot(dotIndex: Int) {
        val set = studentPressedDots.value.toMutableSet()
        if (set.contains(dotIndex)) {
            set.remove(dotIndex)
        } else {
            set.add(dotIndex)
        }
        studentPressedDots.value = set

        // Compute chord integer (dot 1 = bit 0, dot 2 = bit 1, etc.)
        var c = 0
        for (d in set) {
            c = c or (1 shl (d - 1))
        }
        studentChord.value = c
    }

    fun commitChord() {
        val chord = studentChord.value
        if (chord > 0) {
            val resolved = BrailleDict.resolveChord(chord, isBangla.value, shiftActive.value)
            if (resolved != null) {
                for (ch in resolved) {
                    appendStudentChar(TimedChar(ch.toString(), System.currentTimeMillis()))
                }
                // Feed to mirrored student in teacher roster if exists
                val mirror = students.value.find { it.isMirror }
                mirror?.let {
                    for (ch in resolved) {
                        it.chars.add(TimedChar(ch.toString(), System.currentTimeMillis()))
                    }
                    it.lastChord = chord
                }
            }
            studentPressedDots.value = emptySet()
            studentChord.value = 0
        }
    }

    fun addSpace() {
        appendStudentChar(TimedChar(" ", System.currentTimeMillis()))
        val mirror = students.value.find { it.isMirror }
        mirror?.let {
            it.chars.add(TimedChar(" ", System.currentTimeMillis()))
        }
    }

    fun toggleLanguage() {
        val next = !isBangla.value
        isBangla.value = next
    }

    fun toggleShift() {
        shiftActive.value = !shiftActive.value
    }

    fun clearStudentStream() {
        translateJob?.cancel()
        studentChars.value = emptyList()
        studentRecentChars.value = emptyList()
        studentTranslateResult.value = null
        studentTranslateError.value = null
    }

    fun setStudentTranslateTarget(target: String) {
        studentTranslateTarget.value = target
        val text = studentChars.value.joinToString("") { it.char }
        if (text.isNotBlank()) {
            translateStudentStream(target)
        }
    }

    fun translateStudentStream(target: String = studentTranslateTarget.value) {
        val text = studentChars.value.joinToString("") { it.char }
        if (text.isBlank()) {
            studentTranslateResult.value = null
            studentTranslateError.value = "Nothing to translate"
            return
        }

        studentTranslateTarget.value = target
        studentTranslateError.value = null
        isStudentTranslating.value = true

        translateJob?.cancel()
        translateJob = viewModelScope.launch {
            val res = BBTranslate.translate(text, target)
            isStudentTranslating.value = false
            if (res.ok) {
                studentTranslateResult.value = res
                studentTranslateError.value = null
            } else {
                studentTranslateResult.value = null
                studentTranslateError.value = res.error
            }
        }
    }

    // Teacher Management
    fun addStudent(name: String, baud: Int, deviceAddress: String?) {
        viewModelScope.launch {
            val entity = StudentEntity(
                name = name,
                connType = "bluetooth",
                baud = baud,
                deviceAddress = deviceAddress,
                isMirror = false
            )
            studentDao.insertStudent(entity)
            if (!deviceAddress.isNullOrEmpty()) {
                settingsStore.setAssignment(name, deviceAddress)
                // Connect if device scanned
                val service = BleProxyService.instance
                val device = scannedDevices.value.find { it.address == deviceAddress }?.device
                if (service != null && device != null) {
                    service.connectDevice(device, name)
                }
            }
        }
    }

    fun removeStudent(student: StudentModel) {
        viewModelScope.launch {
            studentDao.deleteStudent(student.id)
            settingsStore.setAssignment(student.name, null)
            student.deviceAddress?.let {
                BleProxyService.instance?.disconnectDevice(it)
            }
        }
    }

    fun clearStudent(student: StudentModel) {
        student.chars.clear()
        student.lastChord = 0
        students.value = students.value.toList()
        updateTotalChars()
    }

    fun testStudent(student: StudentModel) {
        val testString = "hello বাংলা"
        viewModelScope.launch(Dispatchers.Default) {
            for (ch in testString) {
                val timed = TimedChar(ch.toString(), System.currentTimeMillis())
                student.chars.add(timed)
                student.lastChord = BrailleDict.charToChord[ch.toString()] ?: 0
                updateTotalChars()
                delay(200)
            }
        }
    }

    fun createMirrorStudent() {
        viewModelScope.launch {
            val exists = students.value.any { it.isMirror }
            if (exists) return@launch
            val entity = StudentEntity(
                name = "Student View (Mirror)",
                connType = "bluetooth",
                baud = 115200,
                deviceAddress = activeStudentDeviceAddress.value,
                isMirror = true
            )
            studentDao.insertStudent(entity)
        }
    }

    fun clearAllFeeds() {
        for (s in students.value) {
            s.chars.clear()
            s.lastChord = 0
        }
        studentChars.value = emptyList()
        studentRecentChars.value = emptyList()
        students.value = students.value.toList()
        updateTotalChars()
    }

    private fun updateTotalChars() {
        var sum = 0
        val currentStudents = students.value
        for (s in currentStudents) {
            sum += s.chars.size
        }
        val newTotal = sum.coerceAtLeast(studentChars.value.size)
        if (totalCharsAllStudents.value != newTotal) {
            totalCharsAllStudents.value = newTotal
        }
    }

    fun exportSingleStudent(student: StudentModel, context: Context) {
        val blocks = AutoFormatter.format(student.chars)
        val plainText = AutoFormatter.toText(blocks)
        val jsonArray = JSONArray()
        for (b in blocks) {
            val obj = JSONObject()
            obj.put("type", b.type)
            obj.put("text", b.text)
            obj.put("time", b.time)
            obj.put("level", b.level)
            jsonArray.put(obj)
        }

        val export = ExportEntity(
            id = "ex_" + UUID.randomUUID().toString().take(8),
            title = student.name,
            mode = "Teacher App",
            source = "student",
            charsCount = student.chars.size,
            blocksJson = jsonArray.toString(),
            created = System.currentTimeMillis(),
            studentName = student.name,
            connInfo = "Bluetooth · ${student.deviceAddress ?: "Virtual"}"
        )

        viewModelScope.launch {
            exportDao.insertExport(export)
            Toast.makeText(context, "${student.name} export saved to Exports", Toast.LENGTH_SHORT).show()
        }
    }

    fun exportAllStudents(context: Context) {
        val allChars = mutableListOf<TimedChar>()
        for (s in students.value) {
            allChars.addAll(s.chars)
        }
        allChars.sortBy { it.time }

        val blocks = AutoFormatter.format(allChars)
        val jsonArray = JSONArray()
        for (b in blocks) {
            val obj = JSONObject()
            obj.put("type", b.type)
            obj.put("text", b.text)
            obj.put("time", b.time)
            obj.put("level", b.level)
            jsonArray.put(obj)
        }

        val export = ExportEntity(
            id = "ex_" + UUID.randomUUID().toString().take(8),
            title = "Class Roster (${students.value.size} students)",
            mode = if (currentMode.value == AppMode.EXAM) "Exam" else "Teacher App",
            source = "class",
            charsCount = allChars.size,
            blocksJson = jsonArray.toString(),
            created = System.currentTimeMillis(),
            studentName = "All Students",
            connInfo = "${students.value.size} student devices"
        )

        viewModelScope.launch {
            exportDao.insertExport(export)
            Toast.makeText(context, "Class export saved to Exports", Toast.LENGTH_SHORT).show()
        }
    }

    fun savePreviewToExports(student: StudentModel, context: Context) {
        exportSingleStudent(student, context)
    }

    fun deleteExport(export: ExportEntity) {
        viewModelScope.launch {
            exportDao.deleteExport(export.id)
        }
    }

    fun clearAllExports() {
        viewModelScope.launch {
            exportDao.deleteAll()
        }
    }

    fun parseBlocks(blocksJson: String): List<FormattedBlock> {
        val list = mutableListOf<FormattedBlock>()
        try {
            val arr = JSONArray(blocksJson)
            for (i in 0 until arr.length()) {
                val obj = arr.getJSONObject(i)
                list.add(
                    FormattedBlock(
                        type = obj.optString("type", "para"),
                        text = obj.optString("text", ""),
                        time = obj.optLong("time", 0L),
                        level = obj.optInt("level", 0)
                    )
                )
            }
        } catch (e: Exception) {
            // Ignore
        }
        return list
    }

    fun connectScannedDevice(device: ScannedBleDevice) {
        val service = BleProxyService.instance
        if (service != null) {
            activeStudentDeviceAddress.value = device.address
            service.connectDevice(device.device)
            showBleScanDialog.value = false
        }
    }

    fun disconnectStudentDevice() {
        val addr = activeStudentDeviceAddress.value
        if (addr != null) {
            BleProxyService.instance?.disconnectDevice(addr)
            isStudentDeviceConnected.value = false
        }
    }
}
