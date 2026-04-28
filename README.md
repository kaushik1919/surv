# Real-Time Surveillance and Threat Detection System

## Overview

This project is a modular Python surveillance system for real-time object detection, tracking, and threat-event generation. The core is adapter-first: tests exercise deterministic domain logic and pipeline flow with fakes, while YOLOv8 and DeepSORT are isolated behind runtime adapters.

## Features

- Explicit domain models for detections, tracks, and threat events.
- Dependency-injected detector, tracker, and alert manager interfaces.
- `SurveillancePipeline.process(frame)` returning tracks and threat events.
- Stateful threat handling with deterministic loitering detection.
- Weapon-label threat events.
- Console and in-memory alert manager.
- Import-safe YOLOv8 and DeepSORT adapter shells.
- Guarded drawing utilities that do not require OpenCV for local validation.
- Runtime webcam and video-file input through OpenCV.
- Frame resizing and optional frame skipping controls.

## Architecture Diagram

```text
frame
  -> detector
  -> tracker
  -> threat_engine
  -> alert_manager
  -> drawing
  -> output
```

## Tech Stack

- Python 3.13
- pytest
- flake8
- numpy
- Optional runtime: Ultralytics YOLOv8, DeepSORT, OpenCV

## Setup Instructions

Install lightweight validation dependencies:

```bash
python -m pip install -r requirements.txt
```

Run local checks:

```bash
flake8 .
pytest
```

Install runtime dependencies only when running real video/model adapters:

```bash
python -m pip install -r requirements-runtime.txt
```

## Demo

The current core is local-validation safe and fake-driven. Runtime video execution will be expanded after the core contracts are stable.

Example CLI shape:

```bash
python main.py --source 0 --model yolov8n.pt --confidence 0.25 --frame-width 640 --frame-skip 0
python main.py --source sample.mp4 --model yolov8n.pt --no-display
```

## Local Validation

Validation is local-only at this stage. Install `requirements.txt`, run `flake8 .`, then run `pytest`. The validation flow does not download models, access cameras, call external services, or require GPU support.

## Future Improvements

- Add full OpenCV video capture and output loop.
- Add integration tests for YOLOv8 and DeepSORT in an opt-in workflow.
- Add restricted-zone threat rules.
- Add optional webhook, email, and sound alert adapters.
- Add demo video assets and benchmark FPS reporting.

## Threat Enhancements (v0.3)

This release adds deterministic, movement-aware loitering detection, rectangular
restricted-zone handling (entry and sustained-presence), and per-event
deduplication to reduce alert spam.

- Movement-aware loitering: a track must exceed the configured time threshold
  and remain below a configurable pixel movement threshold (based on recent
  position history) to generate a `loitering` event.
- Restricted zones: rectangular zones from `config.Settings.restricted_zones`
  produce immediate `zone_entry` events on entry and `zone_presence` events
  when a track remains inside for the configured duration.
- Deduplication and resets: events are deduplicated per `(track_id, event_type)`;
  they are reset when the track disappears, leaves a zone, resumes movement,
  or its label changes.

These features are deterministic (use the injected time provider) and test-driven
—see `tests/test_threat_rules.py` for the behavior-driven test suite.
