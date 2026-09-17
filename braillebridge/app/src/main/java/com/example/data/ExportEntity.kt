package com.example.data

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "exports")
data class ExportEntity(
    @PrimaryKey val id: String,
    val title: String,
    val mode: String,
    val source: String,
    val charsCount: Int,
    val blocksJson: String,
    val created: Long,
    val studentName: String? = null,
    val connInfo: String? = null
)
