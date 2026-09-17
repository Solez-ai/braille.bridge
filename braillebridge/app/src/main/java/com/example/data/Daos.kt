package com.example.data

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import kotlinx.coroutines.flow.Flow

@Dao
interface StudentDao {
    @Query("SELECT * FROM students ORDER BY id ASC")
    fun getAllStudents(): Flow<List<StudentEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertStudent(student: StudentEntity): Long

    @Update
    suspend fun updateStudent(student: StudentEntity)

    @Query("DELETE FROM students WHERE id = :id")
    suspend fun deleteStudent(id: Long)

    @Query("DELETE FROM students")
    suspend fun deleteAll()
}

@Dao
interface ExportDao {
    @Query("SELECT * FROM exports ORDER BY created DESC")
    fun getAllExports(): Flow<List<ExportEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertExport(export: ExportEntity)

    @Query("DELETE FROM exports WHERE id = :id")
    suspend fun deleteExport(id: String)

    @Query("DELETE FROM exports")
    suspend fun deleteAll()

    @Query("SELECT COUNT(*) FROM exports")
    suspend fun count(): Int
}
