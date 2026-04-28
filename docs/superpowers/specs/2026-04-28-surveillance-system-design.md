# Real-Time Surveillance and Threat Detection System Design

## Overview

Build a production-grade Python surveillance system using an adapter-first modular core. The system will process video frames through object detection, tracking, threat rules, alerting, visualization, and output while keeping the core deterministic and safe for CI.

The first version prioritizes offline/demo reliability. CI will validate domain logic and pipeline behavior without requiring YOLOv8, DeepSORT, camera access, GPU, model downloads, network calls, or external services. Runtime adapters will support real YOLOv8 and DeepSORT integrations behind strict boundaries.

## Goals

- Provide a modular real-time surveillance pipeline.
- Support YOLOv8 object detection through a thin adapter.
- Support DeepSORT tracking through a thin adapter.
- Maintain persistent track identities and stateful threat history.
- Detect weapon presence, loitering, and rule-based suspicious activity.
- Emit console alerts and store in-memory alert events.
- Draw labels, bounding boxes, track IDs, and threat state overlays.
- Keep `main.py` as a thin runtime entrypoint.
- Keep CircleCI fast, deterministic, and free of heavy runtime dependencies.
- Maintain a professional README as features land.

## Non-Goals For V1

- No active webhook, email, or sound delivery.
- No trained suspicious-activity behavior model.
- No model download or GPU validation in CI.
- No CI tests that instantiate YOLOv8 or DeepSORT backends.
- No direct dependency on live video devices in tests.

## Project Structure

```text
surveillance-system/
+-- main.py
+-- detector/
|   +-- yolo.py
+-- tracker/
|   +-- deepsort_tracker.py
+-- pipeline/
|   +-- pipeline.py
+-- threats/
|   +-- rules.py
+-- alerts/
|   +-- alert_manager.py
+-- utils/
|   +-- drawing.py
+-- config/
|   +-- settings.py
+-- tests/
|   +-- helpers/
+-- requirements.txt
+-- requirements-runtime.txt
+-- README.md
+-- .circleci/
    +-- config.yml
```

## Domain Models

The core system will use explicit domain models instead of loose dictionaries.

- `Detection`
  - `bbox`: bounding box coordinates.
  - `label`: detected class label.
  - `confidence`: confidence score.
- `Track`
  - `track_id`: persistent object identity.
  - `bbox`: current bounding box coordinates.
  - `label`: tracked object label.
- `ThreatEvent`
  - `event_id`: stable event identifier.
  - `track_id`: associated track ID when available.
  - `label`: threat label.
  - `level`: severity level.
  - `reason`: human-readable reason.
  - `timestamp`: deterministic timestamp supplied by the threat engine clock.

These models form the contract between detector, tracker, threat engine, alert manager, drawing utilities, and pipeline orchestration.

## Core Interfaces And Boundaries

The system will use dependency injection for detector, tracker, and alert manager. The pipeline will depend on behavior contracts rather than hardcoded concrete implementations.

- `detector/yolo.py` must return normalized `Detection` objects and must not expose Ultralytics objects.
- `tracker/deepsort_tracker.py` must return normalized `Track` objects and must not expose DeepSORT internals.
- `threats/rules.py` must be pure logic with no external runtime dependencies.
- `pipeline/pipeline.py` will contain `SurveillancePipeline`, the orchestration class.
- `main.py` will only parse CLI overrides, load settings, instantiate runtime components, and run the pipeline.

Heavy imports are forbidden at module import time. Ultralytics, DeepSORT, OpenCV runtime capture, and other heavy dependencies must be imported only inside constructors or methods that explicitly need them.

## Data Flow

The pipeline order is strict:

```text
frame -> detector -> tracker -> threat_engine -> alert_manager -> drawing -> output
```

`SurveillancePipeline` will coordinate that flow. It will accept injected detector, tracker, threat engine, alert manager, drawing/output behavior, and settings. Tests will verify the order using fakes.

## Threat Engine

`threats/rules.py` will maintain state keyed by `track_id` for loitering and suspicious activity rules.

Per-track history will include:

- `first_seen`
- recent positions
- recent timestamps

Rules for v1:

- Weapon detection: event when a detection or track label matches configured weapon labels.
- Loitering: event when a track remains observed longer than the configured threshold.
- Restricted-zone presence: event when configured zones exist and a track remains inside a restricted zone.
- Suspicious activity: rule-based aggregation of known signals, with a clean future boundary for ML-based behavior classification.

The threat engine will not call real time directly. It will receive a time function or clock so tests can use fixed timestamps.

## Alert System

V1 alerting includes:

- Console output.
- In-memory event storage for deterministic tests and runtime inspection.

The design will leave an adapter interface for webhook, email, and sound delivery, but those adapters will not be active in v1.

## Configuration

`config/settings.py` will hold defaults for:

- Input source.
- Model path and backend choices.
- Frame resizing.
- Optional frame skipping.
- Confidence threshold.
- Loitering threshold.
- Weapon labels.
- Restricted zones.
- Display/output behavior.

`main.py` will handle CLI overrides only. It will not contain core business logic.

## Requirements Split

`requirements.txt` will contain only lightweight CI dependencies:

- `pytest`
- `flake8`
- `numpy`

`requirements-runtime.txt` will contain runtime dependencies such as:

- `ultralytics`
- DeepSORT implementation package
- `opencv-python`

CircleCI will install only `requirements.txt`.

## Testing Strategy

Testing follows strict TDD.

Layers:

- Domain models: pure unit tests with no mocks.
- Threat engine: deterministic tests with fixed timestamps.
- Pipeline: tests only with fake components.
- Alert manager: tests for console-safe event creation and in-memory storage.
- Drawing: minimal optional tests, guarded or skipped gracefully when OpenCV is absent.
- Runtime adapters: import-safety checks only in CI; deeper validation deferred to manual or later integration tests.

Reusable test fakes will live under `tests/helpers`:

- `FakeDetector`
- `FakeTracker`
- `FakeAlertManager`

No CI test may require real video frames, camera devices, network access, GPU checks, model downloads, YOLOv8 instantiation, or DeepSORT instantiation.

## CircleCI

CircleCI will run a fast Python workflow:

```text
python -m pip install -r requirements.txt
flake8 .
pytest
```

Acceptance criteria:

- `flake8` passes with no warnings or an explicit project config.
- `pytest` runs in a few seconds.
- No CI step downloads models or contacts external services.
- The project can be imported without runtime-only dependencies installed.

## README Evolution

The README will be updated after each major feature:

- Initial project scaffold and architecture.
- Detection module.
- Tracking module.
- Threat rules and alerts.
- Final integration and runtime usage.

Required README sections:

- Overview.
- Features.
- Architecture diagram.
- Tech stack.
- Setup instructions.
- Demo section with sample commands and notes for adding video assets.
- CI badge.
- Future improvements.

## Implementation Order

1. Define domain models and interfaces.
2. Write failing tests using deterministic fakes.
3. Implement minimal `SurveillancePipeline`.
4. Implement stateful threat engine.
5. Implement alert manager.
6. Implement light drawing helpers.
7. Implement thin `main.py`.
8. Add YOLOv8 and DeepSORT adapters last, with import-safe boundaries.
9. Update README and CircleCI as each major feature lands.

## Branching And CI Discipline

Development will use feature branches. Main must not receive direct commits. Each feature branch will keep commits small and meaningful. Before any push, local lint and tests must pass. After each push, CircleCI pipeline status must be checked and failures diagnosed before continuing.
