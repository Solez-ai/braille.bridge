package com.example.data

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "students")
data class StudentEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val name: String,
    val connType: String = "bluetooth",
    val baud: Int = 115200,
    val deviceAddress: String? = null,
    val isMirror: Boolean = false
)
