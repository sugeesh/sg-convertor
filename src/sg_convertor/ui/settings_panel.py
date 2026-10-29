"""Card with the format, quality and output-folder controls."""

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from sg_convertor.models import BITRATES, DEFAULT_BITRATE, AudioFormat, ConversionSettings

_FORMATS = list(AudioFormat)
_BITRATE_HINTS = {"320k": "best", "192k": "recommended", "96k": "smallest"}


def _bitrate_label(bitrate: str) -> str:
    label = f"{bitrate.removesuffix('k')} kbps"
    hint = _BITRATE_HINTS.get(bitrate)
    return f"{label}  ({hint})" if hint else label


def _section(text: str) -> QLabel:
    return QLabel(text.upper(), objectName="section")


class SettingsPanel(QFrame):
    open_output_requested = Signal()

    def __init__(self):
        super().__init__(objectName="card")
        self._format_group = QButtonGroup(self)
        self._quality = QComboBox()
        self._output_dir = QLineEdit(placeholderText="Same folder as each source file")
        self._browse = QPushButton("Browse…")
        self._open = QPushButton("Open")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 16)
        layout.setSpacing(10)
        layout.addLayout(self._build_format_and_quality_row())
        layout.addWidget(_section("Output folder"))
        layout.addLayout(self._build_output_row())

    def settings(self) -> ConversionSettings:
        output_dir = self._output_dir.text().strip()
        return ConversionSettings(
            audio_format=_FORMATS[self._format_group.checkedId()],
            bitrate=self._quality.currentData(),
            output_dir=Path(output_dir).expanduser() if output_dir else None,
        )

    def set_locked(self, locked: bool) -> None:
        for widget in (
            self._quality,
            self._output_dir,
            self._browse,
            *self._format_group.buttons(),
        ):
            widget.setEnabled(not locked)

    def _build_format_and_quality_row(self) -> QHBoxLayout:
        format_buttons = QHBoxLayout()
        for format_id, audio_format in enumerate(_FORMATS):
            button = QPushButton(audio_format.name, objectName="toggle", checkable=True)
            self._format_group.addButton(button, format_id)
            format_buttons.addWidget(button)
        self._format_group.button(0).setChecked(True)

        for bitrate in BITRATES:
            self._quality.addItem(_bitrate_label(bitrate), bitrate)
        self._quality.setCurrentIndex(BITRATES.index(DEFAULT_BITRATE))

        format_column = QVBoxLayout()
        format_column.addWidget(_section("Format"))
        format_column.addLayout(format_buttons)

        quality_column = QVBoxLayout()
        quality_column.addWidget(_section("Quality"))
        quality_column.addWidget(self._quality)

        row = QHBoxLayout()
        row.addLayout(format_column)
        row.addSpacing(24)
        row.addLayout(quality_column)
        row.addStretch()
        return row

    def _build_output_row(self) -> QHBoxLayout:
        self._browse.clicked.connect(self._choose_output_dir)
        self._open.clicked.connect(self.open_output_requested)

        row = QHBoxLayout()
        row.addWidget(self._output_dir, 1)
        row.addWidget(self._browse)
        row.addWidget(self._open)
        return row

    def _choose_output_dir(self) -> None:
        start = self._output_dir.text() or str(Path.home())
        folder = QFileDialog.getExistingDirectory(self, "Choose output folder", start)
        if folder:
            self._output_dir.setText(folder)
