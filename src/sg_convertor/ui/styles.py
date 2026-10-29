"""Colours and the application-wide Qt stylesheet."""

from string import Template


class Palette:
    BACKGROUND = "#14161c"
    SURFACE = "#1c1f27"
    SURFACE_RAISED = "#262a36"
    BORDER = "#2a2e3a"
    BORDER_STRONG = "#333849"
    TEXT = "#e6e8ee"
    TEXT_MUTED = "#8a90a2"
    ACCENT = "#7c5cff"
    ACCENT_2 = "#4f8bff"
    INFO = "#7c9cff"
    SUCCESS = "#4ade80"
    WARNING = "#e0b050"
    ERROR = "#ff6b81"


_STYLESHEET = Template("""
* { font-family: "Inter", "Segoe UI", "Ubuntu", sans-serif; font-size: 14px; }
QWidget#root { background: $BACKGROUND; }
QLabel { color: $TEXT; }
QLabel#title { font-size: 24px; font-weight: 700; color: #ffffff; }
QLabel#subtitle { color: $TEXT_MUTED; }
QLabel#section { color: $TEXT_MUTED; font-size: 12px; font-weight: 600; }

QFrame#card { background: $SURFACE; border: 1px solid $BORDER; border-radius: 14px; }
QFrame#drop { background: $SURFACE; border: 2px dashed #3a3f50; border-radius: 14px; }
QFrame#drop[hover="true"] { border-color: $ACCENT; background: #221f33; }

QPushButton {
    background: $SURFACE_RAISED; color: $TEXT; border: 1px solid $BORDER_STRONG;
    border-radius: 10px; padding: 9px 16px;
}
QPushButton:hover { background: #2f3443; }
QPushButton:disabled { color: #5c6170; background: #1f222b; }
QPushButton#primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 $ACCENT, stop:1 $ACCENT_2);
    border: none; color: white; font-weight: 700; padding: 12px 28px;
}
QPushButton#primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8d71ff, stop:1 #649aff);
}
QPushButton#primary:disabled { background: #2b2f3c; color: #6b7080; }
QPushButton#danger { background: #3a1f26; border-color: #5a2a35; color: #ff9aa9; }
QPushButton#danger:hover { background: #4a2530; }
QPushButton#toggle { padding: 10px 26px; font-weight: 600; }
QPushButton#toggle:checked { background: $ACCENT; border-color: $ACCENT; color: white; }

QComboBox, QLineEdit {
    background: $BACKGROUND; color: $TEXT; border: 1px solid $BORDER_STRONG;
    border-radius: 8px; padding: 7px 10px;
}
QComboBox QAbstractItemView {
    background: $SURFACE; color: $TEXT; selection-background-color: $ACCENT;
}

QTableWidget {
    background: $SURFACE; color: $TEXT; border: 1px solid $BORDER; border-radius: 14px;
    gridline-color: transparent; selection-background-color: #2b2c45;
}
QTableWidget::item { padding: 6px; border-bottom: 1px solid #23262f; }
QHeaderView::section {
    background: $SURFACE; color: $TEXT_MUTED; border: none;
    border-bottom: 1px solid $BORDER; padding: 8px; font-weight: 600;
}

QProgressBar {
    background: $BACKGROUND; border: none; border-radius: 6px;
    text-align: center; color: $TEXT; font-size: 11px;
}
QProgressBar::chunk {
    border-radius: 6px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 $ACCENT, stop:1 $ACCENT_2);
}
QProgressBar#overall { max-height: 16px; }

QScrollBar:vertical { background: transparent; width: 10px; }
QScrollBar::handle:vertical { background: $BORDER_STRONG; border-radius: 5px; min-height: 30px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
""")

STYLESHEET = _STYLESHEET.substitute(
    {name: value for name, value in vars(Palette).items() if name.isupper()}
)
