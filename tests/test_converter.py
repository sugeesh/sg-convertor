import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer  # noqa: E402

from sg_convertor.converter import BatchConverter, BatchSummary, Outcome  # noqa: E402
from sg_convertor.models import ConversionSettings  # noqa: E402


@pytest.fixture(scope="module")
def qt_app():
    return QCoreApplication.instance() or QCoreApplication([])


def run_batch(converter, sources, settings, timeout_ms=30_000):
    outcomes: dict[int, Outcome] = {}
    summaries: list[BatchSummary] = []
    loop = QEventLoop()
    converter.file_finished.connect(lambda index, outcome, _: outcomes.__setitem__(index, outcome))
    converter.batch_finished.connect(lambda summary: (summaries.append(summary), loop.quit()))
    QTimer.singleShot(timeout_ms, loop.quit)
    converter.start(sources, settings)
    loop.exec()
    return outcomes, summaries


def test_batch_converts_and_reports_failures(qt_app, tmp_path, video_with_audio, silent_video):
    settings = ConversionSettings(output_dir=tmp_path)

    outcomes, summaries = run_batch(BatchConverter(), [video_with_audio, silent_video], settings)

    assert outcomes == {0: Outcome.DONE, 1: Outcome.FAILED}
    assert summaries == [BatchSummary(converted=1, failed=1, cancelled=False)]
    assert [path.name for path in tmp_path.iterdir()] == ["clip.mp3"]
