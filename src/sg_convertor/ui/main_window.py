"""Main window: wires the widgets to the batch converter."""

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from sg_convertor.converter import BatchConverter, BatchSummary, Outcome
from sg_convertor.files import SUPPORTED_EXTENSIONS, collect_videos
from sg_convertor.ui.drop_zone import DropZone, local_paths
from sg_convertor.ui.file_table import FileTable, RowStatus
from sg_convertor.ui.settings_panel import SettingsPanel

_OUTCOME_STATUS = {
    Outcome.DONE: RowStatus.DONE,
    Outcome.FAILED: RowStatus.FAILED,
    Outcome.CANCELLED: RowStatus.CANCELLED,
    Outcome.SKIPPED: RowStatus.SKIPPED,
}
_VIDEO_FILTER = "Video files ({})".format(
    " ".join(f"*{ext}" for ext in sorted(SUPPORTED_EXTENSIONS))
)
_EMPTY_HINT = "Add some files to get started."


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SG Convertor")
        self.resize(900, 680)
        self.setAcceptDrops(True)

        self._converter = BatchConverter(self)
        self._finished_count = 0
        self._drop_zone = DropZone()
        self._table = FileTable()
        self._settings = SettingsPanel()
        self._add_files = QPushButton("+  Add files")
        self._add_folder = QPushButton("📁  Add folder")
        self._remove = QPushButton("Remove selected")
        self._clear = QPushButton("Clear all")
        self._status = QLabel(_EMPTY_HINT)
        self._overall = QProgressBar(objectName="overall", textVisible=False)
        self._cancel = QPushButton("Cancel", objectName="danger")
        self._convert = QPushButton("Convert", objectName="primary")

        self._build_layout()
        self._connect_signals()
        self._refresh_controls()

    # ----- layout -----

    def _build_layout(self) -> None:
        root = QWidget(objectName="root")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        layout.addWidget(QLabel("SG Convertor", objectName="title"))
        layout.addWidget(
            QLabel(
                "Extract high-quality audio from your videos as MP3 or M4A.", objectName="subtitle"
            )
        )
        layout.addWidget(self._drop_zone)
        layout.addLayout(self._build_file_buttons())
        layout.addWidget(self._table, 1)
        layout.addWidget(self._settings)
        layout.addLayout(self._build_bottom_bar())

    def _build_file_buttons(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addWidget(self._add_files)
        row.addWidget(self._add_folder)
        row.addStretch()
        row.addWidget(self._remove)
        row.addWidget(self._clear)
        return row

    def _build_bottom_bar(self) -> QHBoxLayout:
        status_column = QVBoxLayout()
        status_column.addWidget(self._status)
        status_column.addWidget(self._overall)

        row = QHBoxLayout()
        row.addLayout(status_column, 1)
        row.addSpacing(16)
        row.addWidget(self._cancel)
        row.addWidget(self._convert)
        return row

    def _connect_signals(self) -> None:
        self._drop_zone.paths_dropped.connect(self._add_paths)
        self._add_files.clicked.connect(self._choose_files)
        self._add_folder.clicked.connect(self._choose_folder)
        self._remove.clicked.connect(self._remove_selected)
        self._clear.clicked.connect(self._clear_all)
        self._settings.open_output_requested.connect(self._open_output_folder)
        self._convert.clicked.connect(self._start_batch)
        self._cancel.clicked.connect(self._converter.cancel)

        self._converter.file_started.connect(self._on_file_started)
        self._converter.file_progress.connect(self._on_file_progress)
        self._converter.file_finished.connect(self._on_file_finished)
        self._converter.batch_finished.connect(self._on_batch_finished)

    # ----- adding and removing files -----

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and not self._converter.is_running:
            event.acceptProposedAction()

    def dropEvent(self, event):
        self._add_paths(local_paths(event.mimeData()))

    def _choose_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "Choose video files", str(Path.home()), _VIDEO_FILTER
        )
        self._add_paths([Path(file) for file in files])

    def _choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose a folder", str(Path.home()))
        if folder:
            self._add_paths([Path(folder)])

    def _add_paths(self, paths: list[Path]) -> None:
        if not paths or self._converter.is_running:
            return
        videos = collect_videos(paths)
        if not videos:
            self._status.setText("No supported video files found.")
            return
        self._table.add_files(videos)
        self._status.setText(f"{self._table.rowCount()} file(s) ready.")
        self._refresh_controls()

    def _remove_selected(self) -> None:
        self._table.remove_selected()
        self._refresh_controls()

    def _clear_all(self) -> None:
        self._table.clear_files()
        self._overall.setValue(0)
        self._status.setText(_EMPTY_HINT)
        self._refresh_controls()

    def _open_output_folder(self) -> None:
        sources = self._table.paths()
        folder = self._settings.settings().output_dir or (sources[0].parent if sources else None)
        if folder:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    # ----- conversion -----

    def _start_batch(self) -> None:
        settings = self._settings.settings()
        if settings.output_dir and not self._ensure_folder(settings.output_dir):
            return
        sources = self._table.paths()
        self._table.reset_for_batch()
        self._overall.setRange(0, len(sources) * 100)
        self._overall.setValue(0)
        self._finished_count = 0
        self._converter.start(sources, settings)
        self._refresh_controls()

    def _ensure_folder(self, folder: Path) -> bool:
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            QMessageBox.warning(self, "Output folder", f"Can't create the output folder:\n{error}")
            return False
        return True

    def _on_file_started(self, row: int, destination: Path) -> None:
        self._table.set_status(row, RowStatus.CONVERTING)
        self._table.scroll_to_row(row)
        self._status.setText(f"Converting {self._table.paths()[row].name}  →  {destination.name}")

    def _on_file_progress(self, row: int, percent: int) -> None:
        self._table.set_progress(row, percent)
        self._overall.setValue(self._finished_count * 100 + percent)

    def _on_file_finished(self, row: int, outcome: Outcome, detail: str) -> None:
        self._table.set_status(row, _OUTCOME_STATUS[outcome], tooltip=detail)
        if outcome is Outcome.DONE:
            self._table.set_progress(row, 100)
        if outcome is not Outcome.SKIPPED:
            self._finished_count += 1
            self._overall.setValue(self._finished_count * 100)

    def _on_batch_finished(self, summary: BatchSummary) -> None:
        message = f"Finished: {summary.converted} converted"
        if summary.failed:
            message += f", {summary.failed} failed (hover the status for details)"
        if summary.cancelled:
            message += " — cancelled"
        self._status.setText(message + ".")
        self._refresh_controls()

    def _refresh_controls(self) -> None:
        busy = self._converter.is_running
        has_files = self._table.rowCount() > 0
        self._convert.setEnabled(has_files and not busy)
        self._cancel.setVisible(busy)
        self._add_files.setEnabled(not busy)
        self._add_folder.setEnabled(not busy)
        self._remove.setEnabled(has_files and not busy)
        self._clear.setEnabled(has_files and not busy)
        self._drop_zone.setAcceptDrops(not busy)
        self._settings.set_locked(busy)

    def closeEvent(self, event):
        if self._converter.is_running:
            answer = QMessageBox.question(
                self, "Quit", "A conversion is running. Stop it and quit?"
            )
            if answer != QMessageBox.Yes:
                event.ignore()
                return
            self._converter.cancel()
            self._converter.wait(3000)
        event.accept()
