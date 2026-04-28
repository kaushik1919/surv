from pipeline.pipeline import SurveillancePipeline
from surveillance.domain import BoundingBox, Detection, ThreatEvent, Track
from tests.helpers.fakes import FakeAlertManager, FakeDetector, FakeTracker


def test_pipeline_returns_tracks_and_events_from_injected_components():
    detection = Detection(BoundingBox(0, 0, 10, 10), "person", 0.8)
    track = Track(track_id=1, bbox=detection.bbox, label="person")
    event = ThreatEvent(
        "loiter-1-10.0",
        1,
        "loitering",
        "medium",
        "threshold exceeded",
        10.0,
    )

    detector = FakeDetector([detection])
    tracker = FakeTracker([track])
    alerts = FakeAlertManager()
    threat_engine = lambda tracks, detections: [event]
    pipeline = SurveillancePipeline(detector, tracker, threat_engine, alerts)

    result = pipeline.process(frame=object())

    assert result.tracks == [track]
    assert result.events == [event]
    assert alerts.events == [event]


def test_pipeline_calls_components_in_strict_order():
    calls = []
    detector = FakeDetector([], calls=calls)
    tracker = FakeTracker([], calls=calls)
    alerts = FakeAlertManager(calls=calls)

    def threat_engine(tracks, detections):
        calls.append("threat_engine")
        return []

    pipeline = SurveillancePipeline(detector, tracker, threat_engine, alerts)
    pipeline.process(frame=object())

    assert calls == ["detector", "tracker", "threat_engine"]
