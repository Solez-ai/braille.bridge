package com.example.protocol

data class LanguageItem(
    val code: String,
    val name: String,
    val countryCode: String
) {
    val flag: String
        get() = Translate.countryCodeToFlag(countryCode)

    val displayName: String
        get() = if (flag.isNotEmpty()) "$flag $name" else name
}

object Translate {

    fun countryCodeToFlag(countryCode: String): String {
        if (countryCode.length != 2) return ""
        val code = countryCode.uppercase()
        val firstChar = Character.codePointAt(code, 0)
        val secondChar = Character.codePointAt(code, 1)
        if (firstChar !in 0x41..0x5A || secondChar !in 0x41..0x5A) return ""
        val flagFirst = 0x1F1E6 + (firstChar - 0x41)
        val flagSecond = 0x1F1E6 + (secondChar - 0x41)
        return String(Character.toChars(flagFirst)) + String(Character.toChars(flagSecond))
    }

    val LANGUAGES: List<LanguageItem> = listOf(
        LanguageItem("af", "Afrikaans", "za"),
        LanguageItem("sq", "Albanian", "al"),
        LanguageItem("am", "Amharic", "et"),
        LanguageItem("ar", "Arabic", "sa"),
        LanguageItem("hy", "Armenian", "am"),
        LanguageItem("as", "Assamese", "in"),
        LanguageItem("ay", "Aymara", "bo"),
        LanguageItem("az", "Azerbaijani", "az"),
        LanguageItem("bm", "Bambara", "ml"),
        LanguageItem("eu", "Basque", "es"),
        LanguageItem("be", "Belarusian", "by"),
        LanguageItem("bn", "Bengali", "bd"),
        LanguageItem("bho", "Bhojpuri", "in"),
        LanguageItem("bs", "Bosnian", "ba"),
        LanguageItem("bg", "Bulgarian", "bg"),
        LanguageItem("ca", "Catalan", "es"),
        LanguageItem("ceb", "Cebuano", "ph"),
        LanguageItem("zh-CN", "Chinese (Simplified)", "cn"),
        LanguageItem("zh-TW", "Chinese (Traditional)", "tw"),
        LanguageItem("co", "Corsican", "fr"),
        LanguageItem("hr", "Croatian", "hr"),
        LanguageItem("cs", "Czech", "cz"),
        LanguageItem("da", "Danish", "dk"),
        LanguageItem("dv", "Dhivehi", "mv"),
        LanguageItem("doi", "Dogri", "in"),
        LanguageItem("nl", "Dutch", "nl"),
        LanguageItem("en", "English", "gb"),
        LanguageItem("eo", "Esperanto", "eu"),
        LanguageItem("et", "Estonian", "ee"),
        LanguageItem("ee", "Ewe", "gh"),
        LanguageItem("fil", "Filipino (Tagalog)", "ph"),
        LanguageItem("fi", "Finnish", "fi"),
        LanguageItem("fr", "French", "fr"),
        LanguageItem("fy", "Frisian", "nl"),
        LanguageItem("gl", "Galician", "es"),
        LanguageItem("ka", "Georgian", "ge"),
        LanguageItem("de", "German", "de"),
        LanguageItem("el", "Greek", "gr"),
        LanguageItem("gn", "Guarani", "py"),
        LanguageItem("gu", "Gujarati", "in"),
        LanguageItem("ht", "Haitian Creole", "ht"),
        LanguageItem("ha", "Hausa", "ng"),
        LanguageItem("haw", "Hawaiian", "us"),
        LanguageItem("he", "Hebrew", "il"),
        LanguageItem("hi", "Hindi", "in"),
        LanguageItem("hmn", "Hmong", "la"),
        LanguageItem("hu", "Hungarian", "hu"),
        LanguageItem("is", "Icelandic", "is"),
        LanguageItem("ig", "Igbo", "ng"),
        LanguageItem("ilo", "Ilocano", "ph"),
        LanguageItem("id", "Indonesian", "id"),
        LanguageItem("ga", "Irish", "ie"),
        LanguageItem("it", "Italian", "it"),
        LanguageItem("ja", "Japanese", "jp"),
        LanguageItem("jv", "Javanese", "id"),
        LanguageItem("kn", "Kannada", "in"),
        LanguageItem("kk", "Kazakh", "kz"),
        LanguageItem("km", "Khmer", "kh"),
        LanguageItem("rw", "Kinyarwanda", "rw"),
        LanguageItem("gom", "Konkani", "in"),
        LanguageItem("ko", "Korean", "kr"),
        LanguageItem("kri", "Krio", "sl"),
        LanguageItem("ku", "Kurdish (Kurmanji)", "tr"),
        LanguageItem("ckb", "Kurdish (Sorani)", "iq"),
        LanguageItem("ky", "Kyrgyz", "kg"),
        LanguageItem("lo", "Lao", "la"),
        LanguageItem("la", "Latin", "va"),
        LanguageItem("lv", "Latvian", "lv"),
        LanguageItem("ln", "Lingala", "cd"),
        LanguageItem("lt", "Lithuanian", "lt"),
        LanguageItem("lg", "Luganda", "ug"),
        LanguageItem("lb", "Luxembourgish", "lu"),
        LanguageItem("mk", "Macedonian", "mk"),
        LanguageItem("mai", "Maithili", "in"),
        LanguageItem("mg", "Malagasy", "mg"),
        LanguageItem("ms", "Malay", "my"),
        LanguageItem("ml", "Malayalam", "in"),
        LanguageItem("mt", "Maltese", "mt"),
        LanguageItem("mi", "Maori", "nz"),
        LanguageItem("mr", "Marathi", "in"),
        LanguageItem("mni-Mtei", "Meiteilon (Manipuri)", "in"),
        LanguageItem("lus", "Mizo", "in"),
        LanguageItem("mn", "Mongolian", "mn"),
        LanguageItem("my", "Myanmar (Burmese)", "mm"),
        LanguageItem("ne", "Nepali", "np"),
        LanguageItem("no", "Norwegian", "no"),
        LanguageItem("ny", "Nyanja (Chichewa)", "mw"),
        LanguageItem("or", "Odia (Oriya)", "in"),
        LanguageItem("om", "Oromo", "et"),
        LanguageItem("ps", "Pashto", "af"),
        LanguageItem("fa", "Persian", "ir"),
        LanguageItem("pl", "Polish", "pl"),
        LanguageItem("pt", "Portuguese", "pt"),
        LanguageItem("pa", "Punjabi", "in"),
        LanguageItem("qu", "Quechua", "pe"),
        LanguageItem("ro", "Romanian", "ro"),
        LanguageItem("ru", "Russian", "ru"),
        LanguageItem("sm", "Samoan", "ws"),
        LanguageItem("sa", "Sanskrit", "in"),
        LanguageItem("gd", "Scots Gaelic", "gb"),
        LanguageItem("nso", "Sepedi", "za"),
        LanguageItem("sr", "Serbian", "rs"),
        LanguageItem("st", "Sesotho", "ls"),
        LanguageItem("sn", "Shona", "zw"),
        LanguageItem("sd", "Sindhi", "pk"),
        LanguageItem("si", "Sinhala", "lk"),
        LanguageItem("sk", "Slovak", "sk"),
        LanguageItem("sl", "Slovenian", "si"),
        LanguageItem("so", "Somali", "so"),
        LanguageItem("es", "Spanish", "es"),
        LanguageItem("su", "Sundanese", "id"),
        LanguageItem("sw", "Swahili", "ke"),
        LanguageItem("sv", "Swedish", "se"),
        LanguageItem("tg", "Tajik", "tj"),
        LanguageItem("ta", "Tamil", "in"),
        LanguageItem("tt", "Tatar", "ru"),
        LanguageItem("te", "Telugu", "in"),
        LanguageItem("th", "Thai", "th"),
        LanguageItem("ti", "Tigrinya", "er"),
        LanguageItem("ts", "Tsonga", "za"),
        LanguageItem("tr", "Turkish", "tr"),
        LanguageItem("tk", "Turkmen", "tm"),
        LanguageItem("ak", "Twi (Akan)", "gh"),
        LanguageItem("uk", "Ukrainian", "ua"),
        LanguageItem("ur", "Urdu", "pk"),
        LanguageItem("ug", "Uyghur", "cn"),
        LanguageItem("uz", "Uzbek", "uz"),
        LanguageItem("vi", "Vietnamese", "vn"),
        LanguageItem("cy", "Welsh", "gb"),
        LanguageItem("xh", "Xhosa", "za"),
        LanguageItem("yi", "Yiddish", "il"),
        LanguageItem("yo", "Yoruba", "ng"),
        LanguageItem("zu", "Zulu", "za")
    )

    fun name(code: String): String {
        val clean = code.trim().lowercase()
        val exact = LANGUAGES.find { it.code.lowercase() == clean }
        if (exact != null) return exact.name
        val prefix = LANGUAGES.find { it.code.lowercase().startsWith(clean) || clean.startsWith(it.code.lowercase()) }
        return prefix?.name ?: code
    }

    fun flag(code: String): String {
        val clean = code.trim().lowercase()
        val exact = LANGUAGES.find { it.code.lowercase() == clean }
        if (exact != null) return exact.flag
        val prefix = LANGUAGES.find { it.code.lowercase().startsWith(clean) || clean.startsWith(it.code.lowercase()) }
        return prefix?.flag ?: ""
    }

    fun displayName(code: String): String {
        val clean = code.trim().lowercase()
        val exact = LANGUAGES.find { it.code.lowercase() == clean }
        if (exact != null) return exact.displayName
        val prefix = LANGUAGES.find { it.code.lowercase().startsWith(clean) || clean.startsWith(it.code.lowercase()) }
        return prefix?.displayName ?: code
    }

    fun detectLanguage(text: String): String {
        for (ch in text) {
            val cp = ch.code
            when {
                cp in 0x0980..0x09FF -> return "bn" // Bengali
                cp in 0x0900..0x097F -> return "hi" // Hindi / Devanagari
                cp in 0x0600..0x06FF || cp in 0x0750..0x077F -> return "ar" // Arabic
                cp in 0x0A00..0x0A7F -> return "pa" // Punjabi / Gurmukhi
                cp in 0x0A80..0x0AFF -> return "gu" // Gujarati
                cp in 0x0B00..0x0B7F -> return "or" // Odia
                cp in 0x0B80..0x0BFF -> return "ta" // Tamil
                cp in 0x0C00..0x0C7F -> return "te" // Telugu
                cp in 0x0C80..0x0CFF -> return "kn" // Kannada
                cp in 0x0D00..0x0D7F -> return "ml" // Malayalam
                cp in 0x0D80..0x0DFF -> return "si" // Sinhala
                cp in 0x0E00..0x0E7F -> return "th" // Thai
                cp in 0x0E80..0x0EFF -> return "lo" // Lao
                cp in 0x0F00..0x0FFF -> return "bo" // Tibetan
                cp in 0x1000..0x109F -> return "my" // Myanmar
                cp in 0x1780..0x17FF -> return "km" // Khmer
                cp in 0x0400..0x04FF -> return "ru" // Cyrillic
                cp in 0x0370..0x03FF -> return "el" // Greek
                cp in 0x0590..0x05FF -> return "he" // Hebrew
                cp in 0x3040..0x309F || cp in 0x30A0..0x30FF -> return "ja" // Japanese
                cp in 0xAC00..0xD7AF || cp in 0x1100..0x11FF -> return "ko" // Korean
                cp in 0x4E00..0x9FFF -> return "zh-CN" // Chinese
            }
        }
        return "en"
    }
}
