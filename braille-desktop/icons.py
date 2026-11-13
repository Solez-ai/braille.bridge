"""Crisp Lucide-style SVG vector icon engine for BrailleBridge Desktop (PyQt6).

Renders monochrome vector SVG icons tinted to any theme color without using
any Unicode emojis.
"""
from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget

_ICON_PATHS = {
    'braille': (
        '<circle cx="8" cy="6" r="2.1" fill="currentColor" stroke="none"/>'
        '<circle cx="8" cy="12" r="2.1" fill="currentColor" stroke="none"/>'
        '<circle cx="8" cy="18" r="2.1" fill="currentColor" stroke="none"/>'
        '<circle cx="16" cy="6" r="2.1" fill="currentColor" stroke="none"/>'
        '<circle cx="16" cy="12" r="2.1" fill="currentColor" stroke="none"/>'
        '<circle cx="16" cy="18" r="2.1" fill="none" stroke="currentColor" stroke-width="1.8"/>'
    ),
    'monitor': (
        '<rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>'
        '<line x1="8" y1="21" x2="16" y2="21"/>'
        '<line x1="12" y1="17" x2="12" y2="21"/>'
    ),
    'users': (
        '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>'
        '<circle cx="9" cy="7" r="4"/>'
        '<path d="M23 21v-2a4 4 0 0 0-3-3.87"/>'
        '<path d="M16 3.13a4 4 0 0 1 0 7.75"/>'
    ),
    'user': (
        '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>'
        '<circle cx="12" cy="7" r="4"/>'
    ),
    'file_text': (
        '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
        '<polyline points="14 2 14 8 20 8"/>'
        '<line x1="16" y1="13" x2="8" y2="13"/>'
        '<line x1="16" y1="17" x2="8" y2="17"/>'
        '<polyline points="10 9 9 9 8 9"/>'
    ),
    'book_open': (
        '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>'
        '<path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>'
    ),
    'bluetooth': (
        '<polyline points="6.5 6.5 17.5 17.5 12 23 12 1 17.5 6.5 6.5 17.5"/>'
    ),
    'usb': (
        '<circle cx="10" cy="7" r="1"/>'
        '<circle cx="4" cy="20" r="1"/>'
        '<path d="M4.7 19.3 19 5"/>'
        '<path d="m21 3-3 1 2 2Z"/>'
        '<path d="M9.26 7.68 5 12l2 5"/>'
        '<path d="m10 14 5 2 3.5-3.5"/>'
        '<path d="m18 12 1-1 1 1-1 1Z"/>'
    ),
    'keyboard': (
        '<rect x="2" y="4" width="20" height="16" rx="2" ry="2"/>'
        '<path d="M6 8h.01"/><path d="M10 8h.01"/><path d="M14 8h.01"/><path d="M18 8h.01"/>'
        '<path d="M8 12h.01"/><path d="M12 12h.01"/><path d="M16 12h.01"/>'
        '<path d="M7 16h10"/>'
    ),
    'refresh': (
        '<polyline points="23 4 23 10 17 10"/>'
        '<path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>'
    ),
    'sun': (
        '<circle cx="12" cy="12" r="5"/>'
        '<line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>'
        '<line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>'
        '<line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>'
        '<line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>'
    ),
    'moon': (
        '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>'
    ),
    'volume_on': (
        '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>'
        '<path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>'
        '<path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>'
    ),
    'volume_off': (
        '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>'
        '<line x1="23" y1="9" x2="17" y2="15"/>'
        '<line x1="17" y1="9" x2="23" y2="15"/>'
    ),
    'globe': (
        '<circle cx="12" cy="12" r="10"/>'
        '<line x1="2" y1="12" x2="22" y2="12"/>'
        '<path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>'
    ),
    'send': (
        '<line x1="22" y1="2" x2="11" y2="13"/>'
        '<polygon points="22 2 15 22 11 13 2 9 22 2"/>'
    ),
    'expand': (
        '<polyline points="15 3 21 3 21 9"/>'
        '<polyline points="9 21 3 21 3 15"/>'
        '<line x1="21" y1="3" x2="14" y2="10"/>'
        '<line x1="3" y1="21" x2="10" y2="14"/>'
    ),
    'minimize': (
        '<polyline points="4 14 10 14 10 20"/>'
        '<polyline points="20 10 14 10 14 4"/>'
        '<line x1="14" y1="10" x2="21" y2="3"/>'
        '<line x1="3" y1="21" x2="10" y2="14"/>'
    ),
    'upload': (
        '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
        '<polyline points="17 8 12 3 7 8"/>'
        '<line x1="12" y1="3" x2="12" y2="15"/>'
    ),
    'download': (
        '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
        '<polyline points="7 10 12 15 17 10"/>'
        '<line x1="12" y1="15" x2="12" y2="3"/>'
    ),
    'trash': (
        '<polyline points="3 6 5 6 21 6"/>'
        '<path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>'
    ),
    'x': (
        '<line x1="18" y1="6" x2="6" y2="18"/>'
        '<line x1="6" y1="6" x2="18" y2="18"/>'
    ),
    'plus': (
        '<line x1="12" y1="5" x2="12" y2="19"/>'
        '<line x1="5" y1="12" x2="19" y2="12"/>'
    ),
    'play': (
        '<polygon points="5 3 19 12 5 21 5 3"/>'
    ),
    'repeat': (
        '<polyline points="17 1 21 5 17 9"/>'
        '<path d="M3 11V9a4 4 0 0 1 4-4h14"/>'
        '<polyline points="7 23 3 19 7 15"/>'
        '<path d="M21 13v2a4 4 0 0 1-4 4H3"/>'
    ),
    'save': (
        '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>'
        '<polyline points="17 21 17 13 7 13 7 21"/>'
        '<polyline points="7 3 7 8 15 8"/>'
    ),
    'code': (
        '<polyline points="16 18 22 12 16 6"/>'
        '<polyline points="8 6 2 12 8 18"/>'
    ),
    'clock': (
        '<circle cx="12" cy="12" r="10"/>'
        '<polyline points="12 6 12 12 16 14"/>'
    ),
    'calendar': (
        '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>'
        '<line x1="16" y1="2" x2="16" y2="6"/>'
        '<line x1="8" y1="2" x2="8" y2="6"/>'
        '<line x1="3" y1="10" x2="21" y2="10"/>'
    ),
    'check': (
        '<polyline points="20 6 9 17 4 12"/>'
    ),
    'check_circle': (
        '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>'
        '<polyline points="22 4 12 14.01 9 11.01"/>'
    ),
    'help_circle': (
        '<circle cx="12" cy="12" r="10"/>'
        '<path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>'
        '<line x1="12" y1="17" x2="12.01" y2="17"/>'
    ),
    'alert': (
        '<circle cx="12" cy="12" r="10"/>'
        '<line x1="12" y1="8" x2="12" y2="12"/>'
        '<line x1="12" y1="16" x2="12.01" y2="16"/>'
    ),
    'hash': (
        '<line x1="4" y1="9" x2="20" y2="9"/>'
        '<line x1="4" y1="15" x2="20" y2="15"/>'
        '<line x1="10" y1="3" x2="8" y2="21"/>'
        '<line x1="16" y1="3" x2="14" y2="21"/>'
    ),
    'bookmark': (
        '<path d="m19 21-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>'
    ),
    'return_key': (
        '<polyline points="9 10 4 15 9 20"/>'
        '<path d="M20 4v7a4 4 0 0 1-4 4H4"/>'
    ),
    'delete': (
        '<path d="M21 4H8l-7 8 7 8h13a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2z"/>'
        '<line x1="18" y1="9" x2="12" y2="15"/>'
        '<line x1="12" y1="9" x2="18" y2="15"/>'
    ),
    'arrow_up': (
        '<line x1="12" y1="19" x2="12" y2="5"/>'
        '<polyline points="5 12 12 5 19 12"/>'
    ),
    'eye': (
        '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>'
        '<circle cx="12" cy="12" r="3"/>'
    ),
}

_PIXMAP_CACHE: dict[tuple[str, str, int], QPixmap] = {}


def svg_pixmap(name: str, color: str = '#f5f5f7', size: int = 16) -> QPixmap:
    key = (name, color, size)
    cached = _PIXMAP_CACHE.get(key)
    if cached is not None:
        return cached

    inner = _ICON_PATHS.get(name, _ICON_PATHS['file_text'])
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round">{inner}</svg>'
    ).replace('currentColor', color)

    renderer = QSvgRenderer(QByteArray(svg.encode('utf-8')))
    dpr = 2
    pm = QPixmap(size * dpr, size * dpr)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    renderer.render(painter)
    painter.end()
    pm.setDevicePixelRatio(dpr)
    _PIXMAP_CACHE[key] = pm
    return pm


def svg_icon(name: str, color: str = '#f5f5f7', size: int = 16) -> QIcon:
    return QIcon(svg_pixmap(name, color, size))


class SectionHeader(QWidget):
    """Clean overline header with a crisp vector icon + uppercase title."""

    def __init__(self, icon_name: str, title: str, parent=None):
        super().__init__(parent)
        self.icon_name = icon_name
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(7)

        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(15, 15)
        lay.addWidget(self.icon_lbl)

        self.text_lbl = QLabel(title)
        self.text_lbl.setProperty("overline", True)
        lay.addWidget(self.text_lbl)
        lay.addStretch(1)

    def set_color(self, color: str):
        self.icon_lbl.setPixmap(svg_pixmap(self.icon_name, color, 14))
        self.text_lbl.setStyleSheet(
            f"color: {color}; font-size: 11px; font-weight: bold; letter-spacing: 0.8px;"
        )
