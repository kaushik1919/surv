from surveillance.domain import BoundingBox, Detection, Track
from threats.rules import ThreatEngine


def test_weapon_detection_emits_critical_event_with_injected_time():
    engine = ThreatEngine(time_provider=lambda: 15.0, weapon_labels={"knife"})
    detection = Detection(BoundingBox(0, 0, 1, 1), "knife", 0.95)
    track = Track(3, detection.bbox, "knife")

    events = engine.evaluate([track], [detection])

    assert events[0].track_id == 3
    assert events[0].label == "weapon"
    assert events[0].level == "critical"
    assert events[0].timestamp == 15.0


def test_loitering_uses_track_history_and_injected_time():
    now = {"value": 0.0}
    engine = ThreatEngine(time_provider=lambda: now["value"], loitering_seconds=5.0)
    track = Track(4, BoundingBox(0, 0, 10, 10), "person")

    assert engine.evaluate([track], []) == []
    now["value"] = 6.0
    events = engine.evaluate([track], [])

    assert events[0].label == "loitering"
    assert events[0].track_id == 4
    assert events[0].reason == "track observed for 6.0s"


def test_loitering_event_is_not_duplicated_for_same_track():
    now = {"value": 0.0}
    engine = ThreatEngine(time_provider=lambda: now["value"], loitering_seconds=5.0)
    track = Track(9, BoundingBox(0, 0, 10, 10), "person")

    engine.evaluate([track], [])
    now["value"] = 6.0
    first = engine.evaluate([track], [])
    second = engine.evaluate([track], [])

    assert len(first) == 1
    assert second == []
