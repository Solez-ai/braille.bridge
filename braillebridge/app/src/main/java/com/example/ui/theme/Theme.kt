package com.example.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val DarkColorScheme = darkColorScheme(
    primary = Gold,
    onPrimary = BgDark,
    primaryContainer = GoldDark,
    onPrimaryContainer = GoldLight,
    secondary = AccentBlue,
    onSecondary = Color.White,
    tertiary = AccentTeal,
    background = BgDark,
    onBackground = TextPrimary,
    surface = BgPanel,
    onSurface = TextPrimary,
    surfaceVariant = BgSurface,
    onSurfaceVariant = TextSecondary,
    error = AccentRed,
    onError = Color.White
)

private val LightColorScheme = lightColorScheme(
    primary = Gold,
    onPrimary = Color.White,
    primaryContainer = GoldLight,
    onPrimaryContainer = LightTextPrimary,
    secondary = AccentBlue,
    onSecondary = Color.White,
    tertiary = AccentTeal,
    background = LightBgDark,
    onBackground = LightTextPrimary,
    surface = LightBgPanel,
    onSurface = LightTextPrimary,
    surfaceVariant = LightBgSurface,
    onSurfaceVariant = LightTextSecondary,
    error = AccentRed,
    onError = Color.White
)

@Composable
fun BrailleBridgeTheme(
    darkTheme: Boolean = true,
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
