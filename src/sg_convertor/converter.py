"""Runs ffmpeg over a queue of files without blocking the UI."""

from collections import deque
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, Signal

from sg_convertor import ffmpeg
from sg_convertor.files import output_path_for
from sg_convertor.models import ConversionSettings

_STDERR_TAIL = 8000


class Outcome(Enum):
    DONE = auto()
    FAILED = auto()
    CANCELLED = auto()
    SKIPPED = auto()


@dataclass(frozen=True)
class BatchSummary:
    converted: int
    failed: int
    cancelled: bool


class BatchConverter(QObject):
    """Converts files one at a time and reports progress through signals.

    Files are identified by their index in the list passed to :meth:`start`.
    """

    file_started = Signal(int, object)  # index, destination Path
    file_progress = Signal(int, int)  # index, percent
    file_finished = Signal(int, object, str)  # index, Outcome, detail
    batch_finished = Signal(object)  # BatchSummary

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._pending: deque[tuple[int, Path]] = deque()
        self._settings = ConversionSettings()
        self._process: QProcess | None = None
        self._index = -1
        self._destination: Path | None = None
        self._duration = 0.0
        self._log = ""
        self._converted = 0
        self._failed = 0
        self._cancelled = False

    @property
    def is_running(self) -> bool:
        return self._process is not None

    def start(self, sources: list[Path], settings: ConversionSettings) -> None:
        if self.is_running:
            raise RuntimeError("A batch is already running.")
        self._pending = deque(enumerate(sources))
        self._settings = settings
        self._converted = self._failed = 0
        self._cancelled = False
        self._start_next()

    def cancel(self) -> None:
        self._cancelled = True
        while self._pending:
            index, _ = self._pending.popleft()
            self.file_finished.emit(index, Outcome.SKIPPED, "")
        if self._process:
            self._process.kill()

    def wait(self, timeout_ms: int) -> None:
        if self._process:
            self._process.waitForFinished(timeout_ms)

    def _start_next(self) -> None:
        if self._cancelled or not self._pending:
            self.batch_finished.emit(BatchSummary(self._converted, self._failed, self._cancelled))
            return

        self._index, source = self._pending.popleft()
        self._destination = output_path_for(source, self._settings)
        self._duration = 0.0
        self._log = ""

        process = QProcess(self)
        process.readyReadStandardOutput.connect(self._read_progress)
        process.readyReadStandardError.connect(self._read_log)
        process.finished.connect(self._on_finished)
        process.errorOccurred.connect(self._on_error)
        self._process = process

        self.file_started.emit(self._index, self._destination)
        process.start(
            ffmpeg.executable(),
            ffmpeg.build_arguments(source, self._destination, self._settings),
        )

    def _read_log(self) -> None:
        chunk = bytes(self._process.readAllStandardError()).decode(errors="replace")
        self._log = (self._log + chunk)[-_STDERR_TAIL:]
        if not self._duration:
            self._duration = ffmpeg.parse_duration(self._log) or 0.0

    def _read_progress(self) -> None:
        chunk = bytes(self._process.readAllStandardOutput()).decode(errors="replace")
        position = ffmpeg.parse_progress(chunk)
        if position is not None and self._duration:
            percent = min(99, int(position / self._duration * 100))
            self.file_progress.emit(self._index, percent)

    def _on_error(self, error: QProcess.ProcessError) -> None:
        # A process that never started emits no `finished` signal.
        if error == QProcess.ProcessError.FailedToStart:
            self._log = "Could not start ffmpeg."
            self._on_finished(-1)

    def _on_finished(self, exit_code: int, _exit_status=None) -> None:
        process, self._process = self._process, None
        process.deleteLater()

        if self._cancelled:
            outcome, detail = Outcome.CANCELLED, ""
        elif exit_code == 0:
            outcome, detail = Outcome.DONE, str(self._destination)
            self._converted += 1
        else:
            outcome, detail = Outcome.FAILED, ffmpeg.describe_failure(self._log)
            self._failed += 1

        if outcome is not Outcome.DONE:
            self._destination.unlink(missing_ok=True)

        self.file_finished.emit(self._index, outcome, detail)
        self._start_next()
