package com.example.audio

import android.content.Context
import android.speech.tts.TextToSpeech
import android.util.Log
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.util.Locale

class TTSManager(context: Context) : TextToSpeech.OnInitListener {

    companion object {
        const val TAG = "TTSManager"

        private val SYMBOL_NAMES = mapOf(
            "+" to "plus",
            "-" to "minus",
            "×" to "times",
            "÷" to "divided by",
            "=" to "equals",
            "," to "comma",
            ";" to "semicolon",
            ":" to "colon",
            "." to "period"
        )
    }

    private var tts: TextToSpeech? = TextToSpeech(context.applicationContext, this)

    private val _isTtsReady = MutableStateFlow(false)
    val isTtsReady = _isTtsReady.asStateFlow()

    private val _isBanglaAvailable = MutableStateFlow(false)
    val isBanglaAvailable = _isBanglaAvailable.asStateFlow()

    private val localeEn = Locale.US
    private val localeBn = Locale("bn", "BD")

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            _isTtsReady.value = true
            val t = tts
            if (t != null) {
                val bnRes = t.isLanguageAvailable(localeBn)
                val bnFallback = t.isLanguageAvailable(Locale("bn"))
                val available = (bnRes >= TextToSpeech.LANG_AVAILABLE) || (bnFallback >= TextToSpeech.LANG_AVAILABLE)
                _isBanglaAvailable.value = available
                Log.d(TAG, "TTS initialized successfully. Bangla available: $available")
            }
        } else {
            Log.e(TAG, "TTS initialization failed with status: $status")
            _isTtsReady.value = false
        }
    }

    fun speechTextFor(ch: String): String {
        if (ch.length == 1 && ch[0] in 'A'..'Z') {
            return "capital " + ch.lowercase()
        }
        return SYMBOL_NAMES[ch] ?: ch
    }

    fun speakChar(ch: String, isBangla: Boolean) {
        if (!_isTtsReady.value || tts == null || ch.isBlank()) return
        val targetLocale = if (isBangla) localeBn else localeEn
        try {
            tts?.language = targetLocale
            val textToSpeak = if (isBangla) ch else speechTextFor(ch)
            tts?.speak(textToSpeak, TextToSpeech.QUEUE_FLUSH, null, "char_${System.currentTimeMillis()}")
        } catch (e: Exception) {
            Log.e(TAG, "speakChar failed", e)
        }
    }

    fun speakWord(word: String, isBangla: Boolean) {
        val trimmed = word.trim()
        if (!_isTtsReady.value || tts == null || trimmed.isEmpty()) return
        val targetLocale = if (isBangla) localeBn else localeEn
        try {
            tts?.language = targetLocale
            tts?.speak(trimmed, TextToSpeech.QUEUE_FLUSH, null, "word_${System.currentTimeMillis()}")
        } catch (e: Exception) {
            Log.e(TAG, "speakWord failed", e)
        }
    }

    fun speakText(text: String, isBangla: Boolean) {
        val trimmed = text.trim()
        if (!_isTtsReady.value || tts == null || trimmed.isEmpty()) return
        val targetLocale = if (isBangla) localeBn else localeEn
        try {
            tts?.language = targetLocale
            tts?.speak(trimmed, TextToSpeech.QUEUE_FLUSH, null, "text_${System.currentTimeMillis()}")
        } catch (e: Exception) {
            Log.e(TAG, "speakText failed", e)
        }
    }

    fun shutdown() {
        try {
            tts?.stop()
            tts?.shutdown()
        } catch (e: Exception) {
            Log.e(TAG, "Error shutting down TTS", e)
        }
        tts = null
        _isTtsReady.value = false
    }
}
