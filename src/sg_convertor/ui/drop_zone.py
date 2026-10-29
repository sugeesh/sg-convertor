"""Dashed area that accepts dragged files and folders."""

from pathlib import Path

from PySide6.QtCore import QMimeData, Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


def local_paths(mime: QMimeData) -> list[Path]:
    return [Path(url.toLocalFile()) for url in mime.urls() if url.isLocalFile()]


class DropZone(QFrame):
    paths_dropped = Signal(list)  # list[Path]

    def __init__(self):
        super().__init__(objectName="drop")
        self.setAcceptDrops(True)
        self.setMinimumHeight(110)

        icon = QLabel("🎬  →  🎵", alignment=Qt.AlignCenter)
        icon.setStyleSheet("font-size: 28px;")
        heading = QLabel("Drag & drop MP4 files or folders here", alignment=Qt.AlignCenter)
        heading.setStyleSheet("font-size: 15px; font-weight: 600;")
        hint = QLabel(
            "or use the buttons below  •  MP4, M4V, MOV, MKV, WEBM, AVI",
            objectName="subtitle",
            alignment=Qt.AlignCenter,
        )

        layout = QVBoxLayout(self)
        for label in (icon, heading, hint):
            layout.addWidget(label)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._set_highlighted(True)

    def dragLeaveEvent(self, _event):
        self._set_highlighted(False)

    def dropEvent(self, event):
        self._set_highlighted(False)
        self.paths_dropped.emit(local_paths(event.mimeData()))

    def _set_highlighted(self, highlighted: bool) -> None:
        self.setProperty("hover", highlighted)
        self.style().unpolish(self)
        self.style().polish(self)
