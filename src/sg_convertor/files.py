"""Finding input videos and choosing where converted audio is written."""

from collections.abc import Iterable
from pathlib import Path

from sg_convertor.models import ConversionSettings

SUPPORTED_EXTENSIONS = frozenset({".mp4", ".m4v", ".mov", ".mkv", ".webm", ".avi"})


def is_supported_video(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS


def collect_videos(paths: Iterable[Path]) -> list[Path]:
    """Expand folders recursively and return supported videos, without duplicates."""
    found: dict[Path, None] = {}
    for path in paths:
        candidates = sorted(path.rglob("*")) if path.is_dir() else [path]
        for candidate in candidates:
            if is_supported_video(candidate):
                found[candidate] = None
    return list(found)


def output_path_for(source: Path, settings: ConversionSettings) -> Path:
    """Return a destination path that never overwrites an existing file."""
    folder = settings.output_dir or source.parent
    extension = settings.audio_format.extension
    destination = folder / f"{source.stem}{extension}"
    counter = 1
    while destination.exists():
        destination = folder / f"{source.stem} ({counter}){extension}"
        counter += 1
    return destination
