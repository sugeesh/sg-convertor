import subprocess

import pytest

from sg_convertor import ffmpeg
from sg_convertor.models import AudioFormat, ConversionSettings


def test_parse_duration():
    log = "  Duration: 01:02:03.50, start: 0.000000, bitrate: 512 kb/s"

    assert ffmpeg.parse_duration(log) == pytest.approx(3723.5)


def test_parse_duration_missing():
    assert ffmpeg.parse_duration("no timing here") is None


def test_parse_progress_returns_latest_position():
    chunk = "out_time_us=N/A\nout_time_us=1500000\nprogress=continue\nout_time_us=2500000\n"

    assert ffmpeg.parse_progress(chunk) == pytest.approx(2.5)


def test_parse_progress_missing():
    assert ffmpeg.parse_progress("progress=continue\n") is None


def test_describe_failure_recognises_missing_audio():
    log = "Output file #0 does not contain any stream"

    assert ffmpeg.describe_failure(log) == "The video has no audio track."


def test_describe_failure_uses_last_log_line():
    assert ffmpeg.describe_failure("first\nsecond\nreal reason\n") == "real reason"


@pytest.mark.parametrize(
    ("audio_format", "codec"),
    [(AudioFormat.MP3, "mp3"), (AudioFormat.M4A, "aac")],
)
def test_build_arguments_produce_audio(tmp_path, video_with_audio, audio_format, codec):
    destination = tmp_path / f"out{audio_format.extension}"
    settings = ConversionSettings(audio_format=audio_format, bitrate="128k")

    result = subprocess.run(
        [ffmpeg.executable(), *ffmpeg.build_arguments(video_with_audio, destination, settings)],
        capture_output=True,
    )

    assert result.returncode == 0
    probe = subprocess.run(
        [ffmpeg.executable(), "-hide_banner", "-i", str(destination)],
        capture_output=True,
        text=True,
    )
    assert f"Audio: {codec}" in probe.stderr
    assert "Video:" not in probe.stderr


def test_build_arguments_fail_without_audio(tmp_path, silent_video):
    destination = tmp_path / "out.mp3"

    result = subprocess.run(
        [
            ffmpeg.executable(),
            *ffmpeg.build_arguments(silent_video, destination, ConversionSettings()),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert ffmpeg.describe_failure(result.stderr) == "The video has no audio track."
