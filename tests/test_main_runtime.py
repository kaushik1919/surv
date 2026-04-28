import sys
import types

from config.settings import Settings
from main import build_parser, open_video_source, parse_source, settings_from_args


def test_settings_from_args_accepts_video_performance_controls():
    parser = build_parser()
    args = parser.parse_args(
        [
            "--source",
            "video.mp4",
            "--frame-width",
            "320",
            "--frame-skip",
            "2",
            "--no-display",
        ]
    )

    settings = settings_from_args(args)

    assert settings.source == "video.mp4"
    assert settings.frame_width == 320
    assert settings.frame_skip == 2
    assert settings.display is False


def test_parse_source_converts_numeric_camera_source():
    assert parse_source("0") == 0
    assert parse_source("video.mp4") == "video.mp4"


def test_open_video_source_imports_cv2_only_at_runtime(monkeypatch):
    calls = []

    class FakeVideoCapture:
        def __init__(self, source):
            calls.append(source)

    fake_cv2 = types.ModuleType("cv2")
    fake_cv2.VideoCapture = FakeVideoCapture
    monkeypatch.setitem(sys.modules, "cv2", fake_cv2)

    capture = open_video_source(Settings(source="0"))

    assert isinstance(capture, FakeVideoCapture)
    assert calls == [0]
