"""Building ffmpeg command lines and reading its output."""

import re
from pathlib import Path

import imageio_ffmpeg

from sg_convertor.models import AudioFormat, ConversionSettings

_CODEC_ARGS = {
    AudioFormat.MP3: ("-c:a", "libmp3lame"),
    AudioFormat.M4A: ("-c:a", "aac", "-movflags", "+faststart"),
}
_DURATION_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")
_PROGRESS_RE = re.compile(r"^out_time_us=(\d+)\s*$", re.MULTILINE)
_NO_AUDIO_MARKERS = ("matches no streams", "does not contain any stream")


def executable() -> str:
    """Path to the ffmpeg binary bundled with imageio-ffmpeg."""
    return imageio_ffmpeg.get_ffmpeg_exe()


def build_arguments(source: Path, destination: Path, settings: ConversionSettings) -> list[str]:
    """Arguments that extract the first audio track and report progress on stdout."""
    return [
        "-hide_banner",
        "-nostdin",
        "-y",
        "-i", str(source),
        "-vn",
        "-map", "0:a:0?",
        *_CODEC_ARGS[settings.audio_format],
        "-b:a", settings.bitrate,
        "-progress", "pipe:1",
        "-nostats",
        str(destination),
    ]  # fmt: skip


def parse_duration(log: str) -> float | None:
    """Total input duration in seconds, read from ffmpeg's stderr log."""
    match = _DURATION_RE.search(log)
    if not match:
        return None
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def parse_progress(chunk: str) -> float | None:
    """Latest encoded position in seconds, read from ``-progress`` output."""
    matches = _PROGRESS_RE.findall(chunk)
    return int(matches[-1]) / 1_000_000 if matches else None


def describe_failure(log: str) -> str:
    """A short, human-readable reason for a failed conversion."""
    if any(marker in log for marker in _NO_AUDIO_MARKERS):
        return "The video has no audio track."
    lines = log.strip().splitlines()
    return lines[-1] if lines else "Unknown error."
