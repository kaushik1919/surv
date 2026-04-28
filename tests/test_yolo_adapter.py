import sys
import types

from detector.yolo import YOLODetector
from surveillance.domain import BoundingBox, Detection


class FakeValue:
    def __init__(self, value):
        self.value = value

    def __getitem__(self, index):
        return self.value


class FakeBox:
    def __init__(self, xyxy, confidence, class_id):
        self.xyxy = [xyxy]
        self.conf = FakeValue(confidence)
        self.cls = FakeValue(class_id)


class FakeResult:
    names = {0: "person", 1: "knife"}

    def __init__(self):
        self.boxes = [
            FakeBox([1, 2, 20, 30], 0.91, 1),
            FakeBox([5, 6, 10, 12], 0.10, 0),
        ]


def test_yolo_detector_normalizes_runtime_results(monkeypatch):
    calls = []

    class FakeYOLO:
        def __init__(self, model_path):
            calls.append(("init", model_path))

        def predict(self, frame, conf, verbose):
            calls.append(("predict", frame, conf, verbose))
            return [FakeResult()]

    fake_module = types.ModuleType("ultralytics")
    fake_module.YOLO = FakeYOLO
    monkeypatch.setitem(sys.modules, "ultralytics", fake_module)

    frame = object()
    detector = YOLODetector("demo.pt", confidence_threshold=0.25)
    detections = detector.detect(frame)

    assert calls == [
        ("init", "demo.pt"),
        ("predict", frame, 0.25, False),
    ]
    assert detections == [
        Detection(
            bbox=BoundingBox(1.0, 2.0, 20.0, 30.0),
            label="knife",
            confidence=0.91,
        )
    ]
