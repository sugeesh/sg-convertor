"""Table listing the queued videos with per-file progress and status."""

from enum import Enum, IntEnum
from pathlib import Path

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from sg_convertor.ui.styles import Palette


class Column(IntEnum):
    NAME = 0
    SIZE = 1
    PROGRESS = 2
    STATUS = 3


class RowStatus(Enum):
    READY = ("Ready", Palette.TEXT_MUTED)
    QUEUED = ("Queued", Palette.TEXT_MUTED)
    CONVERTING = ("Converting", Palette.INFO)
    DONE = ("✓ Done", Palette.SUCCESS)
    FAILED = ("✗ Failed", Palette.ERROR)
    CANCELLED = ("Cancelled", Palette.WARNING)
    SKIPPED = ("Skipped", Palette.TEXT_MUTED)

    def __init__(self, label: str, color: str):
        self.label = label
        self.color = color


def human_size(size: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


class FileTable(QTableWidget):
    """Owns the list of source files; row ``i`` always shows ``paths()[i]``."""

    def __init__(self):
        super().__init__(0, len(Column))
        self._paths: list[Path] = []
        self.setHorizontalHeaderLabels(["File", "Size", "Progress", "Status"])
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(40)
        self.setShowGrid(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

        header = self.horizontalHeader()
        header.setSectionResizeMode(Column.NAME, QHeaderView.Stretch)
        header.setSectionResizeMode(Column.SIZE, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(Column.PROGRESS, QHeaderView.Fixed)
        header.setSectionResizeMode(Column.STATUS, QHeaderView.Fixed)
        self.setColumnWidth(Column.PROGRESS, 180)
        self.setColumnWidth(Column.STATUS, 110)

    def paths(self) -> list[Path]:
        return list(self._paths)

    def add_files(self, paths: list[Path]) -> int:
        """Append files not already listed; return how many were added."""
        new_paths = [path for path in paths if path not in self._paths]
        for path in new_paths:
            self._append_row(path)
        return len(new_paths)

    def remove_selected(self) -> None:
        for row in sorted({index.row() for index in self.selectedIndexes()}, reverse=True):
            self.removeRow(row)
            del self._paths[row]

    def clear_files(self) -> None:
        self.setRowCount(0)
        self._paths.clear()

    def reset_for_batch(self) -> None:
        for row in range(self.rowCount()):
            self.set_progress(row, 0)
            self.set_status(row, RowStatus.QUEUED)

    def set_progress(self, row: int, percent: int) -> None:
        self.cellWidget(row, Column.PROGRESS).findChild(QProgressBar).setValue(percent)

    def set_status(self, row: int, status: RowStatus, tooltip: str = "") -> None:
        item = QTableWidgetItem(status.label)
        item.setForeground(QColor(status.color))
        item.setToolTip(tooltip)
        self.setItem(row, Column.STATUS, item)

    def scroll_to_row(self, row: int) -> None:
        self.scrollToItem(self.item(row, Column.NAME))

    def _append_row(self, path: Path) -> None:
        self._paths.append(path)
        row = self.rowCount()
        self.insertRow(row)

        name = QTableWidgetItem(path.name)
        name.setToolTip(str(path))
        self.setItem(row, Column.NAME, name)
        self.setItem(row, Column.SIZE, QTableWidgetItem(human_size(path.stat().st_size)))
        self.setCellWidget(row, Column.PROGRESS, self._progress_cell())
        self.set_status(row, RowStatus.READY)

    @staticmethod
    def _progress_cell() -> QWidget:
        bar = QProgressBar(value=0, format="%p%")
        cell = QWidget()
        layout = QHBoxLayout(cell)
        layout.setContentsMargins(8, 10, 8, 10)
        layout.addWidget(bar)
        return cell
