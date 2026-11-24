"""BrailleBridge — Pure Python Native Desktop Application (PyQt6).

Replaces the legacy pywebview website wrapper with a 100% native Python GUI
featuring direct multi-Bluetooth Low Energy (Bleak + WinRT) and USB Serial
connectivity, interactive 6-dot Braille cells, expanded Student View,
multi-student Teacher Mode, Smart Conditional Logs View (replacing Exam View),
and Learner Freeplay & Chord Sequence Trainer.
"""
import json
import os
import sys
import threading
import time
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QSize, QRectF, QVariantAnimation, QEasingCurve
from PyQt6.QtGui import (
    QColor, QFont, QFontDatabase, QIcon, QKeyEvent, QPainter, QPen, QBrush, QCursor, QTextCursor
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QScrollArea, QFrame,
    QStackedWidget, QDialog, QFileDialog, QMessageBox, QSizePolicy, QTextEdit
)

from icons import svg_icon, svg_pixmap, SectionHeader
from relay import (
    RelayManager, SmartFormatter, DATA_DIR, LOGS_DIR,
    STUDENT_LOGS_FILE, ROSTER_FILE, SETTINGS_FILE
)
from protocol import (
    CHAR_TO_CHORD, resolve_chord, chord_dots_list, decode_text_to_steps,
    TRANSLATE_LANGUAGES, translate_text, SpeechEngine
)

STUDENT_COLORS = [
    '#5a8ae0', '#d45a5a', '#5ab85a', '#c49a4a',
    '#8a6ad4', '#4ac8b8', '#e08a5a', '#5ab8b8'
]


_UI_FONT_NAME: str | None = None


def get_ui_font_family() -> str:
    global _UI_FONT_NAME
    if _UI_FONT_NAME is None:
        fams = set(QFontDatabase.families())
        for fam in ("SF Pro Display", "SF Pro Text", "SF Pro", "Inter", "Segoe UI Variable", "Segoe UI"):
            if fam in fams:
                _UI_FONT_NAME = fam
                break
        if _UI_FONT_NAME is None:
            _UI_FONT_NAME = "Segoe UI"
    return _UI_FONT_NAME


def ui_font(size: int = 12, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    return QFont(get_ui_font_family(), size, weight)


def get_initials(name: str) -> str:
    parts = [w[0] for w in (name or 'S').split() if w]
    return ''.join(parts).upper()[:2] or 'ST'


class ThemePalette:
    """Official BrailleBridge design tokens — Midnight Navy primary, Cream/White paper, Bridge Orange accents."""

    DARK = {
        'bg_window': '#000B29',
        'bg_desk': '#00081F',
        'bg_panel': '#001242',
        'bg_card': '#0A1D4E',
        'bg_surface': '#0F2764',
        'bg_hover': '#16337D',
        'border': '#1E3A7A',
        'navy': '#0A2463',
        'navy_dark': '#001242',
        'text_primary': '#FFFDF9',
        'text_secondary': '#CBD5E1',
        'text_muted': '#94A3B8',
        'gold': '#FF7315',
        'gold_light': '#FF944D',
        'gold_dark': '#E05E06',
        'gold_bg': '#2B180A',
        'red': '#EF4444',
        'green': '#22C55E',
        'blue': '#60A5FA',
        'teal': '#2DD4BF',
        'purple': '#A78BFA',
    }

    LIGHT = {
        'bg_window': '#FAF6F0',
        'bg_desk': '#EDF1FA',
        'bg_panel': '#FFFDF9',
        'bg_card': '#FFFDF9',
        'bg_surface': '#F3ECE1',
        'bg_hover': '#E7EBF5',
        'border': '#D0D8EA',
        'navy': '#001242',
        'navy_dark': '#000B29',
        'text_primary': '#001242',
        'text_secondary': '#334155',
        'text_muted': '#64748B',
        'gold': '#FF7315',
        'gold_light': '#FFE5D3',
        'gold_dark': '#E05E06',
        'gold_bg': '#FFF0E5',
        'red': '#DC2626',
        'green': '#16A34A',
        'blue': '#0A2463',
        'teal': '#0D9488',
        'purple': '#6D28D9',
    }


class RelayBridge(QObject):
    """Thread-safe Qt signal bridge from RelayManager background threads to GUI."""
    sig_data = pyqtSignal(str, str)       # port_name, chunk
    sig_ports = pyqtSignal(list)          # list of port dicts
    sig_event = pyqtSignal(str, str)      # port_name, kind ('open'|'close'|'reconnect')
    sig_scan_done = pyqtSignal(bool)      # silent
    sig_student_conn_done = pyqtSignal(str, bool)  # port_name, ok
    sig_roster_conn_done = pyqtSignal(int, bool, bool, str)  # student_id, is_disconnect, ok, port_name
    sig_sim_char = pyqtSignal(int, str, int)  # student_id, ch, chord


class BrailleDotButton(QPushButton):
    """Custom-painted circular Braille dot button with smooth spring pop animation."""

    def __init__(self, dot_number: int, parent=None):
        super().__init__(parent)
        self.dot_number = dot_number
        self.is_active = False
        self.is_dark = True
        self._pulse_scale = 1.0
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(240)
        self._anim.setStartValue(1.16)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self._anim.valueChanged.connect(self._on_anim_val)
        self.setFixedSize(64, 64)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def _on_anim_val(self, val):
        self._pulse_scale = float(val)
        self.update()

    def trigger_pulse(self):
        self._anim.stop()
        self._anim.start()

    def set_active(self, active: bool):
        if self.is_active != active:
            self.is_active = active
            if active:
                self.trigger_pulse()
            self.update()

    def set_theme(self, is_dark: bool):
        self.is_dark = is_dark
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pal = ThemePalette.DARK if self.is_dark else ThemePalette.LIGHT

        cx = self.width() / 2.0
        cy = self.height() / 2.0
        base_r = (min(self.width(), self.height()) - 12) / 2.0
        r = base_r * self._pulse_scale
        rect = QRectF(cx - r, cy - r, r * 2, r * 2)

        if self.is_active:
            p.setBrush(QBrush(QColor(pal['gold'])))
            p.setPen(QPen(QColor(pal['gold_light']), 2.5))
        else:
            p.setBrush(QBrush(QColor(pal['bg_surface'])))
            p.setPen(QPen(QColor(pal['border']), 1.5))

        p.drawEllipse(rect)

        p.setFont(ui_font(13, QFont.Weight.Bold))
        if self.is_active:
            p.setPen(QColor('#141416' if self.is_dark else '#ffffff'))
        else:
            p.setPen(QColor(pal['text_secondary']))
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(self.dot_number))


class MiniBrailleCell(QWidget):
    """Compact 6-dot Braille cell indicator for Student Feed Cards and Chord Trainer."""

    def __init__(self, chord: int = 0, size_scale: float = 1.0, is_dark: bool = True, parent=None):
        super().__init__(parent)
        self.chord = chord
        self.scale = size_scale
        self.is_dark = is_dark
        w = int(34 * size_scale)
        h = int(48 * size_scale)
        self.setFixedSize(w, h)

    def set_chord(self, chord: int):
        if self.chord != chord:
            self.chord = chord
            self.update()

    def set_theme(self, is_dark: bool):
        self.is_dark = is_dark
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pal = ThemePalette.DARK if self.is_dark else ThemePalette.LIGHT

        r = 4.5 * self.scale
        col_x = [8 * self.scale, 24 * self.scale]
        row_y = [9 * self.scale, 24 * self.scale, 39 * self.scale]

        for d in range(6):
            col = 0 if d < 3 else 1
            row = d % 3
            cx = col_x[col]
            cy = row_y[row]
            active = (self.chord & (1 << d)) != 0
            if active:
                p.setBrush(QBrush(QColor(pal['gold'])))
                p.setPen(Qt.PenStyle.NoPen)
            else:
                p.setBrush(QBrush(QColor(pal['bg_surface'])))
                p.setPen(QPen(QColor(pal['border']), 1.0))
            p.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))


class StatusDot(QWidget):
    """Crisp anti-aliased status circle replacing raw bullet characters."""

    def __init__(self, color: str = '#71717a', size: int = 8, parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(size, size)

    def set_color(self, color: str):
        if self._color != color:
            self._color = color
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(QColor(self._color)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(0.5, 0.5, self.width() - 1, self.height() - 1))


class BrailleBridgeWindow(QMainWindow):
    """Main Native Desktop Window for BrailleBridge."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("BrailleBridge — Educational Platform (Native Python)")
        self.resize(1420, 900)
        self.setMinimumSize(1040, 680)

        # State
        self.is_dark = True
        self.current_mode = 'student'  # 'student' | 'teacher' | 'logs' | 'learn'
        self.speech = SpeechEngine()

        # Student view state
        self.student_dots = set()
        self.student_chord = 0
        self.is_bangla = False
        self.shift_active = False
        self.caps_mode = 'OFF'  # 'OFF' | 'ONCE' | 'LOCK'
        self.student_chars = []        # list of {'char': str, 'time': int_ms}
        self.student_recent = []       # last 60 chars
        self.student_port = None
        self.student_connected = False
        self.student_output_expanded = False  # Full-window expansion toggle
        self.mirror_student_id = None
        self._caret_visible = True
        self._just_typed_flash = False
        self._flash_seq = 0
        self._dot_pulse_seq = 0

        self._caret_timer = QTimer(self)
        self._caret_timer.timeout.connect(self._toggle_caret_blink)
        self._caret_timer.start(520)

        # Teacher roster state
        self.students = []             # list of student dicts
        self.student_id_seq = 1
        self.active_teacher_student_id = None
        self.braille_pad_visible = False
        self.available_ports = []

        # Logs state (persisted per-student log records)
        self.student_logs = []         # list of exported log records
        self.selected_log_student = None
        self.selected_log_session_id = None  # None = 'All Today / Combined'
        self.log_raw_mode = False
        self.log_translated_blocks = None
        self.log_translated_label = None

        # Learner state
        self.learner_lang = 'en'
        self.decoder_lang = 'en'
        self.learner_words = []
        self.last_spoken_word = ''

        # Teacher / Classroom profile (persisted in SETTINGS_FILE)
        self.teacher_name = "Teacher"
        self.school_name = "BrailleBridge Classroom"
        self.teacher_email = ""
        # Hardware chord timing defaults (0 ms window = instant decode-on-release, 15 ms debounce)
        self.chord_debounce_ms = 15
        self.chord_window_ms = 0

        # Load persisted data
        self._load_persisted_state()

        # Build UI
        self._build_ui()
        # Prevent buttons/dropdowns/scrollareas from stealing Spacebar or Enter clicks
        from PyQt6.QtWidgets import QComboBox, QCheckBox, QScrollArea
        for w in self.findChildren((QPushButton, QComboBox, QCheckBox, QScrollArea)):
            w.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        if hasattr(self, 'live_text_edit'):
            self.live_text_edit.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._apply_theme()

        # Initialize RelayManager with thread-safe signal bridge
        self.bridge = RelayBridge()
        self.bridge.sig_data.connect(self._on_relay_data)
        self.bridge.sig_ports.connect(self._on_relay_ports)
        self.bridge.sig_event.connect(self._on_relay_event)
        self.bridge.sig_scan_done.connect(self._on_ble_scan_finished)
        self.bridge.sig_student_conn_done.connect(self._on_student_conn_done)
        self.bridge.sig_roster_conn_done.connect(self._on_roster_conn_done)
        self.bridge.sig_sim_char.connect(self._on_sim_char)

        self.relay = RelayManager(self._relay_emit_callback)

        # Populate initial ports
        QTimer.singleShot(200, self._initial_port_scan)

    # ================================================================ PERSISTENCE
    def _load_persisted_state(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                self.teacher_name = cfg.get('teacher_name', 'Teacher') or 'Teacher'
                self.school_name = cfg.get('school_name', 'BrailleBridge Classroom') or 'BrailleBridge Classroom'
                self.teacher_email = cfg.get('teacher_email', '') or ''
                if 'is_dark' in cfg:
                    self.is_dark = bool(cfg['is_dark'])
                if 'speech_enabled' in cfg:
                    self.speech.enabled = bool(cfg['speech_enabled'])
                if 'sound_boost_pct' in cfg:
                    self.speech.boost_pct = max(100, min(300, int(cfg['sound_boost_pct'])))
                if 'chord_debounce_ms' in cfg:
                    self.chord_debounce_ms = max(5, min(50, int(cfg['chord_debounce_ms'])))
                if 'chord_window_ms' in cfg:
                    w = int(cfg['chord_window_ms'])
                    self.chord_window_ms = 0 if w <= 0 else max(50, min(300, w))
        except Exception:
            pass

        try:
            if os.path.exists(STUDENT_LOGS_FILE):
                with open(STUDENT_LOGS_FILE, 'r', encoding='utf-8') as f:
                    self.student_logs = json.load(f)
        except Exception:
            self.student_logs = []

        try:
            if os.path.exists(ROSTER_FILE):
                with open(ROSTER_FILE, 'r', encoding='utf-8') as f:
                    saved_roster = json.load(f)
                for idx, item in enumerate(saved_roster):
                    self.students.append({
                        'id': self.student_id_seq,
                        'name': item.get('name', f'Student {idx+1}'),
                        'connType': item.get('connType', 'bluetooth'),
                        'baud': int(item.get('baud', 115200)),
                        'portName': item.get('portName', ''),
                        'color': STUDENT_COLORS[idx % len(STUDENT_COLORS)],
                        'chars': item.get('chars', []),
                        'connected': False,
                        'mirror': bool(item.get('mirror', False)),
                        'lastChord': 0,
                    })
                    self.student_id_seq += 1
        except Exception:
            pass

    def _save_settings(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'teacher_name': self.teacher_name,
                    'school_name': self.school_name,
                    'teacher_email': self.teacher_email,
                    'is_dark': self.is_dark,
                    'speech_enabled': self.speech.enabled,
                    'sound_boost_pct': self.speech.boost_pct,
                    'chord_debounce_ms': self.chord_debounce_ms,
                    'chord_window_ms': self.chord_window_ms,
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _save_persisted_logs(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        try:
            with open(STUDENT_LOGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.student_logs[:200], f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _save_persisted_roster(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        try:
            serializable = [
                {
                    'name': s['name'],
                    'connType': s['connType'],
                    'baud': s['baud'],
                    'portName': s['portName'],
                    'chars': s['chars'][-2000:],
                    'mirror': s.get('mirror', False),
                }
                for s in self.students
            ]
            with open(ROSTER_FILE, 'w', encoding='utf-8') as f:
                json.dump(serializable, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ================================================================ RELAY BRIDGE
    def _relay_emit_callback(self, kind, port, payload):
        if kind == 'data':
            self.bridge.sig_data.emit(str(port or ''), str(payload or ''))
        elif kind == 'ports':
            self.bridge.sig_ports.emit(list(payload or []))
        else:
            self.bridge.sig_event.emit(str(port or ''), str(kind or ''))

    def _initial_port_scan(self):
        def _init_bg():
            ports = self.relay.list_ports()
            self.bridge.sig_ports.emit(ports)
            self.relay.scan_bluetooth(include_all_named=True)
            ports2 = self.relay.list_ports()
            self.bridge.sig_ports.emit(ports2)

        threading.Thread(target=_init_bg, daemon=True).start()

    def _on_relay_ports(self, ports: list):
        self.available_ports = ports or []
        self._refresh_port_combos()

    def _on_relay_event(self, port_name: str, event: str):
        if event == 'boot_loop':
            msg = (
                f"ESP32 on {port_name} is resetting in a boot loop — "
                f"check USB cable/power and ensure Dot 2 (GPIO12) is not stuck pressed."
            )
            self.student_conn_info.setText(msg)
            self.show_toast(msg)
            return
        if port_name == self.student_port:
            if event == 'close':
                self.student_connected = False
                self._update_student_conn_ui()
            elif event in ('open', 'reconnect'):
                self.student_connected = True
                self._update_student_conn_ui()

        changed = False
        for s in self.students:
            if s.get('portName') == port_name:
                if event == 'close' and s['connected']:
                    s['connected'] = False
                    changed = True
                elif event in ('open', 'reconnect') and not s['connected']:
                    s['connected'] = True
                    changed = True
        if changed:
            self._rebuild_teacher_ui()
        if event in ('open', 'reconnect') and (self.chord_debounce_ms != 15 or self.chord_window_ms != 0):
            self.relay.send_command(f"DEBOUNCE:{self.chord_debounce_ms}", port_name)
            self.relay.send_command(f"WINDOW:{self.chord_window_ms}", port_name)

    def _on_relay_data(self, port_name: str, chunk: str):
        if not chunk:
            return

        # 1. Check if this port is the Student View device
        if port_name == self.student_port or (self.student_port is None and not any(s.get('portName') == port_name for s in self.students)):
            self._process_incoming_chunk_for_student(chunk)

        # 2. Check if this port belongs to any student in Teacher Roster
        for s in self.students:
            if s.get('portName') == port_name:
                self._process_incoming_chunk_for_roster_student(s, chunk)

    def _process_incoming_chunk_for_student(self, chunk: str):
        stripped = chunk.strip()
        if stripped == 'SYSTEM:BKSP':
            self._student_backspace()
            return
        if stripped == 'SYSTEM:CAP_ONCE':
            self.caps_mode = 'ONCE'
            self._update_student_indicators()
            return
        if stripped == 'SYSTEM:CAP_LOCK':
            self.caps_mode = 'LOCK'
            self._update_student_indicators()
            return
        if stripped == 'SYSTEM:CAP_OFF':
            self.caps_mode = 'OFF'
            self._update_student_indicators()
            return
        if stripped == 'LANG:en':
            self.is_bangla = False
            self._update_student_indicators()
            return
        if stripped == 'LANG:bn':
            self.is_bangla = True
            self._update_student_indicators()
            return
        if stripped in ('Invalid', 'SHIFT') or stripped.startswith('SYSTEM:'):
            return

        for ch in chunk:
            if ch in ('\r', '\n'):
                continue
            self._append_student_char(ch)

    def _process_incoming_chunk_for_roster_student(self, student: dict, chunk: str):
        stripped = chunk.strip()
        if stripped == 'SYSTEM:BKSP':
            if student['chars']:
                student['chars'].pop()
                self._update_single_student_card(student)
                self._update_teacher_stats()
            return
        if stripped in ('Invalid', 'SHIFT') or stripped.startswith(('SYSTEM:', 'LANG:')):
            return

        now_ms = int(time.time() * 1000)
        added = False
        for ch in chunk:
            if ch in ('\r', '\n'):
                continue
            student['chars'].append({'char': ch, 'time': now_ms})
            student['lastChord'] = CHAR_TO_CHORD.get(ch, 0)
            added = True
        if added:
            self._update_single_student_card(student)
            self._update_teacher_stats()

    # ================================================================ UI CONSTRUCTION
    def _build_ui(self):
        self._section_headers = []
        central = QWidget()
        central.setObjectName("CentralRoot")
        self.setCentralWidget(central)
        self.root_layout = QVBoxLayout(central)
        self.root_layout.setContentsMargins(20, 16, 20, 16)
        self.root_layout.setSpacing(14)

        # ── Global Top Header Bar ───────────────────────────────────────────
        self.header_frame = QFrame()
        self.header_frame.setObjectName("HeaderFrame")
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(16, 10, 16, 10)
        header_layout.setSpacing(10)

        # Brand Logo & Title
        self.logo_badge = QLabel()
        self.logo_badge.setFixedSize(36, 36)
        self.logo_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.logo_badge)

        self.brand_label = QLabel("Braille<span style='color:#d29a4a;'>Bridge</span>")
        self.brand_label.setFont(ui_font(17, QFont.Weight.Bold))
        header_layout.addWidget(self.brand_label)

        header_layout.addStretch(1)

        # Mode Segmented Control (Student | Teacher | Logs | Learn)
        self.nav_container = QFrame()
        self.nav_container.setObjectName("NavContainer")
        nav_layout = QHBoxLayout(self.nav_container)
        nav_layout.setContentsMargins(4, 4, 4, 4)
        nav_layout.setSpacing(4)

        self.nav_buttons = {}
        self._nav_icon_names = {
            'student': 'monitor',
            'teacher': 'users',
            'logs': 'file_text',
            'learn': 'book_open',
        }
        modes = [
            ('student', 'Student'),
            ('teacher', 'Teacher'),
            ('logs', 'Exports'),
            ('learn', 'Learn'),
        ]
        for key, label in modes:
            btn = QPushButton(label)
            btn.setIconSize(QSize(15, 15))
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setFixedHeight(34)
            btn.clicked.connect(lambda checked, m=key: self.switch_mode(m))
            nav_layout.addWidget(btn)
            self.nav_buttons[key] = btn

        header_layout.addWidget(self.nav_container)

        # Teacher Profile Pill
        self.profile_btn = QPushButton(f"{get_initials(self.teacher_name)}  {self.teacher_name}")
        self.profile_btn.setIconSize(QSize(15, 15))
        self.profile_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.profile_btn.setFixedHeight(36)
        self.profile_btn.clicked.connect(self._open_account_dialog)
        header_layout.addWidget(self.profile_btn)

        # Chord Timing / Speed Button
        self.timing_btn = QPushButton("Timing")
        self.timing_btn.setIconSize(QSize(15, 15))
        self.timing_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.timing_btn.setFixedHeight(36)
        self.timing_btn.setToolTip("Adjust live hardware debounce & chord timing (or reset to 100+ WPM decode-on-release)")
        self.timing_btn.clicked.connect(self._open_timing_dialog)
        header_layout.addWidget(self.timing_btn)

        # Theme Toggle Button
        self.theme_btn = QPushButton("Light")
        self.theme_btn.setIconSize(QSize(15, 15))
        self.theme_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.theme_btn.setFixedHeight(36)
        self.theme_btn.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.theme_btn)

        # Connection Status Pill
        conn_pill = QWidget()
        conn_pill_lay = QHBoxLayout(conn_pill)
        conn_pill_lay.setContentsMargins(8, 4, 8, 4)
        conn_pill_lay.setSpacing(6)
        self.conn_status_dot = StatusDot('#71717a', 8)
        conn_pill_lay.addWidget(self.conn_status_dot)
        self.conn_status_lbl = QLabel("Disconnected")
        self.conn_status_lbl.setFont(ui_font(10, QFont.Weight.DemiBold))
        conn_pill_lay.addWidget(self.conn_status_lbl)
        header_layout.addWidget(conn_pill)

        self.root_layout.addWidget(self.header_frame)

        # ── Main Stacked Views ──────────────────────────────────────────────
        self.stack = QStackedWidget()
        self.view_student = self._build_student_view()
        self.view_teacher = self._build_teacher_view()
        self.view_logs = self._build_logs_view()
        self.view_learn = self._build_learn_view()

        self.stack.addWidget(self.view_student)
        self.stack.addWidget(self.view_teacher)
        self.stack.addWidget(self.view_logs)
        self.stack.addWidget(self.view_learn)

        self.root_layout.addWidget(self.stack, 1)

        # Toast notification banner at bottom
        self.toast_lbl = QLabel("")
        self.toast_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.toast_lbl.setFixedHeight(36)
        self.toast_lbl.hide()
        self.root_layout.addWidget(self.toast_lbl)

    # ---------------------------------------------------------------- VIEW 1: STUDENT (Microsoft Word Document Workspace)
    def _build_student_view(self) -> QWidget:
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        # 1. Word-style Top Ribbon (Connection + Audio + Script + Document Actions)
        ribbon = QFrame()
        ribbon.setProperty("card", True)
        rib_lay = QVBoxLayout(ribbon)
        rib_lay.setContentsMargins(14, 10, 14, 10)
        rib_lay.setSpacing(8)

        # Row 1: Device & Connection
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        self.student_port_combo = QComboBox()
        self.student_port_combo.setMinimumWidth(220)
        self.student_port_combo.setFixedHeight(32)
        row1.addWidget(self.student_port_combo, 1)

        self.btn_scan_ble = QPushButton("Scan BLE")
        self.btn_scan_ble.setIconSize(QSize(14, 14))
        self.btn_scan_ble.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_scan_ble.setFixedHeight(32)
        self.btn_scan_ble.clicked.connect(self._scan_bluetooth_clicked)
        row1.addWidget(self.btn_scan_ble)

        self.student_baud_combo = QComboBox()
        for b in ["115200", "9600", "57600", "38400"]:
            self.student_baud_combo.addItem(f"{b} baud", int(b))
        self.student_baud_combo.setFixedHeight(32)
        row1.addWidget(self.student_baud_combo)

        self.btn_student_connect = QPushButton("Connect Device")
        self.btn_student_connect.setIconSize(QSize(14, 14))
        self.btn_student_connect.setProperty("primary", True)
        self.btn_student_connect.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_student_connect.setFixedHeight(32)
        self.btn_student_connect.clicked.connect(self._toggle_student_connection)
        row1.addWidget(self.btn_student_connect)

        self.btn_send_to_teacher = QPushButton("Mirror to Teacher")
        self.btn_send_to_teacher.setIconSize(QSize(14, 14))
        self.btn_send_to_teacher.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_send_to_teacher.setFixedHeight(32)
        self.btn_send_to_teacher.clicked.connect(self._send_to_teacher_clicked)
        row1.addWidget(self.btn_send_to_teacher)

        self.student_conn_info = QLabel("Ready · BLE / USB / Keyboard")
        self.student_conn_info.setProperty("muted", True)
        row1.addWidget(self.student_conn_info)
        rib_lay.addLayout(row1)

        # Row 2: Audio, Script, Braille Pad Drawer Toggle, Document Actions
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        self.btn_student_sound_toggle = QPushButton("Sound ON")
        self.btn_student_sound_toggle.setIconSize(QSize(14, 14))
        self.btn_student_sound_toggle.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_student_sound_toggle.setFixedHeight(30)
        self.btn_student_sound_toggle.clicked.connect(self._toggle_speech)
        row2.addWidget(self.btn_student_sound_toggle)

        self.btn_sound_boost = QPushButton(f"Boost {self.speech.boost_pct}%")
        self.btn_sound_boost.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_sound_boost.setFixedHeight(30)
        self.btn_sound_boost.setToolTip("Amplify speech volume (100% to 300%)")
        self.btn_sound_boost.clicked.connect(self._cycle_sound_boost)
        row2.addWidget(self.btn_sound_boost)

        self.btn_ind_lang = QPushButton("English")
        self.btn_ind_lang.setIconSize(QSize(13, 13))
        self.btn_ind_lang.setFixedHeight(30)
        self.btn_ind_lang.clicked.connect(self._toggle_language)
        row2.addWidget(self.btn_ind_lang)

        self.btn_ind_caps = QPushButton("Caps OFF")
        self.btn_ind_caps.setFixedHeight(30)
        self.btn_ind_caps.clicked.connect(self._cycle_caps_mode)
        row2.addWidget(self.btn_ind_caps)

        self.btn_ind_shift = QPushButton("Shift")
        self.btn_ind_shift.setIconSize(QSize(13, 13))
        self.btn_ind_shift.setFixedHeight(30)
        self.btn_ind_shift.clicked.connect(self._toggle_shift)
        row2.addWidget(self.btn_ind_shift)

        row2.addStretch(1)

        self.btn_toggle_pad = QPushButton("Braille Pad")
        self.btn_toggle_pad.setIconSize(QSize(14, 14))
        self.btn_toggle_pad.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_toggle_pad.setFixedHeight(30)
        self.btn_toggle_pad.clicked.connect(self._toggle_braille_pad_drawer)
        row2.addWidget(self.btn_toggle_pad)

        self.btn_expand_student_view = QPushButton("Zoom")
        self.btn_expand_student_view.setIconSize(QSize(14, 14))
        self.btn_expand_student_view.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_expand_student_view.setFixedHeight(30)
        self.btn_expand_student_view.clicked.connect(self._toggle_student_full_expand)
        row2.addWidget(self.btn_expand_student_view)

        self.btn_student_export_all = QPushButton("Save to Exports")
        self.btn_student_export_all.setIconSize(QSize(14, 14))
        self.btn_student_export_all.setProperty("primary", True)
        self.btn_student_export_all.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_student_export_all.setFixedHeight(30)
        self.btn_student_export_all.clicked.connect(self.export_all_to_logs)
        row2.addWidget(self.btn_student_export_all)

        self.btn_student_clear = QPushButton("Clear")
        self.btn_student_clear.setIconSize(QSize(14, 14))
        self.btn_student_clear.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_student_clear.setFixedHeight(30)
        self.btn_student_clear.clicked.connect(self._clear_student_display)
        row2.addWidget(self.btn_student_clear)

        rib_lay.addLayout(row2)
        root.addWidget(ribbon)

        # 2. Document Body: Optional Left Braille Pad Drawer + Centered Word Paper Sheet
        body_row = QHBoxLayout()
        body_row.setContentsMargins(0, 0, 0, 0)
        body_row.setSpacing(14)

        self.student_left_panel = QWidget()
        self.student_left_panel.setFixedWidth(310)
        left_layout = QVBoxLayout(self.student_left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        cell_card = QFrame()
        cell_card.setProperty("card", True)
        cell_lay = QVBoxLayout(cell_card)
        cell_lay.setContentsMargins(16, 14, 16, 14)
        cell_lay.setSpacing(10)

        cell_hdr = QHBoxLayout()
        cell_title = SectionHeader("braille", "6-DOT BRAILLE PAD")
        self._section_headers.append(cell_title)
        cell_hdr.addWidget(cell_title)
        cell_hdr.addStretch(1)
        cell_lay.addLayout(cell_hdr)

        self.chord_preview_lbl = QLabel("Pattern: None  ->  -")
        self.chord_preview_lbl.setFont(ui_font(10, QFont.Weight.Bold))
        cell_lay.addWidget(self.chord_preview_lbl)

        dots_grid = QGridLayout()
        dots_grid.setHorizontalSpacing(24)
        dots_grid.setVerticalSpacing(12)
        self.dot_buttons = {}
        for d in range(1, 7):
            btn = BrailleDotButton(d)
            btn.clicked.connect(lambda checked, idx=d: self._toggle_student_dot(idx))
            col = 0 if d <= 3 else 1
            row = (d - 1) % 3
            dots_grid.addWidget(btn, row, col, Qt.AlignmentFlag.AlignCenter)
            self.dot_buttons[d] = btn

        dots_wrap = QHBoxLayout()
        dots_wrap.addStretch(1)
        dots_wrap.addLayout(dots_grid)
        dots_wrap.addStretch(1)
        cell_lay.addLayout(dots_wrap)

        act_row = QHBoxLayout()
        act_row.setSpacing(6)
        self.btn_commit_chord = QPushButton("Commit")
        self.btn_commit_chord.setIconSize(QSize(14, 14))
        self.btn_commit_chord.setProperty("primary", True)
        self.btn_commit_chord.setFixedHeight(34)
        self.btn_commit_chord.clicked.connect(self._commit_student_chord)
        act_row.addWidget(self.btn_commit_chord)

        self.btn_space_chord = QPushButton("Space")
        self.btn_space_chord.setFixedHeight(34)
        self.btn_space_chord.clicked.connect(self._add_student_space)
        act_row.addWidget(self.btn_space_chord)

        self.btn_bksp_chord = QPushButton("Bksp")
        self.btn_bksp_chord.setIconSize(QSize(14, 14))
        self.btn_bksp_chord.setFixedHeight(34)
        self.btn_bksp_chord.clicked.connect(self._student_backspace)
        act_row.addWidget(self.btn_bksp_chord)
        cell_lay.addLayout(act_row)

        self.btn_ind_speech = QPushButton("Speech ON")
        self.btn_ind_speech.hide()

        left_layout.addWidget(cell_card)
        left_layout.addStretch(1)
        self.student_left_panel.hide()
        body_row.addWidget(self.student_left_panel)

        # Centered Word Desk + Paper Sheet
        desk = QFrame()
        desk.setProperty("desk", True)
        desk_lay = QHBoxLayout(desk)
        desk_lay.setContentsMargins(24, 18, 24, 18)
        desk_lay.addStretch(1)

        self.live_output_card = QFrame()
        self.live_output_card.setProperty("paper", True)
        self.live_output_card.setMinimumWidth(620)
        self.live_output_card.setMaximumWidth(860)
        out_lay = QVBoxLayout(self.live_output_card)
        out_lay.setContentsMargins(46, 30, 46, 22)
        out_lay.setSpacing(12)

        # Document Header inside paper
        doc_hdr = QHBoxLayout()
        self.live_out_title = SectionHeader("file_text", "STUDENT DOCUMENT")
        self._section_headers.append(self.live_out_title)
        doc_hdr.addWidget(self.live_out_title)
        doc_hdr.addStretch(1)

        self.bento_lang_val = QLabel("EN")
        self.bento_lang_val.setFont(ui_font(11, QFont.Weight.Bold))
        doc_hdr.addWidget(self.bento_lang_val)

        self.bento_case_sub = QLabel("Lowercase")
        self.bento_case_sub.setProperty("muted", True)
        doc_hdr.addWidget(self.bento_case_sub)

        self.live_out_stats = QLabel("0 words · 0 chars")
        self.live_out_stats.setProperty("muted", True)
        doc_hdr.addWidget(self.live_out_stats)
        out_lay.addLayout(doc_hdr)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setProperty("hairline", True)
        out_lay.addWidget(sep)

        # Main Word-Style Paper Text Canvas
        self.live_text_edit = QTextEdit()
        self.live_text_edit.setReadOnly(True)
        self.live_text_edit.setProperty("paperEditor", True)
        self.live_text_edit.setPlaceholderText("Start typing on your BrailleBridge device — your document appears here...")
        self.live_text_edit.setFont(ui_font(19))
        out_lay.addWidget(self.live_text_edit, 1)

        # Bottom Document Footer (Recent chars + Translate)
        self.recent_card = QFrame()
        self.recent_card.setProperty("subCard", True)
        rec_lay = QHBoxLayout(self.recent_card)
        rec_lay.setContentsMargins(12, 8, 12, 8)
        rec_lay.setSpacing(10)
        self.recent_chars_lbl = QLabel("No characters yet")
        self.recent_chars_lbl.setFont(QFont("Cascadia Code", 11))
        rec_lay.addWidget(self.recent_chars_lbl, 1)
        out_lay.addWidget(self.recent_card)

        trans_row = QHBoxLayout()
        trans_row.setSpacing(8)
        self.student_trans_status = QLabel("Translate document:")
        self.student_trans_status.setProperty("muted", True)
        trans_row.addWidget(self.student_trans_status, 1)

        self.student_trans_combo = QComboBox()
        for code, name in TRANSLATE_LANGUAGES:
            self.student_trans_combo.addItem(name, code)
        self.student_trans_combo.setFixedHeight(30)
        trans_row.addWidget(self.student_trans_combo)

        self.btn_student_translate = QPushButton("Translate")
        self.btn_student_translate.setIconSize(QSize(14, 14))
        self.btn_student_translate.setFixedHeight(30)
        self.btn_student_translate.clicked.connect(self._translate_student_live)
        trans_row.addWidget(self.btn_student_translate)
        out_lay.addLayout(trans_row)

        desk_lay.addWidget(self.live_output_card, 8)
        desk_lay.addStretch(1)
        body_row.addWidget(desk, 1)

        root.addLayout(body_row, 1)
        return page

    # ---------------------------------------------------------------- VIEW 2: TEACHER (Student Document Tabs + Paper)
    def _build_teacher_view(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 1. Teacher Top Ribbon: Inline Add Student + Class Actions
        ribbon = QFrame()
        ribbon.setProperty("card", True)
        rib_lay = QVBoxLayout(ribbon)
        rib_lay.setContentsMargins(14, 10, 14, 10)
        rib_lay.setSpacing(8)

        row_add = QHBoxLayout()
        row_add.setSpacing(8)

        self.input_student_name = QLineEdit()
        self.input_student_name.setPlaceholderText("New Student Name (e.g. Sarah Ahmed)")
        self.input_student_name.setMinimumWidth(180)
        self.input_student_name.setFixedHeight(32)
        self.input_student_name.returnPressed.connect(self._add_student_from_form)
        row_add.addWidget(self.input_student_name, 2)

        self.teacher_conn_type_combo = QComboBox()
        self.teacher_conn_type_combo.addItem("Bluetooth LE", "ble")
        self.teacher_conn_type_combo.addItem("USB Serial", "usb")
        self.teacher_conn_type_combo.addItem("Assign Later", "later")
        self.teacher_conn_type_combo.setFixedHeight(32)
        self.teacher_conn_type_combo.currentIndexChanged.connect(self._refresh_port_combos)
        row_add.addWidget(self.teacher_conn_type_combo)

        self.teacher_port_combo = QComboBox()
        self.teacher_port_combo.setMinimumWidth(180)
        self.teacher_port_combo.setFixedHeight(32)
        row_add.addWidget(self.teacher_port_combo, 2)

        self.teacher_baud_combo = QComboBox()
        for b in ["115200", "9600", "57600", "38400"]:
            self.teacher_baud_combo.addItem(f"{b}", int(b))
        self.teacher_baud_combo.setFixedHeight(32)
        row_add.addWidget(self.teacher_baud_combo)

        self.btn_add_student = QPushButton("Add Student")
        self.btn_add_student.setIconSize(QSize(14, 14))
        self.btn_add_student.setProperty("primary", True)
        self.btn_add_student.setFixedHeight(32)
        self.btn_add_student.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_add_student.clicked.connect(self._add_student_from_form)
        row_add.addWidget(self.btn_add_student)

        self.btn_roster_scan = QPushButton("Scan BLE")
        self.btn_roster_scan.setIconSize(QSize(13, 13))
        self.btn_roster_scan.setFixedHeight(32)
        self.btn_roster_scan.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_roster_scan.clicked.connect(self._scan_bluetooth_clicked)
        row_add.addWidget(self.btn_roster_scan)
        rib_lay.addLayout(row_add)

        row_meta = QHBoxLayout()
        row_meta.setSpacing(8)
        self.teacher_stats_lbl = QLabel("0 students  ·  0 total characters")
        self.teacher_stats_lbl.setFont(ui_font(10, QFont.Weight.DemiBold))
        row_meta.addWidget(self.teacher_stats_lbl)
        row_meta.addStretch(1)

        self.btn_teacher_export_all = QPushButton("Export All to Exports")
        self.btn_teacher_export_all.setIconSize(QSize(14, 14))
        self.btn_teacher_export_all.setProperty("primary", True)
        self.btn_teacher_export_all.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_teacher_export_all.setFixedHeight(30)
        self.btn_teacher_export_all.clicked.connect(self.export_all_to_logs)
        row_meta.addWidget(self.btn_teacher_export_all)

        self.btn_teacher_clear_all = QPushButton("Clear All")
        self.btn_teacher_clear_all.setIconSize(QSize(14, 14))
        self.btn_teacher_clear_all.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_teacher_clear_all.setFixedHeight(30)
        self.btn_teacher_clear_all.clicked.connect(self._clear_all_teacher_feeds)
        row_meta.addWidget(self.btn_teacher_clear_all)
        rib_lay.addLayout(row_meta)

        layout.addWidget(ribbon)

        # 2. Horizontal Student Document Tab Bar (Switch between each student's document!)
        self.teacher_tabs_bar = QFrame()
        self.teacher_tabs_bar.setProperty("card", True)
        tabs_outer = QHBoxLayout(self.teacher_tabs_bar)
        tabs_outer.setContentsMargins(10, 6, 10, 6)
        tabs_outer.setSpacing(6)

        self.teacher_tabs_scroll = QScrollArea()
        self.teacher_tabs_scroll.setWidgetResizable(True)
        self.teacher_tabs_scroll.setFixedHeight(44)
        self.teacher_tabs_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.teacher_tabs_container = QWidget()
        self.teacher_tabs_layout = QHBoxLayout(self.teacher_tabs_container)
        self.teacher_tabs_layout.setContentsMargins(0, 0, 0, 0)
        self.teacher_tabs_layout.setSpacing(6)
        self.teacher_tabs_layout.addStretch(1)
        self.teacher_tabs_scroll.setWidget(self.teacher_tabs_container)
        tabs_outer.addWidget(self.teacher_tabs_scroll, 1)
        layout.addWidget(self.teacher_tabs_bar)

        # 3. Centered Microsoft Word-Style Active Student Document Desk
        desk = QFrame()
        desk.setProperty("desk", True)
        desk_lay = QHBoxLayout(desk)
        desk_lay.setContentsMargins(24, 18, 24, 18)
        desk_lay.addStretch(1)

        self.teacher_paper = QFrame()
        self.teacher_paper.setProperty("paper", True)
        self.teacher_paper.setMinimumWidth(640)
        self.teacher_paper.setMaximumWidth(860)
        tp_lay = QVBoxLayout(self.teacher_paper)
        tp_lay.setContentsMargins(46, 26, 46, 24)
        tp_lay.setSpacing(12)

        # Active Student Document Header + Controls
        self.teacher_doc_hdr = QWidget()
        td_hdr = QHBoxLayout(self.teacher_doc_hdr)
        td_hdr.setContentsMargins(0, 0, 0, 0)
        td_hdr.setSpacing(10)

        self.td_avatar = QLabel("ST")
        self.td_avatar.setFixedSize(36, 36)
        self.td_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        td_hdr.addWidget(self.td_avatar)

        td_meta = QVBoxLayout()
        td_meta.setSpacing(1)
        self.td_name_lbl = QLabel("No Student Selected")
        self.td_name_lbl.setFont(ui_font(15, QFont.Weight.Bold))
        self.td_sub_lbl = QLabel("Add a student above to start monitoring their document")
        self.td_sub_lbl.setProperty("muted", True)
        td_meta.addWidget(self.td_name_lbl)
        td_meta.addWidget(self.td_sub_lbl)
        td_hdr.addLayout(td_meta, 1)

        self.td_mini_cell = MiniBrailleCell(0, 0.72, self.is_dark)
        td_hdr.addWidget(self.td_mini_cell)

        self.td_btn_conn = QPushButton("Connect")
        self.td_btn_conn.setFixedHeight(30)
        self.td_btn_conn.clicked.connect(self._td_toggle_conn)
        td_hdr.addWidget(self.td_btn_conn)

        self.td_btn_test = QPushButton("Test")
        self.td_btn_test.setFixedHeight(30)
        self.td_btn_test.clicked.connect(self._td_test)
        td_hdr.addWidget(self.td_btn_test)

        self.td_btn_export = QPushButton("Export")
        self.td_btn_export.setProperty("primary", True)
        self.td_btn_export.setFixedHeight(30)
        self.td_btn_export.clicked.connect(self._td_export)
        td_hdr.addWidget(self.td_btn_export)

        self.td_btn_clear = QPushButton("Clear")
        self.td_btn_clear.setFixedHeight(30)
        self.td_btn_clear.clicked.connect(self._td_clear)
        td_hdr.addWidget(self.td_btn_clear)

        self.td_btn_remove = QPushButton("Remove")
        self.td_btn_remove.setFixedHeight(30)
        self.td_btn_remove.clicked.connect(self._td_remove)
        td_hdr.addWidget(self.td_btn_remove)

        tp_lay.addWidget(self.teacher_doc_hdr)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setProperty("hairline", True)
        tp_lay.addWidget(sep2)

        self.teacher_doc_edit = QTextEdit()
        self.teacher_doc_edit.setReadOnly(True)
        self.teacher_doc_edit.setProperty("paperEditor", True)
        self.teacher_doc_edit.setPlaceholderText("Add a student above, connect their BrailleBridge, and their live document appears here...")
        self.teacher_doc_edit.setFont(ui_font(18))
        tp_lay.addWidget(self.teacher_doc_edit, 1)

        desk_lay.addWidget(self.teacher_paper, 8)
        desk_lay.addStretch(1)
        layout.addWidget(desk, 1)

        # Keep hidden dummy containers so legacy helpers never fail
        self.roster_scroll = QScrollArea()
        self.roster_scroll.hide()
        self.feed_scroll = QScrollArea()
        self.feed_scroll.hide()
        return page

    # ---------------------------------------------------------------- VIEW 3: LOGS (Replaces Exam View!)
    def _build_logs_view(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Left Sidebar: List of Students (Student Directory)
        left_card = QFrame()
        left_card.setProperty("card", True)
        left_card.setFixedWidth(340)
        left_lay = QVBoxLayout(left_card)
        left_lay.setContentsMargins(16, 14, 16, 14)
        left_lay.setSpacing(10)

        hdr_row = QHBoxLayout()
        title_lbl = SectionHeader("file_text", "STUDENT LOGS")
        self._section_headers.append(title_lbl)
        hdr_row.addWidget(title_lbl)
        hdr_row.addStretch(1)

        self.btn_logs_snap = QPushButton("Export All")
        self.btn_logs_snap.setIconSize(QSize(13, 13))
        self.btn_logs_snap.setProperty("primary", True)
        self.btn_logs_snap.setFixedHeight(28)
        self.btn_logs_snap.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_logs_snap.clicked.connect(self.export_all_to_logs)
        hdr_row.addWidget(self.btn_logs_snap)
        left_lay.addLayout(hdr_row)

        sub_lbl = QLabel("Select a student below to inspect what they wrote today:")
        sub_lbl.setProperty("muted", True)
        sub_lbl.setWordWrap(True)
        left_lay.addWidget(sub_lbl)

        self.logs_students_scroll = QScrollArea()
        self.logs_students_scroll.setWidgetResizable(True)
        self.logs_students_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.logs_students_widget = QWidget()
        self.logs_students_widget.setObjectName("LogsStudentsWidget")
        self.logs_students_layout = QVBoxLayout(self.logs_students_widget)
        self.logs_students_layout.setContentsMargins(0, 0, 0, 0)
        self.logs_students_layout.setSpacing(8)
        self.logs_students_layout.addStretch(1)
        self.logs_students_scroll.setWidget(self.logs_students_widget)
        left_lay.addWidget(self.logs_students_scroll, 1)

        self.btn_clear_logs = QPushButton("Clear Saved Logs")
        self.btn_clear_logs.setIconSize(QSize(14, 14))
        self.btn_clear_logs.setFixedHeight(32)
        self.btn_clear_logs.clicked.connect(self._clear_all_saved_logs)
        left_lay.addWidget(self.btn_clear_logs)

        layout.addWidget(left_card)

        # Right Main Area: Word-Style Desk + Centered Paper Document Reader
        desk = QFrame()
        desk.setProperty("desk", True)
        desk_lay = QHBoxLayout(desk)
        desk_lay.setContentsMargins(24, 16, 24, 16)
        desk_lay.addStretch(1)

        right_card = QFrame()
        right_card.setProperty("paper", True)
        right_card.setMinimumWidth(580)
        right_card.setMaximumWidth(840)
        right_lay = QVBoxLayout(right_card)
        right_lay.setContentsMargins(42, 26, 42, 24)
        right_lay.setSpacing(12)

        # Document Reader Top Bar
        doc_top = QHBoxLayout()
        doc_top.setSpacing(8)
        self.log_doc_title = QLabel("Select a Student")
        self.log_doc_title.setFont(ui_font(18, QFont.Weight.Bold))
        doc_top.addWidget(self.log_doc_title)

        self.log_doc_meta = QLabel("")
        self.log_doc_meta.setProperty("muted", True)
        doc_top.addWidget(self.log_doc_meta)
        doc_top.addStretch(1)

        # Session Selector Combo (All Today vs specific timestamps)
        self.log_session_combo = QComboBox()
        self.log_session_combo.setMinimumWidth(190)
        self.log_session_combo.setFixedHeight(32)
        self.log_session_combo.currentIndexChanged.connect(self._on_log_session_changed)
        doc_top.addWidget(self.log_session_combo)

        # Translate Combo & Button
        self.log_trans_combo = QComboBox()
        for code, name in TRANSLATE_LANGUAGES:
            self.log_trans_combo.addItem(name, code)
        self.log_trans_combo.setFixedHeight(32)
        doc_top.addWidget(self.log_trans_combo)

        self.btn_log_translate = QPushButton("Translate")
        self.btn_log_translate.setIconSize(QSize(14, 14))
        self.btn_log_translate.setFixedHeight(32)
        self.btn_log_translate.clicked.connect(self._translate_current_log)
        doc_top.addWidget(self.btn_log_translate)

        self.btn_log_raw = QPushButton("Plain Text")
        self.btn_log_raw.setIconSize(QSize(14, 14))
        self.btn_log_raw.setFixedHeight(32)
        self.btn_log_raw.clicked.connect(self._toggle_log_raw_mode)
        doc_top.addWidget(self.btn_log_raw)

        self.btn_log_dl = QPushButton("Save .txt")
        self.btn_log_dl.setIconSize(QSize(14, 14))
        self.btn_log_dl.setProperty("primary", True)
        self.btn_log_dl.setFixedHeight(32)
        self.btn_log_dl.clicked.connect(self._download_current_log_txt)
        doc_top.addWidget(self.btn_log_dl)

        right_lay.addLayout(doc_top)

        # Scrollable Conditionally Formatted Document Canvas
        self.log_doc_scroll = QScrollArea()
        self.log_doc_scroll.setWidgetResizable(True)
        self.log_doc_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.log_doc_container = QWidget()
        self.log_doc_layout = QVBoxLayout(self.log_doc_container)
        self.log_doc_layout.setContentsMargins(8, 8, 8, 8)
        self.log_doc_layout.setSpacing(14)
        self.log_doc_layout.addStretch(1)
        self.log_doc_scroll.setWidget(self.log_doc_container)
        right_lay.addWidget(self.log_doc_scroll, 1)

        desk_lay.addWidget(right_card, 8)
        desk_lay.addStretch(1)
        layout.addWidget(desk, 1)
        return page

    # ---------------------------------------------------------------- VIEW 4: LEARN
    def _build_learn_view(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Card 1: Freeplay Playground
        fp_card = QFrame()
        fp_card.setProperty("card", True)
        fp_lay = QVBoxLayout(fp_card)
        fp_lay.setContentsMargins(20, 16, 20, 16)
        fp_lay.setSpacing(10)

        fp_top = QHBoxLayout()
        fp_titles = QVBoxLayout()
        eyebrow = QLabel("BRAILLEBRIDGE · LEARNER")
        eyebrow.setProperty("overline", True)
        fp_titles.addWidget(eyebrow)
        h2 = QLabel("Freeplay Playground")
        h2.setFont(ui_font(18, QFont.Weight.Bold))
        fp_titles.addWidget(h2)
        sub = QLabel(
            "Type on your BrailleBridge or keyboard — every character is spoken aloud. "
            "Finish a word with SPACE and the complete word is spoken."
        )
        sub.setProperty("muted", True)
        fp_titles.addWidget(sub)
        fp_top.addLayout(fp_titles, 1)

        self.btn_learn_en = QPushButton("English")
        self.btn_learn_en.setFixedHeight(32)
        self.btn_learn_en.clicked.connect(lambda: self._set_learner_lang('en'))
        self.btn_learn_bn = QPushButton("বাংলা")
        self.btn_learn_bn.setFixedHeight(32)
        self.btn_learn_bn.clicked.connect(lambda: self._set_learner_lang('bn'))
        fp_top.addWidget(self.btn_learn_en)
        fp_top.addWidget(self.btn_learn_bn)
        fp_lay.addLayout(fp_top)

        self.learner_input = QLineEdit()
        self.learner_input.setPlaceholderText("Type any letter or word — it will be spoken aloud...")
        self.learner_input.setFont(ui_font(16))
        self.learner_input.setFixedHeight(44)
        self.learner_input.textEdited.connect(self._on_learner_input_edited)
        fp_lay.addWidget(self.learner_input)

        self.learner_words_lbl = QLabel("Spoken words appear here")
        self.learner_words_lbl.setWordWrap(True)
        self.learner_words_lbl.setProperty("infoBox", True)
        self.learner_words_lbl.setMinimumHeight(48)
        fp_lay.addWidget(self.learner_words_lbl)

        fp_actions = QHBoxLayout()
        self.btn_learn_repeat = QPushButton("Repeat Last Word")
        self.btn_learn_repeat.setIconSize(QSize(14, 14))
        self.btn_learn_repeat.setFixedHeight(34)
        self.btn_learn_repeat.clicked.connect(self._repeat_learner_word)
        fp_actions.addWidget(self.btn_learn_repeat)

        self.btn_learn_export = QPushButton("Export Progress")
        self.btn_learn_export.setIconSize(QSize(14, 14))
        self.btn_learn_export.setFixedHeight(34)
        self.btn_learn_export.clicked.connect(self._export_learner_progress)
        fp_actions.addWidget(self.btn_learn_export)

        self.btn_learn_clear = QPushButton("Clear")
        self.btn_learn_clear.setIconSize(QSize(14, 14))
        self.btn_learn_clear.setFixedHeight(34)
        self.btn_learn_clear.clicked.connect(self._clear_learner_playground)
        fp_actions.addWidget(self.btn_learn_clear)
        fp_actions.addStretch(1)
        fp_lay.addLayout(fp_actions)

        layout.addWidget(fp_card)

        # Card 2: Chord Sequence Trainer ("See What Codes You Need")
        tr_card = QFrame()
        tr_card.setProperty("card", True)
        tr_lay = QVBoxLayout(tr_card)
        tr_lay.setContentsMargins(20, 16, 20, 16)
        tr_lay.setSpacing(10)

        tr_top = QHBoxLayout()
        tr_titles = QVBoxLayout()
        eyebrow2 = QLabel("BRAILLEBRIDGE · FOR TRAINERS")
        eyebrow2.setProperty("overline", True)
        tr_titles.addWidget(eyebrow2)
        h2_2 = QLabel("See What Codes You Need")
        h2_2.setFont(ui_font(18, QFont.Weight.Bold))
        tr_titles.addWidget(h2_2)
        sub2 = QLabel("Type any word or sentence — get the exact 6-dot chord sequence a student must press, in order.")
        sub2.setProperty("muted", True)
        tr_titles.addWidget(sub2)
        tr_top.addLayout(tr_titles, 1)

        self.btn_dec_en = QPushButton("English")
        self.btn_dec_en.setFixedHeight(32)
        self.btn_dec_en.clicked.connect(lambda: self._set_decoder_lang('en'))
        self.btn_dec_bn = QPushButton("বাংলা")
        self.btn_dec_bn.setFixedHeight(32)
        self.btn_dec_bn.clicked.connect(lambda: self._set_decoder_lang('bn'))
        tr_top.addWidget(self.btn_dec_en)
        tr_top.addWidget(self.btn_dec_bn)
        tr_lay.addLayout(tr_top)

        dec_row = QHBoxLayout()
        self.decoder_input = QLineEdit()
        self.decoder_input.setPlaceholderText("e.g. Hello World or বাংলা")
        self.decoder_input.setFont(ui_font(14))
        self.decoder_input.setFixedHeight(38)
        self.decoder_input.textChanged.connect(self._update_chord_trainer)
        dec_row.addWidget(self.decoder_input, 1)

        self.btn_show_codes = QPushButton("Show Codes")
        self.btn_show_codes.setIconSize(QSize(14, 14))
        self.btn_show_codes.setProperty("primary", True)
        self.btn_show_codes.setFixedHeight(38)
        self.btn_show_codes.clicked.connect(self._update_chord_trainer)
        dec_row.addWidget(self.btn_show_codes)
        tr_lay.addLayout(dec_row)

        self.decoder_scroll = QScrollArea()
        self.decoder_scroll.setWidgetResizable(True)
        self.decoder_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.decoder_container = QWidget()
        self.decoder_grid = QHBoxLayout(self.decoder_container)
        self.decoder_grid.setContentsMargins(4, 4, 4, 4)
        self.decoder_grid.setSpacing(10)
        self.decoder_grid.addStretch(1)
        self.decoder_scroll.setWidget(self.decoder_container)
        tr_lay.addWidget(self.decoder_scroll, 1)

        layout.addWidget(tr_card, 1)
        return page

    # ================================================================ NAVIGATION & THEME
    def switch_mode(self, mode: str):
        self.current_mode = mode
        idx_map = {'student': 0, 'teacher': 1, 'logs': 2, 'learn': 3}
        self.stack.setCurrentIndex(idx_map.get(mode, 0))
        if mode == 'teacher':
            self._rebuild_teacher_ui()
        elif mode == 'logs':
            self._rebuild_logs_ui()
        self._apply_theme()

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.theme_btn.setText("Light" if self.is_dark else "Dark")
        for btn in self.dot_buttons.values():
            btn.set_theme(self.is_dark)
        self._apply_theme()
        self._save_settings()
        if self.current_mode == 'teacher':
            self._rebuild_teacher_ui()
        elif self.current_mode == 'logs':
            self._rebuild_logs_ui()
        elif self.current_mode == 'learn':
            self._update_chord_trainer()

    def _apply_theme(self):
        pal = ThemePalette.DARK if self.is_dark else ThemePalette.LIGHT
        fg = pal['text_primary']
        fg_muted = pal['text_secondary']
        gold = pal['gold']
        btn_fg = '#ffffff'

        self.logo_badge.setPixmap(svg_pixmap('braille', '#ffffff', 22))
        self.logo_badge.setStyleSheet(
            f"background-color: {pal['navy']}; border: 2px solid {gold}; border-radius: 8px;"
        )
        self.brand_label.setText(
            f"<span style='color:{fg};'>Braille</span>"
            f"<span style='color:{gold};'>Bridge</span>"
        )

        for hdr in self._section_headers:
            hdr.set_color(gold)

        for key, btn in self.nav_buttons.items():
            icon_name = self._nav_icon_names[key]
            if key == self.current_mode:
                btn.setIcon(svg_icon(icon_name, '#ffffff', 15))
                btn.setStyleSheet(
                    f"background-color: {pal['navy']}; color: #ffffff; "
                    f"border-bottom: 2.5px solid {gold}; border-radius: 10px; "
                    f"padding: 4px 16px; font-weight: bold;"
                )
            else:
                btn.setIcon(svg_icon(icon_name, fg_muted, 15))
                btn.setStyleSheet(
                    f"background-color: transparent; color: {fg_muted}; "
                    f"border: none; border-radius: 10px; padding: 4px 16px;"
                )

        # Crisp vector icons on all toolbar & action buttons
        self.profile_btn.setIcon(svg_icon('user', gold, 15))
        self.timing_btn.setIcon(svg_icon('clock', fg, 15))
        self.theme_btn.setIcon(svg_icon('sun' if self.is_dark else 'moon', fg, 15))
        self.btn_scan_ble.setIcon(svg_icon('refresh', fg, 14))
        self.btn_send_to_teacher.setIcon(svg_icon('send', fg, 14))
        self.btn_commit_chord.setIcon(svg_icon('return_key', btn_fg, 14))
        self.btn_bksp_chord.setIcon(svg_icon('delete', fg, 14))
        if hasattr(self, 'btn_toggle_pad'):
            self.btn_toggle_pad.setIcon(svg_icon('braille', gold if self.braille_pad_visible else fg, 14))
        self.btn_expand_student_view.setIcon(
            svg_icon('minimize' if self.student_output_expanded else 'expand', fg, 14)
        )
        self.btn_student_export_all.setIcon(svg_icon('upload', btn_fg, 14))
        self.btn_student_clear.setIcon(svg_icon('x', fg, 14))
        self.btn_student_translate.setIcon(svg_icon('globe', fg, 14))
        self.btn_roster_scan.setIcon(svg_icon('refresh', fg, 13))
        self.btn_add_student.setIcon(svg_icon('plus', btn_fg, 14))
        self.btn_teacher_export_all.setIcon(svg_icon('upload', btn_fg, 14))
        self.btn_teacher_clear_all.setIcon(svg_icon('trash', fg, 14))
        self.btn_logs_snap.setIcon(svg_icon('upload', btn_fg, 13))
        self.btn_clear_logs.setIcon(svg_icon('trash', fg, 14))
        self.btn_log_translate.setIcon(svg_icon('globe', fg, 14))
        self.btn_log_raw.setIcon(svg_icon('code', fg, 14))
        self.btn_log_dl.setIcon(svg_icon('download', btn_fg, 14))
        self.btn_learn_repeat.setIcon(svg_icon('repeat', fg, 14))
        self.btn_learn_export.setIcon(svg_icon('save', fg, 14))
        self.btn_learn_clear.setIcon(svg_icon('x', fg, 14))
        self.btn_show_codes.setIcon(svg_icon('code', btn_fg, 14))

        qss = f"""
            QMainWindow, QWidget#CentralRoot, QDialog {{
                background-color: {pal['bg_window']};
                color: {fg};
                font-family: 'SF Pro Display', 'SF Pro Text', 'Inter', 'Segoe UI Variable', 'Segoe UI', sans-serif;
            }}
            QWidget {{
                color: {fg};
                font-family: 'SF Pro Display', 'SF Pro Text', 'Inter', 'Segoe UI Variable', 'Segoe UI', sans-serif;
            }}
            QFrame#HeaderFrame, QFrame[card="true"] {{
                background-color: {pal['bg_panel']};
                border: 1px solid {pal['border']};
                border-radius: 14px;
            }}
            QFrame[desk="true"] {{
                background-color: {pal['bg_desk']};
                border: 1px solid {pal['border']};
                border-radius: 14px;
            }}
            QFrame[paper="true"] {{
                background-color: {pal['bg_card']};
                border: 1px solid {pal['border']};
                border-top: 3px solid {pal['navy']};
                border-radius: 6px;
            }}
            QFrame[hairline="true"] {{
                background-color: {pal['border']};
                max-height: 1px;
                border: none;
            }}
            QFrame[bentoHero="true"] {{
                background-color: {pal['gold_bg']};
                border: 1px solid {pal['gold']};
                border-radius: 14px;
            }}
            QFrame[subCard="true"] {{
                background-color: {pal['bg_surface']};
                border: 1px solid {pal['border']};
                border-radius: 10px;
            }}
            QFrame#NavContainer {{
                background-color: {pal['bg_surface']};
                border: 1px solid {pal['border']};
                border-radius: 12px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
            QLabel[overline="true"] {{
                color: {gold};
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 0.8px;
            }}
            QLabel[muted="true"] {{
                color: {pal['text_secondary']};
                font-size: 12px;
            }}
            QLabel[infoBox="true"] {{
                background-color: {pal['bg_surface']};
                color: {pal['text_secondary']};
                border: 1px solid {pal['border']};
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 12px;
            }}
            QPushButton {{
                background-color: {pal['bg_surface']};
                color: {pal['text_primary']};
                border: 1px solid {pal['border']};
                border-radius: 10px;
                padding: 5px 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {pal['bg_hover']};
            }}
            QPushButton[primary="true"] {{
                background-color: {pal['navy']};
                color: #ffffff;
                border: 1px solid {pal['navy_dark']};
                border-radius: 10px;
            }}
            QPushButton[primary="true"]:hover {{
                background-color: {gold};
                border-color: {pal['gold_dark']};
            }}
            QLineEdit, QComboBox, QTextEdit {{
                background-color: {pal['bg_surface']};
                color: {pal['text_primary']};
                border: 1px solid {pal['border']};
                border-radius: 10px;
                padding: 5px 10px;
            }}
            QTextEdit[paperEditor="true"] {{
                background-color: transparent;
                color: {pal['text_primary']};
                border: none;
                border-radius: 0px;
                padding: 8px 2px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
                subcontrol-origin: padding;
                subcontrol-position: top right;
            }}
            QComboBox QAbstractItemView {{
                background-color: {pal['bg_panel']};
                color: {pal['text_primary']};
                border: 1px solid {pal['border']};
                border-radius: 10px;
                selection-background-color: {pal['gold_bg']};
                selection-color: {pal['gold']};
                outline: 0;
                padding: 6px;
            }}
            QComboBox QAbstractItemView::item {{
                min-height: 28px;
                padding: 4px 12px;
                border-radius: 8px;
                color: {pal['text_primary']};
                background-color: {pal['bg_panel']};
            }}
            QComboBox QAbstractItemView::item:selected,
            QComboBox QAbstractItemView::item:hover {{
                background-color: {pal['gold_bg']};
                color: {pal['gold']};
            }}
            QScrollArea, QScrollArea > QWidget > QWidget {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical, QScrollBar:horizontal {{
                width: 0px;
                height: 0px;
                background: transparent;
                border: none;
            }}
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal,
            QScrollBar::add-line, QScrollBar::sub-line,
            QScrollBar::add-page, QScrollBar::sub-page {{
                background: transparent;
                border: none;
            }}
        """
        self.setStyleSheet(qss)
        for sa in (self.logs_students_scroll, self.log_doc_scroll, self.decoder_scroll, self.teacher_tabs_scroll):
            sa.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            sa.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")
            if sa.viewport():
                sa.viewport().setStyleSheet("background-color: transparent;")
        self.live_text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.live_text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.teacher_doc_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.teacher_doc_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        for container in (self.teacher_tabs_container, self.logs_students_widget, self.log_doc_container, self.decoder_container):
            obj = container.objectName()
            if obj:
                container.setStyleSheet(f"QWidget#{obj} {{ background-color: transparent; }}")
            else:
                container.setStyleSheet("background-color: transparent;")
        self.theme_btn.setText("Light" if self.is_dark else "Dark")
        self._refresh_port_combos()
        self._update_student_indicators()
        self._update_student_conn_ui()
        self._refresh_student_output_text()

    def show_toast(self, message: str):
        pal = ThemePalette.DARK if self.is_dark else ThemePalette.LIGHT
        self.toast_lbl.setText(message)
        self.toast_lbl.setStyleSheet(
            f"background-color: {pal['gold']}; color: #141416; "
            f"font-weight: bold; border-radius: 8px; padding: 6px 16px;"
        )
        self.toast_lbl.show()
        QTimer.singleShot(3200, self.toast_lbl.hide)

    # ================================================================ STUDENT VIEW HANDLERS
    def _refresh_port_combos(self):
        pal = ThemePalette.DARK if self.is_dark else ThemePalette.LIGHT
        fg = pal['text_primary']

        # 1) Student combo: Bluetooth HID Keyboard + BLE + USB Serial
        prev_st = self.student_port_combo.currentData()
        self.student_port_combo.clear()
        self.student_port_combo.addItem(
            svg_icon('keyboard', pal['gold'], 14),
            "Bluetooth HID Keyboard (Direct Input)",
            "KEYBOARD"
        )
        for p in self.available_ports:
            name = p.get('name', '')
            desc = p.get('description', name)
            ic = svg_icon('bluetooth', pal['blue'], 14) if name.startswith("BLE:") else svg_icon('usb', fg, 14)
            self.student_port_combo.addItem(ic, desc, name)
        if prev_st:
            idx = self.student_port_combo.findData(prev_st)
            if idx >= 0:
                self.student_port_combo.setCurrentIndex(idx)

        # 2) Teacher combo: filtered by teacher_conn_type_combo (ble / usb / later)
        prev_tc = self.teacher_port_combo.currentData()
        self.teacher_port_combo.clear()
        conn_mode = self.teacher_conn_type_combo.currentData() if hasattr(self, 'teacher_conn_type_combo') else 'ble'

        if conn_mode == 'later':
            self.teacher_port_combo.setEnabled(False)
            self.teacher_port_combo.addItem(svg_icon('clock', pal['text_muted'], 14), "Assign device later", "")
            return

        self.teacher_port_combo.setEnabled(True)
        ble_ports = [p for p in self.available_ports if str(p.get('name', '')).startswith('BLE:')]
        usb_ports = [p for p in self.available_ports if not str(p.get('name', '')).startswith('BLE:')]

        if conn_mode == 'ble':
            if ble_ports:
                for p in ble_ports:
                    self.teacher_port_combo.addItem(
                        svg_icon('bluetooth', pal['blue'], 14),
                        p.get('description', p['name']),
                        p['name']
                    )
            else:
                self.teacher_port_combo.addItem(
                    svg_icon('bluetooth', pal['text_muted'], 14),
                    "No BLE found yet — click 'Scan Bluetooth'",
                    ""
                )
        else:
            if usb_ports:
                for p in usb_ports:
                    self.teacher_port_combo.addItem(
                        svg_icon('usb', fg, 14),
                        p.get('description', p['name']),
                        p['name']
                    )
            else:
                self.teacher_port_combo.addItem(
                    svg_icon('usb', pal['text_muted'], 14),
                    "No USB Serial port detected",
                    ""
                )

        if prev_tc:
            idx = self.teacher_port_combo.findData(prev_tc)
            if idx >= 0:
                self.teacher_port_combo.setCurrentIndex(idx)

    def _scan_bluetooth_clicked(self, silent: bool = False):
        self.btn_scan_ble.setText("Scanning...")
        self.btn_scan_ble.setEnabled(False)
        if hasattr(self, 'btn_roster_scan'):
            self.btn_roster_scan.setText("Scanning...")
            self.btn_roster_scan.setEnabled(False)

        def _worker():
            self.relay.scan_bluetooth(include_all_named=True)
            ports = self.relay.list_ports()
            self.bridge.sig_ports.emit(ports)
            self.bridge.sig_scan_done.emit(silent)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_ble_scan_finished(self, silent: bool = False):
        self.btn_scan_ble.setText("Scan BLE")
        self.btn_scan_ble.setEnabled(True)
        if hasattr(self, 'btn_roster_scan'):
            self.btn_roster_scan.setText("Scan Bluetooth")
            self.btn_roster_scan.setEnabled(True)
        if silent:
            return
        err = self.relay.ble.last_error
        ble_count = sum(1 for p in self.available_ports if str(p.get('name', '')).startswith('BLE:'))
        if err:
            self.show_toast(f"Bluetooth notice: {err}")
            self.student_conn_info.setText(f"{err}\nYou can still use Bluetooth Keyboard or USB Serial.")
        else:
            self.show_toast(f"Scan complete: {ble_count} Bluetooth device(s), {len(self.available_ports)} total port(s).")

    def _toggle_student_connection(self):
        if self.student_connected:
            old_port = self.student_port
            self.student_port = None
            self.student_connected = False
            self._update_student_conn_ui()
            self.show_toast("Disconnected student device.")
            if old_port and old_port != "KEYBOARD":
                threading.Thread(target=lambda: self.relay.close_port(old_port), daemon=True).start()
            return

        port_name = self.student_port_combo.currentData()
        baud = self.student_baud_combo.currentData() or 115200
        if not port_name:
            self.show_toast("Select a Bluetooth device or Serial port first.")
            return

        if port_name == "KEYBOARD":
            self.student_port = "KEYBOARD"
            self.student_connected = True
            self._set_student_expanded(True)
            self._update_student_conn_ui()
            self.show_toast("Connected to Bluetooth HID Keyboard! Start typing on BrailleBridge.")
            return

        self.btn_student_connect.setText("Connecting...")
        self.btn_student_connect.setEnabled(False)
        self.student_conn_info.setText(f"Connecting to {port_name}...")

        def _worker():
            ok = self.relay.open_port(port_name, baud)
            self.bridge.sig_student_conn_done.emit(port_name, bool(ok))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_student_conn_done(self, port_name: str, ok: bool):
        self.btn_student_connect.setEnabled(True)
        if ok:
            self.student_port = port_name
            self.student_connected = True
            self._set_student_expanded(True)
            self._update_student_conn_ui()
            self.show_toast(f"Connected to {port_name}!")
        else:
            err = self.relay.ble.last_error or "Check that the device is powered on and nearby."
            self._update_student_conn_ui()
            self.student_conn_info.setText(f"Failed to connect to {port_name}.\n{err}")
            self.show_toast(f"Could not open {port_name}.")

    def _update_student_conn_ui(self):
        pal = ThemePalette.DARK if self.is_dark else ThemePalette.LIGHT
        if self.student_connected:
            self.conn_status_dot.set_color(pal['green'])
            self.conn_status_lbl.setText(f"Connected ({self.student_port})")
            self.conn_status_lbl.setStyleSheet(f"color: {pal['green']}; font-weight: bold;")
            self.btn_student_connect.setText("Disconnect Device")
            self.btn_student_connect.setIcon(svg_icon('x', '#ffffff', 15))
            self.btn_student_connect.setStyleSheet(
                f"background-color: {pal['red']}; color: #ffffff; border-radius: 10px; font-weight: bold;"
            )
            self.student_conn_info.setText(
                f"Connected to {self.student_port}\n"
                f"Live stream active — Student View expanded for reading."
            )
        else:
            self.conn_status_dot.set_color(pal['text_muted'])
            self.conn_status_lbl.setText("Disconnected")
            self.conn_status_lbl.setStyleSheet(f"color: {pal['text_muted']};")
            self.btn_student_connect.setText("Connect Selected Device")
            self.btn_student_connect.setIcon(svg_icon('bluetooth', '#ffffff', 15))
            self.btn_student_connect.setStyleSheet(
                f"background-color: {pal['gold']}; color: #ffffff; border-radius: 10px; font-weight: bold;"
            )

    def _toggle_braille_pad_drawer(self):
        self.braille_pad_visible = not self.braille_pad_visible
        self.student_left_panel.setVisible(self.braille_pad_visible)
        self._apply_theme()

    def _toggle_student_full_expand(self):
        self._set_student_expanded(not self.student_output_expanded)

    def _set_student_expanded(self, expanded: bool):
        pal = ThemePalette.DARK if self.is_dark else ThemePalette.LIGHT
        self.student_output_expanded = expanded
        if expanded:
            self.live_text_edit.setFont(ui_font(24))
            self.recent_card.hide()
            self.btn_expand_student_view.setText("Normal")
            self.btn_expand_student_view.setIcon(svg_icon('minimize', pal['text_primary'], 14))
        else:
            self.live_text_edit.setFont(ui_font(19))
            self.recent_card.show()
            self.btn_expand_student_view.setText("Zoom")
            self.btn_expand_student_view.setIcon(svg_icon('expand', pal['text_primary'], 14))

    def _toggle_student_dot(self, dot_idx: int):
        if dot_idx in self.student_dots:
            self.student_dots.remove(dot_idx)
        else:
            self.student_dots.add(dot_idx)
        self._recalc_student_chord()

    def _recalc_student_chord(self):
        c = 0
        for d in self.student_dots:
            c |= (1 << (d - 1))
        self.student_chord = c
        for d, btn in self.dot_buttons.items():
            btn.set_active(d in self.student_dots)

        if c == 0:
            self.chord_preview_lbl.setText("Pattern: None  ->  -")
        else:
            dots_str = ','.join(str(d) for d in sorted(self.student_dots))
            if c == 0b100000 and not self.shift_active and not self.is_bangla:
                preview = "Capital Prefix"
            else:
                preview = resolve_chord(c, self.is_bangla, self.shift_active, self.caps_mode) or "-"
            self.chord_preview_lbl.setText(f"Pattern: Dots {dots_str}  ->  {preview}")

    def _commit_student_chord(self):
        if self.student_chord <= 0:
            return
        if self.student_chord == 0b100000 and not self.shift_active and not self.is_bangla:
            self._cycle_caps_mode()
            self.student_dots.clear()
            self._recalc_student_chord()
            return

        resolved = resolve_chord(self.student_chord, self.is_bangla, self.shift_active, self.caps_mode)
        if self.caps_mode == 'ONCE':
            self.caps_mode = 'OFF'
        if self.shift_active:
            self.shift_active = False
        self._update_student_indicators()

        if resolved:
            for ch in resolved:
                self._append_student_char(ch)
        self.student_dots.clear()
        self._recalc_student_chord()

    def _add_student_space(self):
        if self.caps_mode == 'ONCE':
            self.caps_mode = 'OFF'
            self._update_student_indicators()
        self._append_student_char(' ')

    def _append_student_char(self, ch: str):
        now_ms = int(time.time() * 1000)
        self.student_chars.append({'char': ch, 'time': now_ms})
        self.student_recent.append(ch)
        if len(self.student_recent) > 60:
            self.student_recent.pop(0)

        # Speech feedback
        if ch == ' ':
            self.speech.speak('space', self.is_bangla)
        else:
            self.speech.speak(ch, self.is_bangla)

        # Mirror to teacher student if active
        if self.mirror_student_id is not None:
            for s in self.students:
                if s['id'] == self.mirror_student_id:
                    s['chars'].append({'char': ch, 'time': now_ms})
                    s['lastChord'] = CHAR_TO_CHORD.get(ch, 0)
                    break

        # Trigger typing animations: 6-dot pulse + O(1) incremental text append
        self._animate_dots_for_char(ch)
        self._append_live_text_fast(ch)

    def _clear_typed_flash(self, seq: int):
        pass

    def _toggle_caret_blink(self):
        pass

    def _append_live_text_fast(self, ch: str):
        """O(1) incremental append to QTextEdit without re-parsing HTML DOM on every keystroke."""
        text_len = len(self.student_chars)
        words = len(''.join(x['char'] for x in self.student_chars).split()) if text_len else 0
        self.live_out_stats.setText(f"{words} words · {text_len} chars")
        if hasattr(self, 'bento_words_val'):
            self.bento_words_val.setText(str(words))
            self.bento_chars_sub.setText(f"words · {text_len} chars")

        cur = self.live_text_edit.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        cur.insertText(ch)
        self.live_text_edit.setTextCursor(cur)
        sb = self.live_text_edit.verticalScrollBar()
        if sb:
            sb.setValue(sb.maximum())

        if not self.student_recent:
            self.recent_chars_lbl.setText("No characters yet")
        else:
            disp = ['␣' if c == ' ' else c for c in self.student_recent]
            self.recent_chars_lbl.setText("  ".join(disp))

    def _animate_dots_for_char(self, ch: str):
        if ch == ' ':
            return
        chord = CHAR_TO_CHORD.get(ch, 0) or CHAR_TO_CHORD.get(ch.lower(), 0)
        if chord <= 0:
            return
        dots = chord_dots_list(chord)
        if not dots:
            return
        self._dot_pulse_seq += 1
        seq = self._dot_pulse_seq
        for d, btn in self.dot_buttons.items():
            btn.set_active(d in dots)
        QTimer.singleShot(340, lambda s=seq: self._clear_dot_pulse(s))

    def _clear_dot_pulse(self, seq: int):
        if seq == self._dot_pulse_seq and not self.student_dots:
            for btn in self.dot_buttons.values():
                btn.set_active(False)

    def _student_backspace(self):
        if self.student_chars:
            self.student_chars.pop()
        if self.student_recent:
            self.student_recent.pop()
        if self.mirror_student_id is not None:
            for s in self.students:
                if s['id'] == self.mirror_student_id and s['chars']:
                    s['chars'].pop()
                    break
        self._refresh_student_output_text()

    def _clear_student_display(self):
        self.student_chars.clear()
        self.student_recent.clear()
        self.student_dots.clear()
        self._recalc_student_chord()
        self._refresh_student_output_text()

    def _refresh_student_output_text(self):
        text = ''.join(x['char'] for x in self.student_chars)
        words = len(text.split()) if text.strip() else 0
        self.live_out_stats.setText(f"{words} words · {len(self.student_chars)} chars")
        if hasattr(self, 'bento_words_val'):
            self.bento_words_val.setText(str(words))
            self.bento_chars_sub.setText(f"words · {len(self.student_chars)} chars")

        if not text:
            self.live_text_edit.clear()
        else:
            self.live_text_edit.setPlainText(text)
        self.live_text_edit.moveCursor(QTextCursor.MoveOperation.End)
        sb = self.live_text_edit.verticalScrollBar()
        if sb:
            sb.setValue(sb.maximum())

        if not self.student_recent:
            self.recent_chars_lbl.setText("No characters yet")
        else:
            disp = ['␣' if c == ' ' else c for c in self.student_recent]
            self.recent_chars_lbl.setText("  ".join(disp))

    def _toggle_speech(self):
        self.speech.enabled = not self.speech.enabled
        self._save_settings()
        self._update_student_indicators()

    def _cycle_sound_boost(self):
        steps = [100, 150, 200, 250, 300]
        cur = self.speech.boost_pct
        nxt = next((v for v in steps if v > cur), steps[0])
        self.speech.boost_pct = nxt
        self._save_settings()
        self._update_student_indicators()
        self.show_toast(f"Sound Booster set to {nxt}%")
        if self.speech.enabled:
            self.speech.speak(f"boost {nxt} percent")

    def _toggle_language(self):
        self.is_bangla = not self.is_bangla
        self._update_student_indicators()
        self._recalc_student_chord()

    def _cycle_caps_mode(self):
        order = {'OFF': 'ONCE', 'ONCE': 'LOCK', 'LOCK': 'OFF'}
        self.caps_mode = order.get(self.caps_mode, 'OFF')
        self._update_student_indicators()
        self._recalc_student_chord()

    def _toggle_shift(self):
        self.shift_active = not self.shift_active
        self._update_student_indicators()
        self._recalc_student_chord()

    def _update_student_indicators(self):
        pal = ThemePalette.DARK if self.is_dark else ThemePalette.LIGHT
        gold = pal['gold']
        muted = pal['text_secondary']

        self.btn_ind_speech.setText("Speech ON" if self.speech.enabled else "Speech OFF")
        self.btn_ind_speech.setIcon(svg_icon('volume_on' if self.speech.enabled else 'volume_off', gold if self.speech.enabled else muted, 13))

        self.btn_ind_lang.setText("বাংলা" if self.is_bangla else "English")
        self.btn_ind_lang.setIcon(svg_icon('globe', gold if self.is_bangla else muted, 13))

        self.btn_ind_caps.setText(f"Caps {self.caps_mode}")

        self.btn_ind_shift.setText("Shift ON" if self.shift_active else "Shift")
        self.btn_ind_shift.setIcon(svg_icon('arrow_up', gold if self.shift_active else muted, 13))

        active_style = f"background-color: {pal['gold_bg']}; color: {gold}; border: 1px solid {gold}; border-radius: 12px; padding: 4px 6px; font-size: 11px;"
        idle_style = f"background-color: {pal['bg_surface']}; color: {muted}; border: 1px solid {pal['border']}; border-radius: 12px; padding: 4px 6px; font-size: 11px;"

        self.btn_ind_speech.setStyleSheet(active_style if self.speech.enabled else idle_style)
        self.btn_ind_lang.setStyleSheet(active_style if self.is_bangla else idle_style)
        self.btn_ind_caps.setStyleSheet(active_style if self.caps_mode != 'OFF' else idle_style)
        self.btn_ind_shift.setStyleSheet(active_style if self.shift_active else idle_style)

        # Keep the prominent Sound ON/OFF button in the Student View main menu synced
        self.btn_student_sound_toggle.setText("Sound ON" if self.speech.enabled else "Sound OFF")
        self.btn_student_sound_toggle.setIcon(
            svg_icon('volume_on' if self.speech.enabled else 'volume_off', pal['green'] if self.speech.enabled else muted, 14)
        )
        if hasattr(self, 'bento_lang_val'):
            self.bento_lang_val.setText("BN" if self.is_bangla else "EN")
            if self.is_bangla:
                self.bento_case_sub.setText("Bangla Script")
            elif self.shift_active:
                self.bento_case_sub.setText("Shift Active")
            elif self.caps_mode != 'OFF':
                self.bento_case_sub.setText(f"Caps {self.caps_mode}")
            else:
                self.bento_case_sub.setText("Lowercase")
        if self.speech.enabled:
            self.btn_student_sound_toggle.setStyleSheet(
                f"background-color: {pal['bg_surface']}; color: {pal['green']}; "
                f"border: 1.5px solid {pal['green']}; border-radius: 10px; padding: 4px 12px; font-weight: bold;"
            )
        else:
            self.btn_student_sound_toggle.setStyleSheet(
                f"background-color: {pal['bg_surface']}; color: {muted}; "
                f"border: 1px solid {pal['border']}; border-radius: 10px; padding: 4px 12px; font-weight: 600;"
            )
        if hasattr(self, 'btn_sound_boost'):
            bp = self.speech.boost_pct
            self.btn_sound_boost.setText(f"Boost {bp}%")
            boosted = bp > 100
            self.btn_sound_boost.setStyleSheet(
                f"background-color: {pal['gold_bg'] if boosted else pal['bg_surface']}; "
                f"color: {pal['gold'] if boosted else muted}; "
                f"border: {'1.5px solid ' + pal['gold'] if boosted else '1px solid ' + pal['border']}; "
                f"border-radius: 10px; padding: 4px 10px; font-weight: {'bold' if boosted else '600'};"
            )

    def _translate_student_live(self):
        text = ''.join(x['char'] for x in self.student_chars).strip()
        if not text:
            self.student_trans_status.setText("Nothing to translate yet — type some text first.")
            return
        target = self.student_trans_combo.currentData() or 'en'
        self.student_trans_status.setText("Translating...")
        QApplication.processEvents()
        res = translate_text(text, target)
        if res['ok']:
            self.student_trans_status.setText(res['text'])
        else:
            self.student_trans_status.setText(f"Translation error: {res['error']}")

    def _send_to_teacher_clicked(self):
        if self.mirror_student_id is not None and any(s['id'] == self.mirror_student_id for s in self.students):
            self.show_toast("Student View is already mirrored in Teacher Mode.")
            self.switch_mode('teacher')
            return
        st = {
            'id': self.student_id_seq,
            'name': 'Student View (Mirror)',
            'connType': 'bluetooth',
            'baud': 115200,
            'portName': self.student_port or 'MIRROR',
            'color': STUDENT_COLORS[len(self.students) % len(STUDENT_COLORS)],
            'chars': list(self.student_chars),
            'connected': True,
            'mirror': True,
            'lastChord': self.student_chord,
        }
        self.student_id_seq += 1
        self.mirror_student_id = st['id']
        self.students.append(st)
        self._save_persisted_roster()
        self.show_toast("Student View mirrored to Teacher Mode!")
        self.switch_mode('teacher')

    # ================================================================ TEACHER VIEW HANDLERS
    def _add_student_from_form(self):
        name = self.input_student_name.text().strip()
        if not name:
            self.show_toast("Enter a student name first.")
            return
        conn_mode = self.teacher_conn_type_combo.currentData() if hasattr(self, 'teacher_conn_type_combo') else 'ble'
        port_name = self.teacher_port_combo.currentData() or ''
        baud = self.teacher_baud_combo.currentData() or 115200
        if conn_mode == 'later':
            port_name = ''
        conn_type = 'bluetooth' if (conn_mode == 'ble' or str(port_name).startswith('BLE:') or not port_name) else 'usb'

        st = {
            'id': self.student_id_seq,
            'name': name,
            'connType': conn_type,
            'baud': baud,
            'portName': port_name,
            'color': STUDENT_COLORS[len(self.students) % len(STUDENT_COLORS)],
            'chars': [],
            'connected': False,
            'connecting': False,
            'mirror': False,
            'lastChord': 0,
        }
        self.student_id_seq += 1
        self.students.append(st)
        if port_name:
            self.relay.set_assignment(name, port_name)
        self.input_student_name.clear()
        self._save_persisted_roster()
        self._rebuild_teacher_ui()
        self.show_toast(f"Added {name} to classroom roster.")

    def _toggle_roster_student_conn(self, student: dict):
        if student.get('connecting'):
            return
        port_name = student.get('portName')
        if not port_name:
            port_name = self.teacher_port_combo.currentData()
            if port_name:
                student['portName'] = port_name
                student['connType'] = 'bluetooth' if str(port_name).startswith('BLE:') else 'usb'
            else:
                self.show_toast(f"Select a Bluetooth or USB device for {student['name']} first (click Scan Bluetooth).")
                return

        if student['connected']:
            student['connecting'] = True
            self._rebuild_teacher_ui()
            sid = student['id']

            def _disc():
                self.relay.close_port(port_name)
                self.bridge.sig_roster_conn_done.emit(sid, True, True, port_name)

            threading.Thread(target=_disc, daemon=True).start()
        else:
            student['connecting'] = True
            self._rebuild_teacher_ui()
            sid = student['id']

            def _conn():
                ok = self.relay.open_port(port_name, student['baud'])
                self.bridge.sig_roster_conn_done.emit(sid, False, bool(ok), port_name)

            threading.Thread(target=_conn, daemon=True).start()

    def _on_roster_conn_done(self, student_id: int, is_disconnect: bool, ok: bool, port_name: str):
        student = next((s for s in self.students if s['id'] == student_id), None)
        if not student:
            return
        student['connecting'] = False
        if is_disconnect:
            student['connected'] = False
            self._rebuild_teacher_ui()
            self.show_toast(f"Disconnected {student['name']}.")
        elif ok:
            student['connected'] = True
            self.relay.set_assignment(student['name'], port_name)
            self._rebuild_teacher_ui()
            self.show_toast(f"Connected {student['name']} ({port_name})!")
        else:
            self._rebuild_teacher_ui()
            self.show_toast(f"Could not connect {student['name']} to {port_name}.")

    def _simulate_student_typing(self, student: dict):
        sample = "Science Notes\n\nChapter 1 Motion\n\nWhat is speed? Answer: Speed is distance divided by time. 20 + 30 = 50. Remember: Check your units!"
        sid = student['id']

        def _sim():
            for ch in sample:
                chord = CHAR_TO_CHORD.get(ch, 0)
                self.bridge.sig_sim_char.emit(sid, ch, chord)
                time.sleep(0.03)
            self._save_persisted_roster()

        threading.Thread(target=_sim, daemon=True).start()

    def _on_sim_char(self, student_id: int, ch: str, chord: int):
        student = next((s for s in self.students if s['id'] == student_id), None)
        if not student:
            return
        student['chars'].append({'char': ch, 'time': int(time.time() * 1000)})
        student['lastChord'] = chord
        self._update_single_student_card(student)
        self._update_teacher_stats()

    def _clear_single_student(self, student: dict):
        student['chars'].clear()
        student['lastChord'] = 0
        self._save_persisted_roster()
        self._rebuild_teacher_ui()

    def _remove_single_student(self, student: dict):
        port_to_close = student.get('portName') if student.get('connected') else None
        self.students = [s for s in self.students if s['id'] != student['id']]
        if self.mirror_student_id == student['id']:
            self.mirror_student_id = None
        self._save_persisted_roster()
        self._rebuild_teacher_ui()
        self.show_toast(f"Removed {student['name']}.")
        if port_to_close:
            threading.Thread(target=lambda: self.relay.close_port(port_to_close), daemon=True).start()

    def _clear_all_teacher_feeds(self):
        for s in self.students:
            s['chars'].clear()
            s['lastChord'] = 0
        self._save_persisted_roster()
        self._rebuild_teacher_ui()
        self.show_toast("Cleared all student feeds.")

    def _update_teacher_stats(self):
        total_chars = sum(len(s['chars']) for s in self.students)
        self.teacher_stats_lbl.setText(f"{len(self.students)} students  ·  {total_chars} total characters")

    def _active_teacher_student(self):
        if not self.students:
            self.active_teacher_student_id = None
            return None
        st = next((s for s in self.students if s['id'] == self.active_teacher_student_id), None)
        if st is None:
            st = self.students[0]
            self.active_teacher_student_id = st['id']
        return st

    def _select_teacher_student(self, student_id: int):
        self.active_teacher_student_id = student_id
        self._rebuild_teacher_ui()

    def _td_toggle_conn(self):
        st = self._active_teacher_student()
        if st:
            self._toggle_roster_student_conn(st)

    def _td_test(self):
        st = self._active_teacher_student()
        if st:
            self._simulate_student_typing(st)

    def _td_export(self):
        st = self._active_teacher_student()
        if st:
            self.export_single_student_to_logs(st)

    def _td_clear(self):
        st = self._active_teacher_student()
        if st:
            self._clear_single_student(st)

    def _td_remove(self):
        st = self._active_teacher_student()
        if st:
            self._remove_single_student(st)

    def _update_single_student_card(self, student: dict):
        tab_btn = student.get('_tab_btn')
        if tab_btn is not None:
            dot = "●" if student['connected'] else "○"
            tab_btn.setText(f"{dot}  {student['name']}  ({len(student['chars'])})")
        active = self._active_teacher_student()
        if active and active['id'] == student['id'] and hasattr(self, 'teacher_doc_edit'):
            txt = ''.join(x['char'] for x in student['chars'])
            self.teacher_doc_edit.setPlainText(txt)
            self.teacher_doc_edit.moveCursor(QTextCursor.MoveOperation.End)
            self.td_mini_cell.set_chord(student.get('lastChord', 0))
            st_lbl = "Online" if student['connected'] else "Offline"
            self.td_sub_lbl.setText(
                f"{student['connType'].upper()} · {student.get('portName') or 'Unassigned'} · {st_lbl} · {len(student['chars'])} chars"
            )

    def _rebuild_teacher_ui(self):
        pal = ThemePalette.DARK if self.is_dark else ThemePalette.LIGHT
        self._update_teacher_stats()

        # 1. Rebuild Horizontal Student Document Tab Bar
        while self.teacher_tabs_layout.count():
            item = self.teacher_tabs_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        active = self._active_teacher_student()
        if not self.students:
            empty_tab = QLabel("No student documents yet — add a student above.")
            empty_tab.setProperty("muted", True)
            self.teacher_tabs_layout.addWidget(empty_tab)
            self.teacher_tabs_layout.addStretch(1)

            self.teacher_doc_hdr.setVisible(False)
            self.teacher_doc_edit.clear()
            self.teacher_doc_edit.setPlaceholderText(
                "Add a student above, connect their BrailleBridge over Bluetooth or USB, and their live document will appear here."
            )
            return

        self.teacher_doc_hdr.setVisible(True)
        for s in self.students:
            is_active = active and active['id'] == s['id']
            dot = "●" if s['connected'] else "○"
            btn = QPushButton(f"{dot}  {s['name']}  ({len(s['chars'])})")
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setFixedHeight(32)
            if is_active:
                btn.setStyleSheet(
                    f"QPushButton {{ background-color: {pal['navy']}; color: #ffffff; "
                    f"border: 1px solid {pal['navy']}; border-bottom: 3px solid {pal['gold']}; "
                    f"border-radius: 8px; padding: 4px 14px; font-weight: bold; }}"
                )
            else:
                btn.setStyleSheet(
                    f"QPushButton {{ background-color: {pal['bg_surface']}; color: {pal['text_primary']}; "
                    f"border: 1px solid {pal['border']}; border-radius: 8px; padding: 4px 12px; }}"
                    f"QPushButton:hover {{ background-color: {pal['bg_hover']}; }}"
                )
            btn.clicked.connect(lambda checked, sid=s['id']: self._select_teacher_student(sid))
            self.teacher_tabs_layout.addWidget(btn)
            s['_tab_btn'] = btn
        self.teacher_tabs_layout.addStretch(1)

        # 2. Populate Active Student's Word Paper Sheet
        self.td_avatar.setText(get_initials(active['name']))
        self.td_avatar.setStyleSheet(
            f"background-color: {pal['navy']}; color: #ffffff; border: 2px solid {pal['gold']}; "
            f"border-radius: 18px; font-weight: bold;"
        )
        self.td_name_lbl.setText(active['name'])
        st_lbl = "Online" if active['connected'] else "Offline"
        self.td_sub_lbl.setText(
            f"{active['connType'].upper()} · {active.get('portName') or 'Unassigned'} · {st_lbl} · {len(active['chars'])} chars"
        )
        self.td_mini_cell.set_theme(self.is_dark)
        self.td_mini_cell.set_chord(active.get('lastChord', 0))

        self.td_btn_conn.setVisible(not active.get('mirror'))
        self.td_btn_conn.setEnabled(not active.get('connecting'))
        self.td_btn_conn.setText(
            "..." if active.get('connecting') else ("Disconnect" if active['connected'] else "Connect")
        )
        self.td_btn_test.setIcon(svg_icon('play', pal['text_primary'], 13))
        self.td_btn_export.setIcon(svg_icon('upload', '#ffffff', 13))
        self.td_btn_remove.setIcon(svg_icon('trash', pal['red'], 13))

        txt = ''.join(x['char'] for x in active['chars'])
        self.teacher_doc_edit.setPlainText(txt)
        self.teacher_doc_edit.moveCursor(QTextCursor.MoveOperation.End)

    def _open_expand_student_dialog(self, student: dict):
        """Large 92%-viewport Live Expanded Student View Modal."""
        pal = ThemePalette.DARK if self.is_dark else ThemePalette.LIGHT
        dlg = QDialog(self)
        dlg.setWindowTitle(f"{student['name']} — Expanded Student View")
        dlg.resize(int(self.width() * 0.92), int(self.height() * 0.88))
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(14)

        hdr = QHBoxLayout()
        hdr.setSpacing(10)
        title = QLabel(f"{student['name']}  ·  Live Expanded Stream")
        title.setFont(ui_font(20, QFont.Weight.Bold))
        hdr.addWidget(title)

        stats_lbl = QLabel(f"{len(student['chars'])} chars")
        stats_lbl.setProperty("muted", True)
        hdr.addWidget(stats_lbl)
        hdr.addStretch(1)

        font_sz = [24]
        big_text = QTextEdit()
        big_text.setReadOnly(True)
        big_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        big_text.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        big_text.setFont(ui_font(font_sz[0]))

        def _zoom(delta: int):
            font_sz[0] = max(14, min(42, font_sz[0] + delta))
            big_text.setFont(ui_font(font_sz[0]))

        btn_zm_out = QPushButton("A-")
        btn_zm_out.setFixedSize(36, 36)
        btn_zm_out.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_zm_out.clicked.connect(lambda: _zoom(-3))
        hdr.addWidget(btn_zm_out)

        btn_zm_in = QPushButton("A+")
        btn_zm_in.setFixedSize(36, 36)
        btn_zm_in.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_zm_in.clicked.connect(lambda: _zoom(3))
        hdr.addWidget(btn_zm_in)

        btn_to_logs = QPushButton("Export & View in Logs")
        btn_to_logs.setIcon(svg_icon('upload', '#ffffff', 14))
        btn_to_logs.setIconSize(QSize(14, 14))
        btn_to_logs.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_to_logs.setStyleSheet(
            f"QPushButton {{ background-color: {pal['gold']}; color: #ffffff; "
            f"border: 1px solid {pal['gold_dark']}; border-radius: 14px; padding: 6px 14px; font-weight: 600; }}"
            f"QPushButton:hover {{ background-color: {pal['gold_dark']}; }}"
        )
        btn_to_logs.setFixedHeight(36)
        btn_to_logs.clicked.connect(lambda: (
            self.export_single_student_to_logs(student),
            dlg.accept(),
            self.switch_mode('logs')
        ))
        hdr.addWidget(btn_to_logs)

        btn_close = QPushButton("Close")
        btn_close.setIcon(svg_icon('x', pal['text_primary'], 14))
        btn_close.setIconSize(QSize(14, 14))
        btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_close.setFixedHeight(36)
        btn_close.clicked.connect(dlg.accept)
        hdr.addWidget(btn_close)
        lay.addLayout(hdr)

        last_len = [-1]
        def _sync_live():
            cur_len = len(student['chars'])
            if cur_len != last_len[0]:
                last_len[0] = cur_len
                full_str = ''.join(x['char'] for x in student['chars'])
                big_text.setPlainText(full_str if full_str else "Waiting for student input...")
                words = len(full_str.split()) if full_str.strip() else 0
                stats_lbl.setText(f"{words} words · {cur_len} chars")
                big_text.moveCursor(QTextCursor.MoveOperation.End)

        _sync_live()
        live_timer = QTimer(dlg)
        live_timer.timeout.connect(_sync_live)
        live_timer.start(150)

        lay.addWidget(big_text, 1)
        dlg.exec()

    # ================================================================ LOGS VIEW & SMART CONDITIONAL FORMATTING
    def export_single_student_to_logs(self, student: dict):
        chars = student.get('chars', [])
        if not chars:
            self.show_toast(f"{student['name']} has no text to export yet.")
            return
        self._save_student_log_entry(
            student_name=student['name'],
            color=student.get('color', '#d29a4a'),
            conn_info=f"{student.get('connType', 'bluetooth').upper()} · {student.get('baud', 115200)} baud",
            chars=chars,
        )
        self._save_persisted_logs()
        self.show_toast(f"Saved {student['name']}'s writing to Logs!")
        if self.current_mode == 'logs':
            self._rebuild_logs_ui()

    def export_all_to_logs(self):
        """Export All button handler (works from both Student View and Teacher View).
        Saves each student's writing into the Student Logs record so clicking a student
        in the Logs tab displays everything they wrote that day."""
        exported_count = 0

        # 1. If Student View has characters (and isn't already mirrored), record Student View
        if self.student_chars and self.mirror_student_id is None:
            self._save_student_log_entry(
                student_name="Student View",
                color="#d29a4a",
                conn_info=f"Direct ({self.student_port or 'Local'})",
                chars=self.student_chars,
            )
            exported_count += 1

        # 2. Export every student in Teacher Roster
        for s in self.students:
            if s['chars']:
                self._save_student_log_entry(
                    student_name=s['name'],
                    color=s.get('color', '#5a8ae0'),
                    conn_info=f"{s.get('connType', 'bluetooth').upper()} · {s.get('baud', 115200)} baud",
                    chars=s['chars'],
                )
                exported_count += 1

        # Also flush hardware relay logs to disk
        self.relay.save_all_logs()
        self._save_persisted_logs()

        if exported_count == 0:
            self.show_toast("No new student writing to export yet — type some text first!")
        else:
            self.show_toast(f"Exported {exported_count} student log(s) to the Logs tab!")
            if self.current_mode == 'logs':
                self._rebuild_logs_ui()

    def _save_student_log_entry(self, student_name: str, color: str, conn_info: str, chars: list):
        blocks = SmartFormatter.format_blocks(chars)
        plain_text = ''.join(x['char'] if isinstance(x, dict) else str(x) for x in chars)
        word_count = len(plain_text.split()) if plain_text.strip() else 0
        now_ms = int(time.time() * 1000)
        entry = {
            'id': f"log_{now_ms}_{len(self.student_logs)}",
            'studentName': student_name,
            'color': color,
            'connInfo': conn_info,
            'charsCount': len(chars),
            'wordCount': word_count,
            'blocks': blocks,
            'created': now_ms,
            'dateStr': datetime.fromtimestamp(now_ms / 1000.0).strftime('%b %d, %Y'),
            'timeStr': datetime.fromtimestamp(now_ms / 1000.0).strftime('%H:%M:%S'),
        }
        self.student_logs.insert(0, entry)
        self.selected_log_student = student_name

    def _get_student_directory_groups(self):
        """Aggregate all students from saved logs + active roster so the Logs tab
        always lists every student and their writing."""
        groups = {}

        # 1. From saved exports/logs
        for entry in self.student_logs:
            sname = entry.get('studentName') or 'Student'
            if sname not in groups:
                groups[sname] = {
                    'name': sname,
                    'color': entry.get('color', '#d29a4a'),
                    'connInfo': entry.get('connInfo', 'Bluetooth'),
                    'sessions': [],
                }
            groups[sname]['sessions'].append(entry)

        # 2. Also include active roster students (even if not exported yet, or with live chars)
        for idx, s in enumerate(self.students):
            sname = s['name']
            if sname not in groups:
                groups[sname] = {
                    'name': sname,
                    'color': s.get('color', STUDENT_COLORS[idx % len(STUDENT_COLORS)]),
                    'connInfo': f"{s['connType'].upper()} · {s['baud']} baud",
                    'sessions': [],
                }
            if s['chars'] and not groups[sname]['sessions']:
                blocks = SmartFormatter.format_blocks(s['chars'])
                plain = ''.join(x['char'] for x in s['chars'])
                groups[sname]['sessions'].append({
                    'id': f"live_{s['id']}",
                    'studentName': sname,
                    'color': s['color'],
                    'connInfo': f"{s['connType'].upper()} (Live)",
                    'charsCount': len(s['chars']),
                    'wordCount': len(plain.split()) if plain.strip() else 0,
                    'blocks': blocks,
                    'created': int(time.time() * 1000),
                    'dateStr': datetime.now().strftime('%b %d, %Y'),
                    'timeStr': 'Live Session',
                })

        # 3. Also include Student View if it has live chars and no saved logs yet
        if self.student_chars and 'Student View' not in groups:
            blocks = SmartFormatter.format_blocks(self.student_chars)
            plain = ''.join(x['char'] for x in self.student_chars)
            groups['Student View'] = {
                'name': 'Student View',
                'color': '#d29a4a',
                'connInfo': 'Student Tab (Live)',
                'sessions': [{
                    'id': 'live_student_view',
                    'studentName': 'Student View',
                    'color': '#d29a4a',
                    'connInfo': 'Student Tab (Live)',
                    'charsCount': len(self.student_chars),
                    'wordCount': len(plain.split()) if plain.strip() else 0,
                    'blocks': blocks,
                    'created': int(time.time() * 1000),
                    'dateStr': datetime.now().strftime('%b %d, %Y'),
                    'timeStr': 'Live Session',
                }]
            }

        return list(groups.values())

    def _rebuild_logs_ui(self):
        pal = ThemePalette.DARK if self.is_dark else ThemePalette.LIGHT
        groups = self._get_student_directory_groups()

        # Clear student list on left
        while self.logs_students_layout.count():
            item = self.logs_students_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not groups:
            empty = QLabel(
                "No student records yet.\n\n"
                "Click 'Export All' in the Student or Teacher tab "
                "to record student writing here."
            )
            empty.setWordWrap(True)
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setProperty("muted", True)
            self.logs_students_layout.addWidget(empty)
            self.logs_students_layout.addStretch(1)
            self._render_log_document_blocks([])
            return

        if not self.selected_log_student or not any(g['name'] == self.selected_log_student for g in groups):
            self.selected_log_student = groups[0]['name']

        for g in groups:
            is_sel = (g['name'] == self.selected_log_student)
            sessions = g['sessions']
            total_words = sum(s.get('wordCount', 0) for s in sessions)
            total_chars = sum(s.get('charsCount', 0) for s in sessions)
            latest_date = sessions[0].get('dateStr', 'Today') if sessions else 'No writing yet'

            # Preview snippet
            snippet = "No writing exported yet"
            if sessions and sessions[0].get('blocks'):
                snippet = sessions[0]['blocks'][0].get('text', '')[:65]

            card_btn = QFrame()
            card_btn.setObjectName("LogStudentCard")
            card_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            border_col = pal['gold'] if is_sel else pal['border']
            bg_col = pal['gold_bg'] if is_sel else pal['bg_surface']
            card_btn.setStyleSheet(
                f"QFrame#LogStudentCard {{ background-color: {bg_col}; border: 1.5px solid {border_col}; "
                f"border-radius: 16px; }}"
            )
            c_lay = QHBoxLayout(card_btn)
            c_lay.setContentsMargins(12, 10, 12, 10)
            c_lay.setSpacing(10)

            av = QLabel(get_initials(g['name']))
            av.setFixedSize(36, 36)
            av.setAlignment(Qt.AlignmentFlag.AlignCenter)
            av.setStyleSheet(
                f"background-color: {g.get('color', pal['gold'])}; color: #ffffff; "
                f"border-radius: 18px; font-weight: bold; font-size: 12px; border: none;"
            )
            c_lay.addWidget(av, 0, Qt.AlignmentFlag.AlignTop)

            info_col = QVBoxLayout()
            info_col.setSpacing(2)
            nm_lbl = QLabel(g['name'])
            nm_lbl.setFont(ui_font(11, QFont.Weight.Bold))
            meta_lbl = QLabel(f"{len(sessions)} session(s) · {total_words} words ({total_chars} chars) · {latest_date}")
            meta_lbl.setStyleSheet(f"color: {pal['text_secondary']}; font-size: 11px;")
            snip_lbl = QLabel(f"\"{snippet}\"")
            snip_lbl.setWordWrap(True)
            snip_lbl.setStyleSheet(f"color: {pal['text_muted']}; font-size: 11px; font-style: italic;")
            info_col.addWidget(nm_lbl)
            info_col.addWidget(meta_lbl)
            info_col.addWidget(snip_lbl)
            c_lay.addLayout(info_col, 1)

            card_btn.mousePressEvent = lambda ev, name=g['name']: self._select_log_student(name)
            self.logs_students_layout.addWidget(card_btn)

        self.logs_students_layout.addStretch(1)
        self._populate_selected_student_sessions()

    def _select_log_student(self, student_name: str):
        self.selected_log_student = student_name
        self.selected_log_session_id = None
        self.log_translated_blocks = None
        self.log_translated_label = None
        self._rebuild_logs_ui()

    def _populate_selected_student_sessions(self):
        pal = ThemePalette.DARK if self.is_dark else ThemePalette.LIGHT
        groups = self._get_student_directory_groups()
        grp = next((g for g in groups if g['name'] == self.selected_log_student), None)
        if not grp:
            return

        sessions = grp['sessions']
        self.log_doc_title.setText(f"{grp['name']}")
        total_words = sum(s.get('wordCount', 0) for s in sessions)
        total_chars = sum(s.get('charsCount', 0) for s in sessions)
        self.log_doc_meta.setText(f"  ·  {len(sessions)} Session(s)  ·  {total_words} Words  ·  {total_chars} Chars")

        self.log_session_combo.blockSignals(True)
        self.log_session_combo.clear()
        self.log_session_combo.addItem(
            svg_icon('calendar', pal['gold'], 13),
            f"All Writing ({len(sessions)} sessions)",
            "ALL",
        )
        for s in sessions:
            self.log_session_combo.addItem(
                svg_icon('clock', pal['text_secondary'], 13),
                f"{s.get('dateStr', '')} at {s.get('timeStr', '')} ({s.get('wordCount', 0)} words)",
                s['id']
            )
        if self.selected_log_session_id:
            idx = self.log_session_combo.findData(self.selected_log_session_id)
            if idx >= 0:
                self.log_session_combo.setCurrentIndex(idx)
        self.log_session_combo.blockSignals(False)

        self._render_selected_student_log()

    def _on_log_session_changed(self):
        self.selected_log_session_id = self.log_session_combo.currentData()
        self.log_translated_blocks = None
        self.log_translated_label = None
        self._render_selected_student_log()

    def _get_current_student_blocks(self) -> list:
        groups = self._get_student_directory_groups()
        grp = next((g for g in groups if g['name'] == self.selected_log_student), None)
        if not grp:
            return []
        sessions = grp['sessions']
        sel_id = self.selected_log_session_id
        if not sel_id or sel_id == "ALL":
            # Combine blocks across sessions in chronological order
            combined = []
            for s in reversed(sessions):
                combined.extend(s.get('blocks', []))
            return combined
        target = next((s for s in sessions if s['id'] == sel_id), None)
        return target.get('blocks', []) if target else []

    def _render_selected_student_log(self):
        blocks = self.log_translated_blocks if self.log_translated_blocks is not None else self._get_current_student_blocks()
        self._render_log_document_blocks(blocks)

    def _render_log_document_blocks(self, blocks: list):
        """Render the student's writing in a nice, big editorial layout with
        Smart Conditional Formatting (Title, Section Heading, Question, Answer,
        Math Expression, Highlight Callout, Lists, and Large Prose Paragraphs)."""
        pal = ThemePalette.DARK if self.is_dark else ThemePalette.LIGHT

        while self.log_doc_layout.count():
            item = self.log_doc_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if self.log_translated_label:
            banner = QLabel(f"Translated Document ({self.log_translated_label})")
            banner.setStyleSheet(
                f"background-color: {pal['gold_bg']}; color: {pal['gold']}; "
                f"border: 1px solid {pal['gold']}; border-radius: 8px; padding: 8px 12px; font-weight: bold;"
            )
            self.log_doc_layout.addWidget(banner)

        if not blocks:
            empty = QLabel(
                "No writing recorded for this student yet.\n"
                "Have the student type in Student or Teacher view, then click 'Export All'."
            )
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setFont(ui_font(15))
            empty.setProperty("muted", True)
            self.log_doc_layout.addWidget(empty)
            self.log_doc_layout.addStretch(1)
            return

        if self.log_raw_mode:
            raw_box = QTextEdit()
            raw_box.setReadOnly(True)
            raw_box.setFont(ui_font(18))
            raw_box.setPlainText(SmartFormatter.to_plain_text(blocks))
            self.log_doc_layout.addWidget(raw_box, 1)
            return

        num_counter = 0
        for b in blocks:
            btype = b.get('type', 'para')
            text = b.get('text', '')
            badge = b.get('badge', '')

            if btype not in ('numbered',):
                num_counter = 0

            if btype == 'title':
                card = QFrame()
                card.setStyleSheet(
                    f"background-color: {pal['bg_surface']}; "
                    f"border-bottom: 3px solid {pal['gold']}; border-radius: 10px; padding: 14px;"
                )
                v = QVBoxLayout(card)
                tag = QLabel("DOCUMENT TITLE")
                tag.setStyleSheet(f"color: {pal['gold']}; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
                lbl = QLabel(text)
                lbl.setWordWrap(True)
                lbl.setFont(ui_font(24, QFont.Weight.Bold))
                v.addWidget(tag)
                v.addWidget(lbl)
                self.log_doc_layout.addWidget(card)

            elif btype == 'heading':
                card = QFrame()
                card.setStyleSheet(
                    f"background-color: {pal['bg_surface']}; "
                    f"border-left: 4px solid {pal['gold']}; border-radius: 8px; padding: 10px 14px;"
                )
                v = QVBoxLayout(card)
                tag = QLabel(badge or "SECTION")
                tag.setStyleSheet(f"color: {pal['gold']}; font-size: 10px; font-weight: bold;")
                lbl = QLabel(text)
                lbl.setWordWrap(True)
                lbl.setFont(ui_font(19, QFont.Weight.Bold))
                v.addWidget(tag)
                v.addWidget(lbl)
                self.log_doc_layout.addWidget(card)

            elif btype == 'question':
                card = QFrame()
                card.setObjectName("SmartCard")
                card.setStyleSheet(
                    f"QFrame#SmartCard {{ background-color: {pal['bg_surface']}; "
                    f"border-left: 5px solid {pal['blue']}; border-radius: 16px; padding: 14px 18px; }}"
                )
                v = QVBoxLayout(card)
                tag = SectionHeader("help_circle", "QUESTION")
                tag.set_color(pal['blue'])
                lbl = QLabel(text)
                lbl.setWordWrap(True)
                lbl.setFont(ui_font(17, QFont.Weight.DemiBold))
                v.addWidget(tag)
                v.addWidget(lbl)
                self.log_doc_layout.addWidget(card)

            elif btype == 'answer':
                card = QFrame()
                card.setObjectName("SmartCard")
                card.setStyleSheet(
                    f"QFrame#SmartCard {{ background-color: {pal['bg_surface']}; "
                    f"border-left: 5px solid {pal['green']}; border-radius: 16px; padding: 14px 18px; }}"
                )
                v = QVBoxLayout(card)
                tag = SectionHeader("check_circle", "ANSWER")
                tag.set_color(pal['green'])
                lbl = QLabel(text)
                lbl.setWordWrap(True)
                lbl.setFont(ui_font(17))
                v.addWidget(tag)
                v.addWidget(lbl)
                self.log_doc_layout.addWidget(card)

            elif btype == 'math':
                card = QFrame()
                card.setObjectName("SmartCard")
                card.setStyleSheet(
                    f"QFrame#SmartCard {{ background-color: {pal['bg_surface']}; "
                    f"border-left: 5px solid {pal['teal']}; border-radius: 16px; padding: 14px 18px; }}"
                )
                v = QVBoxLayout(card)
                tag = SectionHeader("hash", "MATH & CALCULATION")
                tag.set_color(pal['teal'])
                lbl = QLabel(text)
                lbl.setWordWrap(True)
                lbl.setFont(QFont("Cambria Math", 19, QFont.Weight.Bold))
                v.addWidget(tag)
                v.addWidget(lbl)
                self.log_doc_layout.addWidget(card)

            elif btype == 'callout':
                card = QFrame()
                card.setObjectName("SmartCard")
                card.setStyleSheet(
                    f"QFrame#SmartCard {{ background-color: {pal['gold_bg']}; "
                    f"border-left: 5px solid {pal['gold']}; border-radius: 16px; padding: 14px 18px; }}"
                )
                v = QVBoxLayout(card)
                tag = SectionHeader("bookmark", "IMPORTANT NOTE")
                tag.set_color(pal['gold'])
                lbl = QLabel(text)
                lbl.setWordWrap(True)
                lbl.setFont(ui_font(17, QFont.Weight.Medium))
                v.addWidget(tag)
                v.addWidget(lbl)
                self.log_doc_layout.addWidget(card)

            elif btype in ('bullet', 'numbered'):
                if btype == 'numbered':
                    num_counter += 1
                    prefix = f"{num_counter}."
                else:
                    prefix = "•"
                row_w = QFrame()
                row_w.setStyleSheet(
                    f"background-color: {pal['bg_surface']}; border-radius: 8px; padding: 8px 14px;"
                )
                h = QHBoxLayout(row_w)
                b_lbl = QLabel(prefix)
                b_lbl.setFont(ui_font(17, QFont.Weight.Bold))
                b_lbl.setStyleSheet(f"color: {pal['gold']};")
                b_lbl.setFixedWidth(28)
                t_lbl = QLabel(text)
                t_lbl.setWordWrap(True)
                t_lbl.setFont(ui_font(17))
                h.addWidget(b_lbl)
                h.addWidget(t_lbl, 1)
                self.log_doc_layout.addWidget(row_w)

            else:
                # Standard Big Readable Prose Paragraph
                p_card = QFrame()
                p_card.setStyleSheet(
                    f"background-color: {pal['bg_surface']}; border-radius: 10px; padding: 14px 18px;"
                )
                v = QVBoxLayout(p_card)
                lbl = QLabel(text)
                lbl.setWordWrap(True)
                lbl.setFont(ui_font(18))
                v.addWidget(lbl)
                self.log_doc_layout.addWidget(p_card)

        self.log_doc_layout.addStretch(1)

    def _toggle_log_raw_mode(self):
        self.log_raw_mode = not self.log_raw_mode
        self.btn_log_raw.setText("Formatted" if self.log_raw_mode else "Plain Text")
        self._render_selected_student_log()

    def _translate_current_log(self):
        pal = ThemePalette.DARK if self.is_dark else ThemePalette.LIGHT
        if self.log_translated_blocks is not None:
            self.log_translated_blocks = None
            self.log_translated_label = None
            self.btn_log_translate.setText("Translate")
            self.btn_log_translate.setIcon(svg_icon('globe', pal['text_primary'], 14))
            self._render_selected_student_log()
            return

        blocks = self._get_current_student_blocks()
        if not blocks:
            self.show_toast("Nothing to translate.")
            return

        target = self.log_trans_combo.currentData() or 'en'
        target_name = self.log_trans_combo.currentText()
        joined = "\n\n".join(b.get('text', '') for b in blocks)
        self.btn_log_translate.setText("Translating...")
        QApplication.processEvents()

        res = translate_text(joined, target)
        if res['ok']:
            parts = res['text'].split("\n\n")
            new_blocks = []
            for idx, b in enumerate(blocks):
                nb = dict(b)
                nb['text'] = parts[idx].strip() if idx < len(parts) else b['text']
                new_blocks.append(nb)
            self.log_translated_blocks = new_blocks
            self.log_translated_label = target_name
            self.btn_log_translate.setText("Original")
            self.btn_log_translate.setIcon(svg_icon('repeat', pal['text_primary'], 14))
            self._render_selected_student_log()
        else:
            self.btn_log_translate.setText("Translate")
            self.btn_log_translate.setIcon(svg_icon('globe', pal['text_primary'], 14))
            self.show_toast(res['error'] or "Translation failed.")

    def _download_current_log_txt(self):
        blocks = self.log_translated_blocks if self.log_translated_blocks is not None else self._get_current_student_blocks()
        if not blocks:
            self.show_toast("No log content to save.")
            return
        sname = (self.selected_log_student or 'Student').replace(' ', '_')
        default_path = os.path.join(LOGS_DIR, f"{sname}_formatted_log.txt")
        os.makedirs(LOGS_DIR, exist_ok=True)
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Formatted Student Log", default_path, "Text Files (*.txt)"
        )
        if path:
            content = (
                f"BrailleBridge Student Writing Record\n"
                f"Student: {self.selected_log_student}\n"
                f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"{'=' * 48}\n\n"
                + SmartFormatter.to_plain_text(blocks)
            )
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.show_toast(f"Saved to {os.path.basename(path)}!")

    def _clear_all_saved_logs(self):
        self.student_logs.clear()
        self._save_persisted_logs()
        self._rebuild_logs_ui()
        self.show_toast("Cleared saved log history.")

    # ================================================================ LEARN VIEW HANDLERS
    def _set_learner_lang(self, lang: str):
        self.learner_lang = lang
        self.is_bangla = (lang == 'bn')
        self._update_student_indicators()

    def _set_decoder_lang(self, lang: str):
        self.decoder_lang = lang
        self._update_chord_trainer()

    def _on_learner_input_edited(self, text: str):
        if not text:
            return
        last_ch = text[-1]
        is_bn = ('\u0980' <= last_ch <= '\u09ff') or (self.learner_lang == 'bn')
        if last_ch == ' ':
            words = text.strip().split()
            if words:
                w = words[-1]
                self.last_spoken_word = w
                self.learner_words.append(w)
                self.learner_words_lbl.setText("  ·  ".join(self.learner_words[-30:]))
                self.speech.speak(w, is_bn)
        else:
            self.speech.speak(last_ch, is_bn)

    def _repeat_learner_word(self):
        if self.last_spoken_word:
            is_bn = any('\u0980' <= c <= '\u09ff' for c in self.last_spoken_word)
            self.speech.speak(self.last_spoken_word, is_bn)

    def _clear_learner_playground(self):
        self.learner_input.clear()
        self.learner_words.clear()
        self.learner_words_lbl.setText("Spoken words appear here")

    def _export_learner_progress(self):
        if not self.learner_words:
            self.show_toast("Speak a word in the playground first.")
            return
        os.makedirs(LOGS_DIR, exist_ok=True)
        path = os.path.join(LOGS_DIR, f"Learner_Progress_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt")
        with open(path, 'w', encoding='utf-8') as f:
            f.write("BrailleBridge Learner Progress\n==============================\n\n")
            for idx, w in enumerate(self.learner_words, 1):
                f.write(f"{idx}. {w}\n")
        self.show_toast(f"Saved Learner Progress to logs/{os.path.basename(path)}!")

    def _update_chord_trainer(self):
        pal = ThemePalette.DARK if self.is_dark else ThemePalette.LIGHT
        while self.decoder_grid.count():
            item = self.decoder_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        text = self.decoder_input.text()
        if not text:
            lbl = QLabel("Type a word or phrase above to see each 6-dot Braille chord.")
            lbl.setProperty("muted", True)
            self.decoder_grid.addWidget(lbl)
            self.decoder_grid.addStretch(1)
            return

        steps = decode_text_to_steps(text, self.decoder_lang)
        for step in steps:
            box = QFrame()
            box.setProperty("subCard", True)
            box.setFixedWidth(92)
            v = QVBoxLayout(box)
            v.setContentsMargins(8, 8, 8, 8)
            v.setAlignment(Qt.AlignmentFlag.AlignCenter)

            ch_lbl = QLabel(step['char'])
            ch_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ch_lbl.setFont(ui_font(14, QFont.Weight.Bold))
            v.addWidget(ch_lbl)

            if step['type'] == 'chord':
                cell = MiniBrailleCell(step['chord'], size_scale=1.1, is_dark=self.is_dark)
                v.addWidget(cell, 0, Qt.AlignmentFlag.AlignCenter)
                dots_txt = "Dots " + ",".join(str(d) for d in step['dots'])
                if step.get('shift'):
                    dots_txt = "SHIFT + " + dots_txt
                d_lbl = QLabel(dots_txt)
                d_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                d_lbl.setStyleSheet(f"color: {pal['gold']}; font-size: 10px; font-weight: bold;")
                v.addWidget(d_lbl)
            elif step['type'] == 'space':
                sp_lbl = QLabel("Press\nSPACE")
                sp_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                sp_lbl.setProperty("muted", True)
                v.addWidget(sp_lbl)

            self.decoder_grid.addWidget(box)

        self.decoder_grid.addStretch(1)

    # ================================================================ ACCOUNT DIALOG
    def _open_account_dialog(self):
        pal = ThemePalette.DARK if self.is_dark else ThemePalette.LIGHT
        dlg = QDialog(self)
        dlg.setWindowTitle("Classroom & Teacher Profile")
        dlg.setFixedSize(440, 380)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(10)

        hdr_lbl = QLabel("Classroom Profile")
        hdr_lbl.setFont(ui_font(18, QFont.Weight.Bold))
        lay.addWidget(hdr_lbl)

        sub_lbl = QLabel("Customize your teacher name and school for exported logs and reports.")
        sub_lbl.setProperty("muted", True)
        sub_lbl.setWordWrap(True)
        lay.addWidget(sub_lbl)

        in_name = QLineEdit(self.teacher_name)
        in_name.setPlaceholderText("Teacher Name")
        in_name.setFixedHeight(36)
        lay.addWidget(in_name)

        in_school = QLineEdit(self.school_name)
        in_school.setPlaceholderText("School or Classroom Name")
        in_school.setFixedHeight(36)
        lay.addWidget(in_school)

        in_email = QLineEdit(self.teacher_email)
        in_email.setPlaceholderText("Teacher Email (optional)")
        in_email.setFixedHeight(36)
        lay.addWidget(in_email)

        total_chars = sum(len(s['chars']) for s in self.students) + len(self.student_chars)
        stats = QLabel(
            f"Active Roster Students: {len(self.students)}  ·  "
            f"Saved Logs: {len(self.student_logs)}  ·  "
            f"Characters: {total_chars}"
        )
        stats.setProperty("muted", True)
        stats.setWordWrap(True)
        lay.addWidget(stats)
        lay.addStretch(1)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedHeight(36)
        btn_cancel.clicked.connect(dlg.reject)
        btn_row.addWidget(btn_cancel)

        btn_save = QPushButton("Save Profile")
        btn_save.setStyleSheet(
            f"QPushButton {{ background-color: {pal['gold']}; color: #ffffff; "
            f"border: 1px solid {pal['gold_dark']}; border-radius: 14px; padding: 6px 16px; font-weight: 600; }}"
            f"QPushButton:hover {{ background-color: {pal['gold_dark']}; }}"
        )
        btn_save.setFixedHeight(36)

        def _save():
            self.teacher_name = in_name.text().strip() or "Teacher"
            self.school_name = in_school.text().strip() or "BrailleBridge Classroom"
            self.teacher_email = in_email.text().strip()
            self.profile_btn.setText(f"{get_initials(self.teacher_name)}  {self.teacher_name}")
            self._save_settings()
            dlg.accept()
            self.show_toast("Classroom profile saved.")

        btn_save.clicked.connect(_save)
        btn_row.addWidget(btn_save)
        lay.addLayout(btn_row)
        dlg.exec()

    # ================================================================ LIVE CHORD TIMING DIALOG
    def _open_timing_dialog(self):
        from PyQt6.QtWidgets import QSlider
        pal = ThemePalette.DARK if self.is_dark else ThemePalette.LIGHT
        dlg = QDialog(self)
        dlg.setWindowTitle("Live Chord Timing & Speed Tuning")
        dlg.setFixedSize(470, 390)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)

        hdr = QLabel("Hardware Chord Timing")
        hdr.setFont(ui_font(18, QFont.Weight.Bold))
        lay.addWidget(hdr)

        sub = QLabel(
            "Tune switch debounce and chord commit timing live over Bluetooth or USB Serial. "
            "Default uses instant decode-on-release (0 ms window) + 15 ms debounce for 100+ WPM Perkins typing."
        )
        sub.setProperty("muted", True)
        sub.setWordWrap(True)
        lay.addWidget(sub)

        # Debounce slider (5..50 ms)
        deb_lbl = QLabel(f"Switch Debounce: {self.chord_debounce_ms} ms  (default: 15 ms)")
        deb_lbl.setFont(ui_font(11, QFont.Weight.DemiBold))
        lay.addWidget(deb_lbl)

        deb_slider = QSlider(Qt.Orientation.Horizontal)
        deb_slider.setRange(5, 50)
        deb_slider.setValue(self.chord_debounce_ms)
        deb_slider.valueChanged.connect(
            lambda v: deb_lbl.setText(f"Switch Debounce: {v} ms  (default: 15 ms)")
        )
        lay.addWidget(deb_slider)

        # Window slider (0 = Decode on release, or 50..300 ms)
        def _win_text(v: int) -> str:
            if v == 0:
                return "Chord Window: Instant on Release (0 ms — Recommended / Default)"
            return f"Chord Window: {v} ms fixed timer (lags fast typists >{int(60000/(v*5))} WPM)"

        win_lbl = QLabel(_win_text(self.chord_window_ms))
        win_lbl.setFont(ui_font(11, QFont.Weight.DemiBold))
        lay.addWidget(win_lbl)

        win_slider = QSlider(Qt.Orientation.Horizontal)
        win_slider.setRange(0, 300)
        win_slider.setSingleStep(10)
        win_slider.setPageStep(20)
        win_slider.setValue(self.chord_window_ms)

        def _on_win_change(v: int):
            if 0 < v < 50:
                v = 50
                win_slider.blockSignals(True)
                win_slider.setValue(50)
                win_slider.blockSignals(False)
            win_lbl.setText(_win_text(v))

        win_slider.valueChanged.connect(_on_win_change)
        lay.addWidget(win_slider)
        lay.addStretch(1)

        btn_row = QHBoxLayout()
        btn_reset = QPushButton("Reset to Default")
        btn_reset.setFixedHeight(36)
        btn_reset.setToolTip("Restore decode-on-release (0 ms window) + 15 ms debounce")

        def _reset():
            deb_slider.setValue(15)
            win_slider.setValue(0)
            self.chord_debounce_ms = 15
            self.chord_window_ms = 0
            self._save_settings()
            cnt = self.relay.send_command("RESET_TIMING")
            self.show_toast(
                f"Reset to Default (Decode-on-Release + 15 ms) — sent to {cnt} device(s)"
            )
            dlg.accept()

        btn_reset.clicked.connect(_reset)
        btn_row.addWidget(btn_reset)

        btn_apply = QPushButton("Apply Live")
        btn_apply.setFixedHeight(36)
        btn_apply.setStyleSheet(
            f"QPushButton {{ background-color: {pal['gold']}; color: #ffffff; "
            f"border: 1px solid {pal['gold_dark']}; border-radius: 14px; padding: 6px 16px; font-weight: 600; }}"
            f"QPushButton:hover {{ background-color: {pal['gold_dark']}; }}"
        )

        def _apply():
            self.chord_debounce_ms = deb_slider.value()
            w = win_slider.value()
            self.chord_window_ms = 0 if w <= 0 else max(50, w)
            self._save_settings()
            c1 = self.relay.send_command(f"DEBOUNCE:{self.chord_debounce_ms}")
            c2 = self.relay.send_command(f"WINDOW:{self.chord_window_ms}")
            cnt = max(c1, c2)
            mode_str = "Decode-on-Release" if self.chord_window_ms == 0 else f"{self.chord_window_ms} ms window"
            self.show_toast(f"Timing applied ({self.chord_debounce_ms} ms debounce, {mode_str}) to {cnt} device(s)")
            dlg.accept()

        btn_apply.clicked.connect(_apply)
        btn_row.addWidget(btn_apply)
        lay.addLayout(btn_row)
        dlg.exec()

    # ================================================================ KEYBOARD SHORTCUTS & BLE KEYBOARD CAPTURE
    def keyPressEvent(self, event: QKeyEvent):
        if event.isAutoRepeat():
            return
        focused = QApplication.focusWidget()
        if isinstance(focused, QLineEdit):
            super().keyPressEvent(event)
            return

        key = event.key()
        mods = event.modifiers()
        txt = event.text()

        # Alt+L toggles language, Alt+S toggles shift
        if (mods & Qt.KeyboardModifier.AltModifier) and key == Qt.Key.Key_L:
            self._toggle_language()
            return
        if (mods & Qt.KeyboardModifier.AltModifier) and key == Qt.Key.Key_S:
            self._toggle_shift()
            return

        if self.current_mode == 'student':
            # When connected via USB Serial or BLE NUS, ignore OS HID keystrokes so
            # BLE HID + Serial/NUS never double-type the same character.
            if self.student_connected and self.student_port != "KEYBOARD":
                event.accept()
                return
            if key == Qt.Key.Key_Backspace:
                self._student_backspace()
                return
            if key == Qt.Key.Key_Space:
                if self.student_chord > 0:
                    self._commit_student_chord()
                else:
                    self._add_student_space()
                return
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if self.student_chord > 0:
                    self._commit_student_chord()
                return
            if txt in ('1', '2', '3', '4', '5', '6') and (
                (mods & Qt.KeyboardModifier.AltModifier) or bool(self.student_dots)
            ):
                self._toggle_student_dot(int(txt))
                return
            if txt and len(txt) == 1 and ord(txt) >= 32 and not (mods & Qt.KeyboardModifier.ControlModifier):
                self._append_student_char(txt)
                return

        super().keyPressEvent(event)

    def closeEvent(self, event):
        self._save_persisted_roster()
        self._save_persisted_logs()
        if hasattr(self, 'relay') and self.relay:
            self.relay.shutdown()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    win = BrailleBridgeWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
