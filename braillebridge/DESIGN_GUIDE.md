# BrailleBridge Mobile — UI Design & Color Schematic Guide

> Single source of truth for colors, surfaces, and semantic roles in the
> BrailleBridge Android app. Mirrors `app/src/main/java/com/example/ui/theme/Color.kt`.
> Dark theme is the **default and primary** identity; light theme is the
> accessibility alternative.

---

## 1. Brand Principles

1. **Dark-first, high-contrast** — a classroom tool read at a distance and by
   low-vision users. Contrast beats decoration.
2. **Brass & ink identity** — warm gold on deep ink-blue evokes brass braille
   slates and typewriter hardware. Distinct from every default-blue dev tool.
3. **Color = meaning, never decoration.** Gold is interactive, green is
   success/connected, red is error/unset, and nothing else.
4. **Two hues, one story** — the entire UI runs on warm neutrals + gold.
   Cool accents (blue/purple/teal) exist only for chart/category coding.

---

## 2. App Aesthetic & Screen Architecture

**The feel: a writing instrument, not an app.** Think of a brass braille
slate resting on dark paper — quiet, warm, tactile. One job per screen,
generous empty space, big readable type, and color that only ever means
something (see §3). If a screen starts to feel like a dashboard, it's wrong.

### The Tabs — complete information architecture

The app has **exactly four tabs** in the bottom navigation, in this fixed
order. The bar itself: `BgPanel` background, active tab in **Gold**, inactive
tabs in `TextMuted`. There is no fifth tab, no side menu, no settings gear.

| # | Tab | The one job |
|---|---|---|
| 1 | **Write** | Write with BrailleBridge, see the text, send it to the teacher |
| 2 | **Teacher** | Add students — nothing else |
| 3 | **Exports** | Review saved exports — nothing else |
| 4 | **Account** | The teacher's profile (Samin Yeasar) |

Anything not written below does **not** get a tab, a button, or a settings
row. No recent-character strips, no Google Translate bars, no diagnostics
consoles, no on-screen dot keyboards, no exam mode — just what is listed here.

#### Tab 1 — Write (the first screen)

A single vertical flow, centered, in this exact order — **three elements,
nothing else:**

1. **Wordmark** — "BrailleBridge" in `headlineLarge` Serif, Gold, centered at
   the top. This is the only brand moment in the app.
2. **The writing field** — one large, **selectable** text area filling most of
   the screen. Paper-look panel (`BgSurface`), `TextPrimary` Serif at
   `titleLarge`, blinking Gold caret. Braille input lands here as characters;
   the user can tap, long-press, select and copy the text like any text field.
   Empty state: one muted centered line — "Write with your BrailleBridge".
3. **Send to Teacher** — full-width Gold `primary` button directly under the
   field. The screen's single call to action.

Not on this tab: translate controls, character history, dot-pad, diagnostics,
settings. If it isn't one of the three elements above, it doesn't render.

#### Tab 2 — Teacher (add students ONLY)

Scope is exactly one job: **adding a student.**

- Roster list of added students (name + connection chip)
- **Add Student** button → dialog: name + BLE device picker
- Empty state: one calm prompt — "Add your first student"

Not on this tab: feeds, analytics, test tools, exports. If it isn't "add a
student," it doesn't live here.

#### Tab 3 — Exports (review saved work)

Where every export lands after the teacher saves it — **a read-and-review
library, nothing else.**

- List of saved exports as cards: title, date, source, character count
- Tapping a card opens the document **auto-formatted**: titles, headings,
  paragraph spacing and structure detected and rendered cleanly
- Swipe/long-press to delete an export

Standard card recipe, no new colors. Not on this tab: editing tools, analytics.

#### Tab 4 — Account

The teacher's identity card: avatar, name (**Samin Yeasar**), role, and light
session stats (students added, characters written). A read-only profile —
no settings maze.

---

## 3. Core Palette — Dark (Default)

### Backgrounds (ink blue, darkest → lightest)

| Token | Hex | Role |
|---|---|---|
| `BgDark` | `#0F111A` | App background, behind everything |
| `BgPanel` | `#161822` | Top bar, bottom nav, large panels |
| `BgCard` | `#1C1F2E` | Cards resting on the background |
| `BgSurface` | `#242738` | Elevated surfaces: inputs, text area, chips |
| `BgHover` | `#2D3044` | Hover/pressed state on any surface |

**Elevation rule:** things get *lighter* as they get closer. Never place a
darker surface on a lighter one.

### Text

| Token | Hex | Role |
|---|---|---|
| `TextPrimary` | `#E8E6E0` | Headings, live output, primary body |
| `TextSecondary` | `#A8A4A0` | Labels, secondary body, values |
| `TextMuted` | `#6A6A7A` | Placeholder text, disabled states, hints |

**Contrast:** all three pass WCAG AA on `BgSurface`. Never use `TextMuted`
for anything a student must read.

### Brand — Gold (the identity hue)

| Token | Hex | Role |
|---|---|---|
| `Gold` | `#C49A4A` | Primary: buttons, active nav, links, caret, highlights |
| `GoldLight` | `#DBB86A` | Gradient top on active braille dots, hover on gold |
| `GoldDark` | `#A07828` | Gradient bottom on active dots, pressed gold |

**Gold gradient for pressed/active dots:** `GoldLight → GoldDark` at 145° —
matches the website (`style.css`) exactly.

### Status Accents

| Token | Hex | Use ONLY for |
|---|---|---|
| `AccentGreen` | `#5AB85A` | Connected badges, success, "বাংলা ON", data-flowing logs |
| `AccentRed` | `#D45A5A` | Errors, destructive actions, "EN / shift off" LEDs |
| `AccentBlue` | `#5A8AE0` | Charts only — category color #1 |
| `AccentPurple` | `#8A6AD4` | Charts only — category color #2 |
| `AccentTeal` | `#4AC8B8` | Charts / tertiary theme slot |

**Forbidden:** blue as button color, green as brand color, purple/teal
anywhere outside data visualization. If a new screen needs a new color,
the palette is wrong — extend semantics, not hues.

### Alpha Rules

- Active/connected chip backgrounds: status color `@ 15–25%`, text/icon full color
- Highlighted panels (selected export, etc.): `primary @ 8%` background + `@ 30%` border
- Error surfaces: `error @ 10%` background + `@ 40%` border

---

## 4. Light Theme (Accessibility Alternative)

| Dark | Light | Token |
|---|---|---|
| `BgDark #0F111A` | `LightBgDark #F4F3F0` | App background |
| `BgPanel #161822` | `LightBgPanel #FFFFFF` | Bars & panels |
| `BgCard #1C1F2E` | `LightBgCard #FAF9F6` | Cards |
| `BgSurface #242738` | `LightBgSurface #EFEDE8` | Elevated surfaces |
| `BgHover #2D3044` | `LightBgHover #E6E3DC` | Hover/pressed |
| `TextPrimary #E8E6E0` | `LightTextPrimary #1A1A2E` | Primary text |
| `TextSecondary #A8A4A0` | `LightTextSecondary #4A4A5A` | Secondary text |
| `TextMuted #6A6A7A` | `LightTextMuted #8A8A9A` | Muted text |

**Gold, red, green are shared across both themes** (no `Light` variants) —
`#C49A4A` passes AA on light backgrounds and reads as "burnished brass" on
dark. One accent set = one identity.

---

## 5. Theme → Material 3 Mapping

How raw tokens map to `MaterialTheme` slots (see `Theme.kt`):

| M3 Slot | Dark value | Light value |
|---|---|---|
| `primary` / `onPrimary` | Gold / `BgDark` | Gold / White |
| `primaryContainer` | `GoldDark` | `GoldLight` |
| `secondary` | `AccentBlue` | `AccentBlue` |
| `tertiary` | `AccentTeal` | `AccentTeal` |
| `background` / `onBackground` | `BgDark` / `TextPrimary` | `LightBgDark` / `LightTextPrimary` |
| `surface` / `onSurface` | `BgPanel` / `TextPrimary` | `LightBgPanel` / `LightTextPrimary` |
| `surfaceVariant` / `onSurfaceVariant` | `BgSurface` / `TextSecondary` | `LightBgSurface` / `LightTextSecondary` |
| `error` | `AccentRed` | `AccentRed` |

**Rule for new screens:** consume `MaterialTheme.colorScheme.*` only — never
import raw `Color.kt` values except Gold/Green/Red for status LEDs.

---

## 6. Semantic Cheat Sheet

| Element | Correct treatment |
|---|---|
| Primary button (Send to Teacher, Add Student) | `primary` container, `onPrimary` text |
| Secondary button | `surfaceVariant` container, `onSurface` text |
| Writing field text | `TextPrimary`, Serif, `titleLarge` |
| Writing field caret / selection | `primary` blinking caret, `primary @ 30%` selection handles |
| Empty states (field, roster, library) | `TextMuted`, centered, one calm sentence |
| Student roster row | `BgCard` surface, `onSurface` name, status chip in `labelMedium` |
| Export card | `BgCard`, title `onSurface`, meta `TextSecondary`, Serif preview |
| Auto-formatted export document | Serif body (`bodyLarge`), headings `titleMedium`, `TextPrimary` |
| Account card | `BgPanel`, Gold avatar ring, stats in `TextSecondary` |

---

## 7. Typography (quick reference)

| Token | Font | Size/LH | Use |
|---|---|---|---|
| `headlineLarge` | Serif | 28/34 | **"BrailleBridge" wordmark** |
| `titleLarge` | Serif | 20/26 | Writing field text |
| `titleMedium` | Sans | 16/22 | Card titles, export headings |
| `bodyLarge` | Sans | 16/24 | Export document body |
| `bodyMedium` | Sans | 14/20 | Body, empty-state text |
| `bodySmall` | Sans | 13/18 | Meta text, timestamps |
| `labelLarge` | Sans, SemiBold | 15/20 | All button labels |
| `labelMedium` | Sans, Medium | 13/16 | Chips, status text |
| `labelSmall` | **Monospace** | 12/16 | Section headers |

Never hardcode `fontSize = N.sp` in screens — use tokens so system font
scaling works.

---

## 8. Shape, Spacing, Elevation

- **Corner radius:** 16dp cards · 14dp writing field · 10dp buttons ·
  12–16dp chips
- **Spacing scale:** 4 / 8 / 12 / 16 dp only. Screen padding 16dp.
- **Tap targets:** minimum 48×48dp everywhere, even if visual element is smaller
- **Elevation:** shadows are avoided; surface *lightness* carries depth
  (see elevation rule in §3)
- **Borders:** 1dp `outlineVariant` on all resting cards

---

## 9. Hard Rules (violations = review rejection)

1. Never introduce a color not in `Color.kt`.
2. Never use `AccentBlue/Purple/Teal` outside charts.
3. Never put status color on a background without its alpha recipe (§3).
4. Never hardcode `fontSize`/`Color(0x…)` in a composable.
5. Never place darker surfaces over lighter ones (dark theme).
6. Never rely on color alone to convey state — pair color with a label or icon.
7. The app has exactly four tabs — Write, Teacher, Exports, Account — in that
   fixed order. No fifth tab, no hidden screens.
