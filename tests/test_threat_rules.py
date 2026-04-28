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
    assert "6.0" in events[0].reason
    assert "movement" in events[0].reason


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


def test_loitering_blocked_by_movement():
    now = {"value": 0.0}
    engine = ThreatEngine(
        time_provider=lambda: now["value"],
        loitering_seconds=5.0,
        movement_threshold=5.0,
    )
    track = Track(10, BoundingBox(0, 0, 10, 10), "person")

    assert engine.evaluate([track], []) == []
    now["value"] = 6.0
    moving_track = Track(10, BoundingBox(30, 0, 40, 10), "person")

    assert engine.evaluate([moving_track], []) == []


def test_loitering_triggered_when_static():
    now = {"value": 0.0}
    engine = ThreatEngine(
        time_provider=lambda: now["value"],
        loitering_seconds=5.0,
        movement_threshold=5.0,
    )
    track = Track(11, BoundingBox(0, 0, 10, 10), "person")

    assert engine.evaluate([track], []) == []
    now["value"] = 6.0
    events = engine.evaluate([track], [])

    assert len(events) == 1
    assert events[0].track_id == 11
    assert events[0].label == "loitering"
    assert events[0].level == "medium"
    assert "6.0" in events[0].reason
    assert "movement" in events[0].reason


def test_restricted_zone_entry():
    now = {"value": 0.0}
    engine = ThreatEngine(
        time_provider=lambda: now["value"],
        restricted_zones=((0, 0, 100, 100),),
    )
    outside_track = Track(12, BoundingBox(150, 150, 160, 160), "person")
    inside_track = Track(12, BoundingBox(10, 10, 20, 20), "person")

    assert engine.evaluate([outside_track], []) == []
    now["value"] = 1.0
    events = engine.evaluate([inside_track], [])

    assert len(events) == 1
    assert events[0].track_id == 12
    assert events[0].label == "zone_entry"
    assert events[0].level == "high"


def test_restricted_zone_sustained_presence():
    now = {"value": 0.0}
    engine = ThreatEngine(
        time_provider=lambda: now["value"],
        loitering_seconds=5.0,
        restricted_zones=((0, 0, 100, 100),),
    )
    outside_track = Track(13, BoundingBox(150, 150, 160, 160), "person")
    inside_track = Track(13, BoundingBox(10, 10, 20, 20), "person")

    assert engine.evaluate([outside_track], []) == []
    now["value"] = 1.0
    first = engine.evaluate([inside_track], [])
    now["value"] = 6.0
    second = engine.evaluate([inside_track], [])
    now["value"] = 7.0
    third = engine.evaluate([inside_track], [])

    assert any(event.label == "zone_entry" for event in first)
    zone_presence_events = [
        event
        for event in second + third
        if event.label == "zone_presence"
    ]
    assert len(zone_presence_events) <= 1


def test_deduplication_same_event_not_repeated():
    now = {"value": 0.0}
    engine = ThreatEngine(
        time_provider=lambda: now["value"],
        loitering_seconds=5.0,
        movement_threshold=5.0,
    )
    track = Track(14, BoundingBox(0, 0, 10, 10), "person")

    assert engine.evaluate([track], []) == []
    now["value"] = 6.0
    first = engine.evaluate([track], [])
    second = engine.evaluate([track], [])

    assert len(first) == 1
    assert second == []


def test_deduplication_resets_after_movement():
    now = {"value": 0.0}
    engine = ThreatEngine(
        time_provider=lambda: now["value"],
        loitering_seconds=5.0,
        movement_threshold=5.0,
    )
    track = Track(15, BoundingBox(0, 0, 10, 10), "person")

    assert engine.evaluate([track], []) == []
    now["value"] = 6.0
    first = engine.evaluate([track], [])

    now["value"] = 7.0
    moved_track = Track(15, BoundingBox(30, 0, 40, 10), "person")
    assert engine.evaluate([moved_track], []) == []

    now["value"] = 13.0
    static_track = Track(15, BoundingBox(30, 0, 40, 10), "person")
    second = engine.evaluate([static_track], [])

    assert len(first) == 1
    assert len(second) == 1


def test_weapon_detection_regression_still_works():
    engine = ThreatEngine(time_provider=lambda: 15.0, weapon_labels={"knife"})
    detection = Detection(BoundingBox(0, 0, 1, 1), "knife", 0.95)
    track = Track(3, detection.bbox, "knife")

    events = engine.evaluate([track], [detection])

    assert events[0].track_id == 3
    assert events[0].label == "weapon"
    assert events[0].level == "critical"
    assert events[0].timestamp == 15.0


def test_existing_loitering_regression_still_works():
    now = {"value": 0.0}
    engine = ThreatEngine(
        time_provider=lambda: now["value"],
        loitering_seconds=5.0,
        movement_threshold=5.0,
    )
    track = Track(4, BoundingBox(0, 0, 10, 10), "person")

    assert engine.evaluate([track], []) == []
    now["value"] = 6.0
    events = engine.evaluate([track], [])

    assert events[0].label == "loitering"
    assert events[0].track_id == 4
    assert "6.0" in events[0].reason
