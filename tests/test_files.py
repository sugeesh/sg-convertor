from pathlib import Path

from sg_convertor.files import collect_videos, output_path_for
from sg_convertor.models import AudioFormat, ConversionSettings


def touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
    return path


def test_collect_videos_expands_folders_and_filters_extensions(tmp_path):
    top = touch(tmp_path / "a.mp4")
    nested = touch(tmp_path / "sub" / "b.MOV")
    touch(tmp_path / "notes.txt")

    assert collect_videos([tmp_path]) == [top, nested]


def test_collect_videos_removes_duplicates(tmp_path):
    video = touch(tmp_path / "a.mp4")

    assert collect_videos([video, tmp_path, video]) == [video]


def test_output_path_defaults_to_source_folder(tmp_path):
    source = tmp_path / "song.mp4"

    destination = output_path_for(source, ConversionSettings(audio_format=AudioFormat.M4A))

    assert destination == tmp_path / "song.m4a"


def test_output_path_uses_chosen_folder(tmp_path):
    out_dir = tmp_path / "out"
    settings = ConversionSettings(output_dir=out_dir)

    assert output_path_for(tmp_path / "song.mp4", settings) == out_dir / "song.mp3"


def test_output_path_never_overwrites(tmp_path):
    touch(tmp_path / "song.mp3")
    touch(tmp_path / "song (1).mp3")

    destination = output_path_for(tmp_path / "song.mp4", ConversionSettings())

    assert destination == tmp_path / "song (2).mp3"
