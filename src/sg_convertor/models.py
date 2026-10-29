"""Value types shared by the conversion engine and the UI."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

BITRATES = ("320k", "256k", "192k", "128k", "96k")
DEFAULT_BITRATE = "192k"


class AudioFormat(Enum):
    MP3 = "mp3"
    M4A = "m4a"

    @property
    def extension(self) -> str:
        return f".{self.value}"


@dataclass(frozen=True)
class ConversionSettings:
    audio_format: AudioFormat = AudioFormat.MP3
    bitrate: str = DEFAULT_BITRATE
    output_dir: Path | None = None
    """Where to write audio files; ``None`` means next to each source video."""
