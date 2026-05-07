import sys
import types

from surveillance.domain import BoundingBox, Detection, Track
from tracker.deepsort_tracker import DeepSortTracker


class FakeRuntimeTrack:
    def __init__(self, track_id, bbox, label, confirmed=True):
        self.track_id = track_id
        self._bbox = bbox
        self._label = label
        self._confirmed = confirmed

    def is_confirmed(self):
        return self._confirmed

    def to_ltrb(self):
        return self._bbox

    def get_det_class(self):
        return self._label


def test_deepsort_tracker_normalizes_runtime_tracks(monkeypatch):
    calls = []

    class FakeDeepSort:
        def __init__(self, max_age, n_init):
            calls.append(("init", max_age, n_init))

        def update_tracks(self, tracker_inputs, frame):
            calls.append(("update", tracker_inputs, frame))
            return [
                FakeRuntimeTrack("12", [1, 2, 20, 30], "person"),
                FakeRuntimeTrack("13", [3, 4, 10, 12], "person", confirmed=False),
            ]

    package = types.ModuleType("deep_sort_realtime")
    module = types.ModuleType("deep_sort_realtime.deepsort_tracker")
    module.DeepSort = FakeDeepSort
    monkeypatch.setitem(sys.modules, "deep_sort_realtime", package)
    monkeypatch.setitem(sys.modules, "deep_sort_realtime.deepsort_tracker", module)

    frame = object()
    detection = Detection(BoundingBox(1, 2, 20, 30), "person", 0.82)
    tracker = DeepSortTracker(max_age=20, n_init=2)
    tracks = tracker.update(frame, [detection])

    assert calls == [
        ("init", 20, 2),
        ("update", [([1, 2, 19, 28], 0.82, "person")], frame),
    ]
    assert tracks == [
        Track(
            track_id=12,
            bbox=BoundingBox(1.0, 2.0, 20.0, 30.0),
            label="person",
        )
    ]
