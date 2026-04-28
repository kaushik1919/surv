# Real-Time Surveillance and Threat Detection System

[![CircleCI](https://dl.circleci.com/status-badge/img/gh/kaushik1919/surv/tree/main.svg?style=svg)](https://dl.circleci.com/status-badge/redirect/gh/kaushik1919/surv/tree/main)

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
- Guarded drawing utilities that do not require OpenCV in CI.

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
- CircleCI

## Setup Instructions

Install CI-safe dependencies:

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

The current core is CI-safe and fake-driven. Runtime video execution will be expanded after the core contracts are stable.

Example CLI shape:

```bash
python main.py --source 0 --model yolov8n.pt --confidence 0.25
```

## CI

CircleCI installs only `requirements.txt`, runs `flake8 .`, then runs `pytest`. It does not download models, access cameras, call external services, or require GPU support.

## Future Improvements

- Add full OpenCV video capture and output loop.
- Add integration tests for YOLOv8 and DeepSORT in an opt-in workflow.
- Add restricted-zone threat rules.
- Add optional webhook, email, and sound alert adapters.
- Add demo video assets and benchmark FPS reporting.
