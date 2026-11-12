"""BrailleBridge protocol module — Braille dictionary, chord resolver,
Learner chord-sequence decoder, Google Translate bridge, and Speech Engine.
Mirrors braile/braile.ino and Android BrailleDict.kt 100%.
"""
import json
import re
import subprocess
import sys
import threading
import urllib.parse
import urllib.request

# 6-dot Bharati + English Braille dictionary (dot 1 = bit 0 ... dot 6 = bit 5)
BRAILLE_DICT = [
    (0b000001, 'a', 'অ'),
    (0b000011, 'b', 'ব'),
    (0b001001, 'c', 'চ'),
    (0b011001, 'd', 'দ'),
    (0b010001, 'e', 'এ'),
    (0b001011, 'f', None),
    (0b011011, 'g', 'গ'),
    (0b010011, 'h', 'হ'),
    (0b001000, 'i', '্'),
    (0b011010, 'j', 'জ'),
    (0b000101, 'k', 'ক'),
    (0b000111, 'l', 'ল'),
    (0b001101, 'm', 'ম'),
    (0b011101, 'n', 'ন'),
    (0b010101, 'o', 'ও'),
    (0b001111, 'p', 'প'),
    (0b011111, 'q', 'ক্ষ'),
    (0b010111, 'r', 'র'),
    (0b001100, 's', 'ঐ'),
    (0b011100, 't', 'আ'),
    (0b100101, 'u', 'উ'),
    (0b100111, 'v', 'ৱ'),
    (0b111010, 'w', None),
    (0b101101, 'x', 'য'),
    (0b111101, 'y', 'য'),
    (0b110101, 'z', 'ড়'),
    (0b001010, None, 'ই'),
    (0b010010, None, 'ঞ'),
    (0b001110, None, 'স'),
    (0b111111, None, 'ঢ'),
    (0b100001, None, 'ছ'),
    (0b100011, None, 'ঘ'),
    (0b011000, None, 'ভ'),
    (0b111001, None, 'থ'),
    (0b110110, None, 'ঠ'),
    (0b101010, None, 'ঔ'),
    (0b010110, None, 'ফ'),
    (0b110100, None, 'ঝ'),
    (0b101011, None, 'ড'),
    (0b010100, None, 'ঈ'),
    (0b011110, None, 'ত'),
    (0b101000, None, 'খ'),
    (0b101100, None, 'ঙ'),
    (0b111110, None, 'ট'),
    (0b101110, None, 'ধ'),
    (0b111100, None, 'ণ'),
    (0b110011, None, 'ঊ'),
    (0b101111, None, 'ষ'),
    (0b110001, None, 'শ'),
    (0b110000, None, 'ং'),
    (0b010000, None, 'ঁ'),
    (0b100110, None, 'ি'),
    (0b110010, None, 'ূ'),
    (0b100010, None, 'স'),
]

NUMBER_CHORDS = [
    0b000001, 0b000011, 0b001001, 0b011001, 0b010001,
    0b001011, 0b011011, 0b010011, 0b001000, 0b011010,
]
NUMBER_MAP = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']

SHIFT_SYMBOLS = [
    (0b010110, '+'),
    (0b100100, '-'),
    (0b100110, '×'),
    (0b110110, '='),
    (0b001100, '÷'),
    (0b000010, ','),
    (0b000110, ';'),
    (0b010010, ':'),
    (0b110010, '.'),
]

BANGLA_SHIFT_MAP = [
    (0b000001, None),
    (0b011100, 'া'),
    (0b001010, 'ি'),
    (0b010100, 'ী'),
    (0b100101, 'ু'),
    (0b110011, 'ূ'),
    (0b010001, 'ে'),
    (0b001100, 'ৈ'),
    (0b010101, 'ো'),
    (0b101010, 'ৌ'),
]

CHAR_TO_CHORD = {}
for _c, _en, _bn in BRAILLE_DICT:
    if _en:
        CHAR_TO_CHORD[_en] = _c
        if len(_en) == 1 and 'a' <= _en <= 'z':
            CHAR_TO_CHORD[_en.upper()] = _c
    if _bn:
        CHAR_TO_CHORD[_bn] = _c
for _i, _num in enumerate(NUMBER_MAP):
    CHAR_TO_CHORD[_num] = NUMBER_CHORDS[_i]
for _c, _sym in SHIFT_SYMBOLS:
    CHAR_TO_CHORD[_sym] = _c
for _c, _kar in BANGLA_SHIFT_MAP:
    if _kar:
        CHAR_TO_CHORD[_kar] = _c


def lookup_chord(chord: int, is_bangla: bool):
    for c, en, bn in BRAILLE_DICT:
        if c == chord:
            return bn if is_bangla else en
    return None


def lookup_number(chord: int):
    if chord in NUMBER_CHORDS:
        return NUMBER_MAP[NUMBER_CHORDS.index(chord)]
    return None


def lookup_shift_symbol(chord: int):
    for c, sym in SHIFT_SYMBOLS:
        if c == chord:
            return sym
    return None


def lookup_bangla_shift(chord: int):
    for c, kar in BANGLA_SHIFT_MAP:
        if c == chord:
            return kar
    return None


def resolve_chord(chord: int, is_bangla: bool, shift: bool, caps_mode: str = 'OFF'):
    """Resolve a 6-bit chord into its output string."""
    if chord <= 0:
        return None
    if shift:
        num = lookup_number(chord)
        if num is not None:
            return num
        sym = lookup_shift_symbol(chord)
        if sym is not None:
            return sym
        if not is_bangla:
            ch = lookup_chord(chord, False)
            if ch and len(ch) == 1 and 'a' <= ch <= 'z':
                return ch.upper()
            return None
        else:
            kar = lookup_bangla_shift(chord)
            if kar is not None:
                return kar
            return lookup_chord(chord, True)
    else:
        res = lookup_chord(chord, is_bangla)
        if res and not is_bangla and caps_mode in ('ONCE', 'LOCK') and len(res) == 1 and 'a' <= res <= 'z':
            return res.upper()
        return res


def chord_dots_list(chord: int):
    return [d + 1 for d in range(6) if (chord & (1 << d))]


# Reverse maps for Learner Chord Sequence Trainer
REVERSE_EN = {}
REVERSE_BN = {}
for _c, _en, _bn in BRAILLE_DICT:
    if _en and _en not in REVERSE_EN:
        REVERSE_EN[_en] = (_c, False, False)
    if _bn and _bn not in REVERSE_BN:
        REVERSE_BN[_bn] = (_c, False, False)
for _i, _d in enumerate(NUMBER_MAP):
    if _d not in REVERSE_EN:
        REVERSE_EN[_d] = (NUMBER_CHORDS[_i], True, False)
    if _d not in REVERSE_BN:
        REVERSE_BN[_d] = (NUMBER_CHORDS[_i], True, False)
for _code in range(26):
    _lc = chr(97 + _code)
    _uc = _lc.upper()
    if _lc in REVERSE_EN:
        _l_chord = REVERSE_EN[_lc][0]
        # Letters a-j with Shift produce numbers 1-0, so uppercase A-J use Dot 6 Capital prefix
        _is_a_to_j = _l_chord in NUMBER_CHORDS
        REVERSE_EN[_uc] = (_l_chord, not _is_a_to_j, _is_a_to_j)
for _c, _sym in SHIFT_SYMBOLS:
    if _sym not in REVERSE_EN:
        REVERSE_EN[_sym] = (_c, True, False)
    if _sym not in REVERSE_BN:
        REVERSE_BN[_sym] = (_c, True, False)
for _c, _kar in BANGLA_SHIFT_MAP:
    if _kar and _kar not in REVERSE_BN:
        REVERSE_BN[_kar] = (_c, True, False)

BANGLA_MULTI = sorted(
    [(bn, c) for c, _, bn in BRAILLE_DICT if bn and len(bn) > 1],
    key=lambda x: -len(x[0])
)


def decode_text_to_steps(text: str, lang: str = 'en'):
    """Decode any English or Bangla string into a sequence of Braille chord steps."""
    steps = []
    rev = REVERSE_BN if lang == 'bn' else REVERSE_EN
    p = 0
    n = len(text)
    while p < n:
        ch = text[p]
        if ch == ' ':
            steps.append({'type': 'space', 'char': 'SPACE', 'chord': 0, 'shift': False, 'cap_prefix': False, 'dots': []})
            p += 1
            continue
        if ch in ('\n', '\r', '\t'):
            p += 1
            continue
        if lang == 'bn':
            hit = None
            for m_txt, m_chord in BANGLA_MULTI:
                if text.startswith(m_txt, p):
                    hit = (m_txt, m_chord)
                    break
            if hit:
                steps.append({
                    'type': 'chord',
                    'char': hit[0],
                    'chord': hit[1],
                    'shift': False,
                    'cap_prefix': False,
                    'dots': chord_dots_list(hit[1]),
                })
                p += len(hit[0])
                continue
        if ch in rev:
            chord, shift, cap_prefix = rev[ch]
            if cap_prefix:
                steps.append({
                    'type': 'chord',
                    'char': '⇪ Cap',
                    'chord': 0b100000,
                    'shift': False,
                    'cap_prefix': True,
                    'dots': [6],
                })
            steps.append({
                'type': 'chord',
                'char': ch,
                'chord': chord,
                'shift': shift,
                'cap_prefix': False,
                'dots': chord_dots_list(chord),
            })
            p += 1
            continue
        steps.append({'type': 'unknown', 'char': ch, 'chord': 0, 'shift': False, 'cap_prefix': False, 'dots': []})
        p += 1
    return steps


# Catalogue of languages for Google Translate
TRANSLATE_LANGUAGES = [
    ('en', 'English'),
    ('bn', 'Bangla (বাংলা)'),
    ('ar', 'Arabic'),
    ('zh-CN', 'Chinese (Simplified)'),
    ('fr', 'French'),
    ('de', 'German'),
    ('hi', 'Hindi'),
    ('id', 'Indonesian'),
    ('it', 'Italian'),
    ('ja', 'Japanese'),
    ('ko', 'Korean'),
    ('ms', 'Malay'),
    ('ne', 'Nepali'),
    ('fa', 'Persian'),
    ('pt', 'Portuguese'),
    ('pa', 'Punjabi'),
    ('ru', 'Russian'),
    ('es', 'Spanish'),
    ('sw', 'Swahili'),
    ('ta', 'Tamil'),
    ('te', 'Telugu'),
    ('th', 'Thai'),
    ('tr', 'Turkish'),
    ('ur', 'Urdu'),
    ('vi', 'Vietnamese'),
]


def translate_text(text: str, target_lang: str = 'en', source_lang: str = 'auto'):
    """Translate text using Google Translate public gtx endpoint."""
    trimmed = (text or '').strip()
    if not trimmed:
        return {'ok': False, 'text': '', 'detected': None, 'error': 'Nothing to translate'}
    try:
        q = urllib.parse.quote(trimmed)
        url = (
            f"https://translate.googleapis.com/translate_a/single"
            f"?client=gtx&sl={urllib.parse.quote(source_lang)}&tl={urllib.parse.quote(target_lang)}&dt=t&q={q}"
        )
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8.0) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if isinstance(data, list) and data and isinstance(data[0], list):
                out = ''.join(seg[0] for seg in data[0] if seg and seg[0])
                detected = data[2] if len(data) > 2 and isinstance(data[2], str) else None
                return {'ok': True, 'text': out, 'detected': detected, 'error': None}
    except Exception as e:
        return {'ok': False, 'text': '', 'detected': None, 'error': f'Translation unavailable: {e}'}
    return {'ok': False, 'text': '', 'detected': None, 'error': 'Translation failed'}


SYMBOL_SPEECH = {
    '+': 'plus', '-': 'minus', '×': 'times', '÷': 'divided by',
    '=': 'equals', ',': 'comma', ';': 'semicolon', ':': 'colon', '.': 'period'
}


class SpeechEngine:
    """Asynchronous cross-platform TTS engine using Windows SAPI / PowerShell."""

    def __init__(self):
        self.enabled = True
        self._lock = threading.Lock()

    def speak(self, text: str, is_bangla: bool = False):
        if not self.enabled or not text:
            return
        clean = str(text).strip()
        if not clean:
            return
        if len(clean) == 1:
            if 'A' <= clean <= 'Z':
                clean = f"capital {clean.lower()}"
            elif clean in SYMBOL_SPEECH:
                clean = SYMBOL_SPEECH[clean]

        def _worker():
            if sys.platform == 'win32':
                try:
                    safe = clean.replace("'", "''").replace('"', '')
                    cmd = (
                        f"Add-Type -AssemblyName System.Speech; "
                        f"$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                        f"$s.Rate = 1; $s.Speak('{safe}')"
                    )
                    subprocess.run(
                        ['powershell', '-NoProfile', '-WindowStyle', 'Hidden', '-Command', cmd],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=6,
                        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                    )
                except Exception:
                    pass

        threading.Thread(target=_worker, daemon=True).start()
