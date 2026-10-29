import subprocess
from pathlib import Path

import pytest

from sg_convertor import ffmpeg


def _make_video(path: Path, *, with_audio: bool) -> Path:
    inputs = ["-f", "lavfi", "-i", "testsrc=size=160x120:rate=10"]
    if with_audio:
        inputs += ["-f", "lavfi", "-i", "sine=frequency=440"]
    subprocess.run(
        [ffmpeg.executable(), "-v", "error", "-y", *inputs, "-t", "2", "-shortest", str(path)],
        check=True,
    )
    return path


@pytest.fixture(scope="session")
def video_with_audio(tmp_path_factory) -> Path:
    return _make_video(tmp_path_factory.mktemp("media") / "clip.mp4", with_audio=True)


@pytest.fixture(scope="session")
def silent_video(tmp_path_factory) -> Path:
    return _make_video(tmp_path_factory.mktemp("media") / "silent.mp4", with_audio=False)
