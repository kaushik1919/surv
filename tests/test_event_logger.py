import importlib
import json

from surveillance.domain import ThreatEvent


def _make_event(event_id="evt-1", timestamp=12.5):
    return ThreatEvent(
        event_id=event_id,
        track_id=7,
        label="zone_presence",
        level="high",
        reason="track remained in restricted zone 0 for 5.0s",
        timestamp=timestamp,
    )


def test_event_logger_exports_expected_api():
    module = importlib.import_module("event_logging.event_logger")

    assert hasattr(module, "EventLogger")
    assert hasattr(module, "FileEventLogger")


def test_event_logger_writes_jsonl_entries(tmp_path):
    module = importlib.import_module("event_logging.event_logger")
    log_path = tmp_path / "events.jsonl"
    logger = module.FileEventLogger(log_path, max_bytes=1024)
    event = _make_event()

    logger.log(event)
    logger.flush()

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1

    payload = json.loads(lines[0])
    assert set(payload) == {
        "timestamp",
        "event_id",
        "track_id",
        "label",
        "level",
        "reason",
        "bbox",
    }
    assert payload["event_id"] == event.event_id
    assert payload["track_id"] == event.track_id
    assert payload["label"] == event.label
    assert payload["level"] == event.level
    assert payload["reason"] == event.reason
    assert payload["timestamp"] == event.timestamp
    assert payload["bbox"] == [0, 0, 0, 0]


def test_event_logger_appends_multiple_entries(tmp_path):
    module = importlib.import_module("event_logging.event_logger")
    log_path = tmp_path / "events.jsonl"
    logger = module.FileEventLogger(log_path, max_bytes=1024)

    logger.log(_make_event("evt-1", 1.0))
    logger.log(_make_event("evt-2", 2.0))
    logger.flush()

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2


def test_event_logger_rotates_when_file_exceeds_max_bytes(tmp_path):
    module = importlib.import_module("event_logging.event_logger")
    log_path = tmp_path / "events.jsonl"
    logger = module.FileEventLogger(log_path, max_bytes=1)

    logger.log(_make_event("evt-1", 1.0))
    logger.log(_make_event("evt-2", 2.0))
    logger.flush()

    rotated_files = sorted(tmp_path.glob("events.jsonl*"))
    assert len(rotated_files) >= 2
