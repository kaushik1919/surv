import pytest

from surveillance.domain import BoundingBox, Detection, ThreatEvent, Track


def test_detection_keeps_explicit_fields():
    detection = Detection(
        bbox=BoundingBox(1, 2, 3, 4),
        label="person",
        confidence=0.9,
    )

    assert detection.bbox.as_xyxy() == (1, 2, 3, 4)
    assert detection.label == "person"
    assert detection.confidence == 0.9


def test_track_keeps_persistent_identity():
    bbox = BoundingBox(5, 6, 20, 30)
    track = Track(track_id=42, bbox=bbox, label="person")

    assert track.track_id == 42
    assert track.bbox == bbox
    assert track.label == "person"


def test_threat_event_keeps_auditable_fields():
    event = ThreatEvent(
        event_id="weapon-7-12.5",
        track_id=7,
        label="weapon",
        level="critical",
        reason="weapon label detected",
        timestamp=12.5,
    )

    assert event.track_id == 7
    assert event.level == "critical"
    assert event.reason == "weapon label detected"


def test_detection_rejects_invalid_confidence():
    with pytest.raises(ValueError, match="confidence"):
        Detection(
            bbox=BoundingBox(1, 2, 3, 4),
            label="person",
            confidence=1.5,
        )
