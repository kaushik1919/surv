# Surveillance Core Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the CI-safe surveillance core with explicit domain models, base interfaces, fake-driven pipeline tests, deterministic threat rules, alert storage, guarded drawing, and import-safe adapters.

**Architecture:** The core uses dependency injection and normalized domain models. `SurveillancePipeline` orchestrates frame processing while detector, tracker, alert, and drawing implementations remain swappable. Heavy runtime dependencies are isolated to adapter methods or constructors and are not required in CI.

**Tech Stack:** Python 3, dataclasses, typing protocols/ABCs, pytest, flake8, numpy, optional OpenCV/Ultralytics/DeepSORT runtime packages.

---

## File Map

- `surveillance/domain.py`: `Detection`, `Track`, `ThreatEvent`, and `BoundingBox` models.
- `surveillance/interfaces.py`: `BaseDetector`, `BaseTracker`, and `BaseAlertManager` abstract interfaces.
- `pipeline/pipeline.py`: `SurveillancePipeline.process(frame) -> PipelineResult` with tracks and events.
- `threats/rules.py`: deterministic `ThreatEngine` with injected time provider and per-track history.
- `alerts/alert_manager.py`: console plus in-memory event storage.
- `utils/drawing.py`: guarded optional OpenCV overlay helpers.
- `detector/yolo.py`: import-safe YOLOv8 adapter.
- `tracker/deepsort_tracker.py`: import-safe DeepSORT adapter.
- `config/settings.py`: default runtime settings.
- `main.py`: thin CLI entrypoint.
- `tests/helpers/fakes.py`: reusable `FakeDetector`, `FakeTracker`, `FakeAlertManager`.
- `.circleci/config.yml`: CI install, lint, tests.
- `requirements.txt`: lightweight CI dependencies only.
- `requirements-runtime.txt`: heavy runtime dependencies.
- `README.md`: professional evolving project documentation.

## Task 1: Domain Models And Interfaces

**Files:**
- Create: `surveillance/domain.py`
- Create: `surveillance/interfaces.py`
- Create: `surveillance/__init__.py`
- Test: `tests/test_domain.py`
- Test: `tests/test_interfaces.py`

- [ ] **Step 1: Write failing domain tests**

```python
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
```

- [ ] **Step 2: Run test to verify RED**

Run: `pytest tests/test_domain.py -v`
Expected: FAIL because `surveillance.domain` does not exist.

- [ ] **Step 3: Implement domain models**

Create frozen dataclasses for `BoundingBox`, `Detection`, `Track`, and `ThreatEvent`. Validate confidence is between 0 and 1.

- [ ] **Step 4: Run domain tests to verify GREEN**

Run: `pytest tests/test_domain.py -v`
Expected: PASS.

- [ ] **Step 5: Write failing interface tests**

```python
from surveillance.interfaces import BaseAlertManager, BaseDetector, BaseTracker


def test_base_interfaces_define_required_methods():
    assert hasattr(BaseDetector, "detect")
    assert hasattr(BaseTracker, "update")
    assert hasattr(BaseAlertManager, "handle")
```

- [ ] **Step 6: Run interface test to verify RED**

Run: `pytest tests/test_interfaces.py -v`
Expected: FAIL because `surveillance.interfaces` does not exist.

- [ ] **Step 7: Implement interfaces**

Use `abc.ABC` abstract base classes with `detect(frame)`, `update(frame, detections)`, and `handle(event)`.

- [ ] **Step 8: Run tests and commit**

Run: `pytest tests/test_domain.py tests/test_interfaces.py -v`
Expected: PASS.
Commit: `feat: add domain models and base interfaces`

## Task 2: Fake Components And Pipeline Contract

**Files:**
- Create: `tests/helpers/fakes.py`
- Create: `tests/helpers/__init__.py`
- Create: `pipeline/pipeline.py`
- Create: `pipeline/__init__.py`
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: Write failing pipeline tests with fakes**

```python
from pipeline.pipeline import SurveillancePipeline
from surveillance.domain import BoundingBox, Detection, ThreatEvent, Track
from tests.helpers.fakes import FakeAlertManager, FakeDetector, FakeTracker


def test_pipeline_returns_tracks_and_events_from_injected_components():
    detection = Detection(BoundingBox(0, 0, 10, 10), "person", 0.8)
    track = Track(track_id=1, bbox=detection.bbox, label="person")
    event = ThreatEvent("loiter-1-10.0", 1, "loitering", "medium", "threshold exceeded", 10.0)

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
```

- [ ] **Step 2: Run test to verify RED**

Run: `pytest tests/test_pipeline.py -v`
Expected: FAIL because `pipeline.pipeline` and fakes do not exist.

- [ ] **Step 3: Implement fakes and minimal pipeline**

`SurveillancePipeline.process(frame)` must call detector, tracker, threat engine, alert manager, and return `PipelineResult(tracks, events)`.

- [ ] **Step 4: Run tests and commit**

Run: `pytest tests/test_pipeline.py tests/test_domain.py tests/test_interfaces.py -v`
Expected: PASS.
Commit: `feat: add fake-driven surveillance pipeline`

## Task 3: Deterministic Threat Engine

**Files:**
- Create: `threats/rules.py`
- Create: `threats/__init__.py`
- Test: `tests/test_threat_rules.py`

- [ ] **Step 1: Write failing threat tests**

```python
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
```

- [ ] **Step 2: Run test to verify RED**

Run: `pytest tests/test_threat_rules.py -v`
Expected: FAIL because `threats.rules` does not exist.

- [ ] **Step 3: Implement minimal threat engine**

Maintain `track_history` keyed by `track_id`. Use the injected `time_provider`; never import or call real time.

- [ ] **Step 4: Run tests and commit**

Run: `pytest tests/test_threat_rules.py tests/test_pipeline.py -v`
Expected: PASS.
Commit: `feat: add deterministic threat rules`

## Task 4: Alert Manager, Drawing Isolation, And Import-Safe Adapters

**Files:**
- Create: `alerts/alert_manager.py`
- Create: `alerts/__init__.py`
- Create: `utils/drawing.py`
- Create: `utils/__init__.py`
- Create: `detector/yolo.py`
- Create: `detector/__init__.py`
- Create: `tracker/deepsort_tracker.py`
- Create: `tracker/__init__.py`
- Test: `tests/test_alert_manager.py`
- Test: `tests/test_import_safety.py`

- [ ] **Step 1: Write failing tests**

```python
from alerts.alert_manager import AlertManager
from surveillance.domain import ThreatEvent


def test_alert_manager_stores_events_in_memory(capsys):
    manager = AlertManager(console=True)
    event = ThreatEvent("evt-1", 1, "weapon", "critical", "weapon label detected", 2.0)

    manager.handle(event)

    assert manager.events == [event]
    assert "critical" in capsys.readouterr().out
```

```python
import importlib


def test_runtime_adapters_are_import_safe_without_heavy_dependencies():
    importlib.import_module("detector.yolo")
    importlib.import_module("tracker.deepsort_tracker")
    importlib.import_module("utils.drawing")
```

- [ ] **Step 2: Run tests to verify RED**

Run: `pytest tests/test_alert_manager.py tests/test_import_safety.py -v`
Expected: FAIL because modules do not exist.

- [ ] **Step 3: Implement alert manager, guarded drawing, and import-safe adapters**

Keep OpenCV imports inside drawing functions. Keep Ultralytics and DeepSORT imports inside adapter constructors or methods only.

- [ ] **Step 4: Run tests and commit**

Run: `pytest tests/test_alert_manager.py tests/test_import_safety.py -v`
Expected: PASS.
Commit: `feat: add alert manager and import-safe runtime boundaries`

## Task 5: Config, Main Entrypoint, CI, README

**Files:**
- Create: `config/settings.py`
- Create: `config/__init__.py`
- Create: `main.py`
- Create: `requirements.txt`
- Create: `requirements-runtime.txt`
- Create: `.flake8`
- Create: `.circleci/config.yml`
- Create: `README.md`
- Test: `tests/test_main_imports.py`

- [ ] **Step 1: Write failing import/config tests**

```python
import importlib

from config.settings import Settings


def test_main_import_is_safe_without_runtime_dependencies():
    importlib.import_module("main")


def test_settings_include_ci_safe_defaults():
    settings = Settings()

    assert settings.confidence_threshold > 0
    assert "knife" in settings.weapon_labels
```

- [ ] **Step 2: Run test to verify RED**

Run: `pytest tests/test_main_imports.py -v`
Expected: FAIL because settings and main are missing.

- [ ] **Step 3: Implement thin main, settings, CI, README, and requirements**

`main.py` parses CLI overrides only and defers runtime construction until `main()` is called. CI installs only `requirements.txt`.

- [ ] **Step 4: Run full local verification and commit**

Run: `python -m pip install -r requirements.txt`
Run: `flake8 .`
Run: `pytest`
Expected: all pass.
Commit: `chore: add ci and project documentation`

## Push And CI Loop

After each commit:

- [ ] Push the feature branch to `https://github.com/kaushik1919/surv.git`.
- [ ] Check CircleCI pipeline status for the pushed commit.
- [ ] If CircleCI fails, diagnose the job, fix with TDD or config validation, rerun local checks, commit, push, and re-check.

