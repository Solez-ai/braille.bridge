package com.example.audio

import android.content.Context
import android.media.AudioAttributes
import android.media.MediaPlayer
import android.speech.tts.TextToSpeech
import android.util.Log
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.net.URLEncoder
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
    private var mediaPlayer: MediaPlayer? = null

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

    private fun speakBanglaOnline(text: String) {
        val clean = text.trim()
        if (clean.isEmpty()) return
        try {
            mediaPlayer?.stop()
            mediaPlayer?.release()
            mediaPlayer = null

            val encoded = URLEncoder.encode(clean, "UTF-8")
            val url = "https://translate.google.com/translate_tts?ie=UTF-8&tl=bn&client=tw-ob&q=$encoded"
            val player = MediaPlayer().apply {
                setAudioAttributes(
                    AudioAttributes.Builder()
                        .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                        .setUsage(AudioAttributes.USAGE_ASSISTANCE_ACCESSIBILITY)
                        .build()
                )
                setDataSource(url)
                setOnPreparedListener { it.start() }
                setOnCompletionListener {
                    it.release()
                    if (mediaPlayer === it) mediaPlayer = null
                }
                setOnErrorListener { mp, _, _ ->
                    mp.release()
                    if (mediaPlayer === mp) mediaPlayer = null
                    true
                }
                prepareAsync()
            }
            mediaPlayer = player
        } catch (e: Exception) {
            Log.e(TAG, "Online Bangla TTS playback failed", e)
        }
    }

    fun speakChar(ch: String, isBangla: Boolean) {
        if (ch.isBlank()) return
        val actualIsBangla = isBangla || ch.any { it in '\u0980'..'\u09FF' }
        if (actualIsBangla) {
            if (_isBanglaAvailable.value && tts != null) {
                try {
                    tts?.language = localeBn
                    val res = tts?.speak(ch, TextToSpeech.QUEUE_FLUSH, null, "char_${System.currentTimeMillis()}")
                    if (res == TextToSpeech.ERROR) {
                        speakBanglaOnline(ch)
                    }
                } catch (e: Exception) {
                    speakBanglaOnline(ch)
                }
            } else {
                speakBanglaOnline(ch)
            }
            return
        }

        if (!_isTtsReady.value || tts == null) return
        try {
            tts?.language = localeEn
            val textToSpeak = speechTextFor(ch)
            tts?.speak(textToSpeak, TextToSpeech.QUEUE_FLUSH, null, "char_${System.currentTimeMillis()}")
        } catch (e: Exception) {
            Log.e(TAG, "speakChar failed", e)
        }
    }

    fun speakWord(word: String, isBangla: Boolean) {
        val trimmed = word.trim()
        if (trimmed.isEmpty()) return
        val actualIsBangla = isBangla || trimmed.any { it in '\u0980'..'\u09FF' }
        if (actualIsBangla) {
            if (_isBanglaAvailable.value && tts != null) {
                try {
                    tts?.language = localeBn
                    val res = tts?.speak(trimmed, TextToSpeech.QUEUE_FLUSH, null, "word_${System.currentTimeMillis()}")
                    if (res == TextToSpeech.ERROR) {
                        speakBanglaOnline(trimmed)
                    }
                } catch (e: Exception) {
                    speakBanglaOnline(trimmed)
                }
            } else {
                speakBanglaOnline(trimmed)
            }
            return
        }

        if (!_isTtsReady.value || tts == null) return
        try {
            tts?.language = localeEn
            tts?.speak(trimmed, TextToSpeech.QUEUE_FLUSH, null, "word_${System.currentTimeMillis()}")
        } catch (e: Exception) {
            Log.e(TAG, "speakWord failed", e)
        }
    }

    fun speakText(text: String, isBangla: Boolean) {
        val trimmed = text.trim()
        if (trimmed.isEmpty()) return
        val actualIsBangla = isBangla || trimmed.any { it in '\u0980'..'\u09FF' }
        if (actualIsBangla) {
            if (_isBanglaAvailable.value && tts != null) {
                try {
                    tts?.language = localeBn
                    val res = tts?.speak(trimmed, TextToSpeech.QUEUE_FLUSH, null, "text_${System.currentTimeMillis()}")
                    if (res == TextToSpeech.ERROR) {
                        speakBanglaOnline(trimmed)
                    }
                } catch (e: Exception) {
                    speakBanglaOnline(trimmed)
                }
            } else {
                speakBanglaOnline(trimmed)
            }
            return
        }

        if (!_isTtsReady.value || tts == null) return
        try {
            tts?.language = localeEn
            tts?.speak(trimmed, TextToSpeech.QUEUE_FLUSH, null, "text_${System.currentTimeMillis()}")
        } catch (e: Exception) {
            Log.e(TAG, "speakText failed", e)
        }
    }

    fun shutdown() {
        try {
            mediaPlayer?.stop()
            mediaPlayer?.release()
            mediaPlayer = null
            tts?.stop()
            tts?.shutdown()
        } catch (e: Exception) {
            Log.e(TAG, "Error shutting down TTS", e)
        }
        tts = null
        _isTtsReady.value = false
    }
}

