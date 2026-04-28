import importlib
from types import SimpleNamespace

import numpy as np
import pytest

from surveillance.domain import BoundingBox, ThreatEvent, Track


def test_visualizer_exports_expected_api():
    module = importlib.import_module("utils.visualization")

    assert hasattr(module, "draw_tracks")
    assert hasattr(module, "Visualizer")


def test_visualizer_draw_tracks_handles_optional_opencv():
    pytest.importorskip("cv2", reason="OpenCV is optional for visualization tests")

    module = importlib.import_module("utils.visualization")
    visualizer = module.Visualizer()
    frame = np.zeros((32, 32, 3), dtype=np.uint8)
    tracks = [Track(1, BoundingBox(2, 2, 12, 12), "person")]
    events = [
        ThreatEvent(
            event_id="evt-1",
            track_id=1,
            label="zone_entry",
            level="high",
            reason="track entered restricted zone 0",
            timestamp=3.0,
        )
    ]
    settings = SimpleNamespace(
        visualization_enabled=True,
        restricted_zones=((0, 0, 16, 16),),
        trail_length=10,
    )

    output = visualizer.draw(frame, tracks, events, settings)

    assert output is not None
