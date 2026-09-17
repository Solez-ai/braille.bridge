package com.example.protocol

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONArray
import java.net.URLEncoder
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.TimeUnit

data class TranslateResult(
    val ok: Boolean,
    val text: String,
    val detectedLang: String = "",
    val detectedName: String = "",
    val targetLang: String = "",
    val targetName: String = "",
    val error: String = ""
) {
    val feedback: String
        get() {
            if (!ok) return error
            return if (detectedName.isNotEmpty() && targetName.isNotEmpty()) {
                "($detectedName → $targetName)"
            } else if (detectedName.isNotEmpty()) {
                "(detected: $detectedName)"
            } else {
                ""
            }
        }
}

object BBTranslate {
    private val cache = ConcurrentHashMap<String, TranslateResult>()

    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS)
        .build()

    fun hasBengali(text: String): Boolean {
        return text.any { it in '\u0980'..'\u09FF' }
    }

    fun clearCache() {
        cache.clear()
    }

    suspend fun translate(text: String, target: String): TranslateResult = withContext(Dispatchers.IO) {
        val trimmed = text.trim()
        if (trimmed.isEmpty()) {
            return@withContext TranslateResult(
                ok = false,
                text = "",
                targetLang = target,
                targetName = Translate.name(target),
                error = "Nothing to translate"
            )
        }

        val cacheKey = "$target::$trimmed"
        cache[cacheKey]?.let {
            return@withContext it
        }

        // Primary: gtx single endpoint (sl=auto detects ANY source language)
        try {
            val encodedQuery = URLEncoder.encode(trimmed, "UTF-8")
            val url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=$target&dt=t&q=$encodedQuery"
            val request = Request.Builder()
                .url(url)
                .header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
                .build()

            val response = client.newCall(request).execute()
            if (response.isSuccessful) {
                val body = response.body?.string()
                if (body != null) {
                    val jsonArray = JSONArray(body)
                    val segments = jsonArray.optJSONArray(0)
                    if (segments != null) {
                        val sb = StringBuilder()
                        for (i in 0 until segments.length()) {
                            val seg = segments.optJSONArray(i)
                            if (seg != null) {
                                sb.append(seg.optString(0, ""))
                            }
                        }
                        val result = sb.toString()
                        if (result.isNotEmpty()) {
                            var detectedCode = jsonArray.optString(2, "")
                            if (detectedCode.isEmpty() || detectedCode == "null") {
                                detectedCode = Translate.detectLanguage(trimmed)
                            }
                            val detectedName = Translate.name(detectedCode)
                            val targetName = Translate.name(target)

                            val trResult = TranslateResult(
                                ok = true,
                                text = result,
                                detectedLang = detectedCode,
                                detectedName = detectedName,
                                targetLang = target,
                                targetName = targetName
                            )
                            cache[cacheKey] = trResult
                            return@withContext trResult
                        }
                    }
                }
            }
        } catch (e: Exception) {
            // Fall through to fallback
        }

        // Fallback: v2 shape
        try {
            val encodedQuery = URLEncoder.encode(trimmed, "UTF-8")
            val url = "https://translate.googleapis.com/language/translate/v2?target=$target&q=$encodedQuery"
            val request = Request.Builder()
                .url(url)
                .header("User-Agent", "Mozilla/5.0")
                .build()
            val response = client.newCall(request).execute()
            if (response.isSuccessful) {
                val body = response.body?.string()
                if (body != null) {
                    val json = org.json.JSONObject(body)
                    val data = json.optJSONObject("data")
                    val translations = data?.optJSONArray("translations")
                    val first = translations?.optJSONObject(0)
                    val translatedText = first?.optString("translatedText")
                    if (!translatedText.isNullOrEmpty()) {
                        val detectedCode = first.optString("detectedSourceLanguage").ifEmpty {
                            Translate.detectLanguage(trimmed)
                        }
                        val trResult = TranslateResult(
                            ok = true,
                            text = translatedText,
                            detectedLang = detectedCode,
                            detectedName = Translate.name(detectedCode),
                            targetLang = target,
                            targetName = Translate.name(target)
                        )
                        cache[cacheKey] = trResult
                        return@withContext trResult
                    }
                }
            }
        } catch (e: Exception) {
            // Ignore
        }

        TranslateResult(
            ok = false,
            text = "",
            targetLang = target,
            targetName = Translate.name(target),
            error = "Translation unavailable (check network connection)"
        )
    }
}

