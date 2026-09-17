package com.example.data

import com.example.protocol.TimedChar
import kotlinx.coroutines.flow.Flow

data class StudentModel(
    val id: Long,
    val name: String,
    val connType: String,
    val baud: Int,
    val deviceAddress: String?,
    val isMirror: Boolean,
    val color: String,
    val chars: MutableList<TimedChar> = mutableListOf(),
    var isConnected: Boolean = false,
    var lastChord: Int = 0
)

val STUDENT_COLORS = listOf(
    "#5a8ae0", "#d45a5a", "#5ab85a", "#c49a4a",
    "#8a6ad4", "#4ac8b8", "#e08a5a", "#5ab8b8"
)

fun getColorForIndex(index: Int): String {
    return STUDENT_COLORS[index % STUDENT_COLORS.size]
}

fun getInitials(name: String): String {
    val parts = name.trim().split("\\s+".toRegex())
    return if (parts.size >= 2) {
        "${parts[0].firstOrNull()?.uppercase() ?: ""}${parts[1].firstOrNull()?.uppercase() ?: ""}"
    } else {
        name.take(2).uppercase()
    }
}

class StudentRepo(
    private val studentDao: StudentDao,
    private val exportDao: ExportDao
) {
    val allStudentEntities: Flow<List<StudentEntity>> = studentDao.getAllStudents()
    val allExports: Flow<List<ExportEntity>> = exportDao.getAllExports()

    suspend fun addStudent(student: StudentEntity): Long {
        return studentDao.insertStudent(student)
    }

    suspend fun deleteStudent(id: Long) {
        studentDao.deleteStudent(id)
    }

    suspend fun saveExport(export: ExportEntity) {
        exportDao.insertExport(export)
    }

    suspend fun deleteExport(id: String) {
        exportDao.deleteExport(id)
    }

    suspend fun deleteAllExports() {
        exportDao.deleteAll()
    }
}
