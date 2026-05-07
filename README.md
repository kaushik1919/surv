# Real-Time Surveillance and Threat Detection System

Deterministic real-time pipeline for object detection, tracking, threat analysis, and reproducible demo generation.

## Demo

![Demo](assets/demo.gif)

Processed video showing object tracking, overlays, and rule-based threat analysis.

[Download Full Video](assets/demo_video.mp4)

Optional support for external Roboflow-hosted detection models through adapter-based integration.

## Visual Output

![Tracking with bounding boxes and IDs](assets/tracking.png)

Tracking with bounding boxes and IDs.

![Zone-aware monitoring](assets/zone.png)

Zone-aware monitoring.

![Annotated detection frame](assets/alert.png)

Annotated detection frame.

## Key Features

- YOLOv8-based object detection
- DeepSORT-based multi-object tracking
- Deterministic threat rules
- Restricted zone monitoring
- Loitering detection
- Runtime visualization overlays
- JSONL event logging
- Reproducible demo generation
- Optional Roboflow violence analysis

## System Design

- Adapter-first architecture around detector, tracker, threat engine, alert manager, and visualizer interfaces
- Separation between core runtime logic and demo-only enhancements
- Import-safe runtime modules that load heavy dependencies only when needed
- Deterministic testing strategy with synthetic fakes and isolated adapters

## Architecture

Video → Detection → Tracking → Threat Engine → Alerts → Visualization

## Determinism and Testing

- Fake-driven tests for pipeline behavior, domain rules, and adapter boundaries
- Isolated runtime dependencies so import-time behavior stays lightweight
- Reproducible outputs from the demo generator and real assets under `assets/`
- Injected time provider in the threat engine for deterministic rule evaluation
- Validation with `pytest` and `flake8`

## Visualization

- Bounding boxes around tracked objects
- Persistent track IDs
- Zone overlays for restricted regions
- Threat-level color coding
- Optional motion trails for track history

## Event Logging

Events are written as JSON Lines, one JSON object per line. Each record includes `timestamp`, `event_id`, `track_id`, `label`, `level`, `reason`, and `bbox`.

Real lines from `assets/sample_events.jsonl`:

```json
{"bbox": [115, 280, 225, 440], "event_id": "loitering-1-30.0", "label": "loitering", "level": "medium", "reason": "track observed for 30.0s; movement=0.0px", "timestamp": 30.0, "track_id": 1}
{"bbox": [527, 216, 627, 356], "event_id": "zone-entry-2-0-86.0", "label": "zone_entry", "level": "high", "reason": "track entered restricted zone 0", "timestamp": 86.0, "track_id": 2}
{"bbox": [763, 216, 863, 356], "event_id": "zone-presence-2-0-116.0", "label": "zone_presence", "level": "high", "reason": "track remained in restricted zone 0 for 30.0s", "timestamp": 116.0, "track_id": 2}
```

## Reproducible Demo

Run the demo generator:

```bash
python scripts/generate_demo_assets.py
```

Outputs:

- Demo video: `assets/demo_video.mp4`
- Screenshots: `assets/tracking.png`, `assets/zone.png`, `assets/alert.png`
- Event log: `assets/sample_events.jsonl`
- Optional Roboflow overlay video: `assets/demo_video_with_violence.mp4`

## Extensible Model Integration

The system supports optional external inference providers through adapter-based integration. Roboflow-hosted models can be connected without modifying the core pipeline, and any compatible Roboflow project can be configured through environment variables.

Example use cases include violence detection, fire detection, weapon detection, and accident detection.

The adapter normalizes external predictions into the internal Detection schema. Core tracking, threat rules, and visualization remain unchanged.

## Optional Roboflow Integration

Configured via `.env` and isolated from the core pipeline.

```env
ROBOFLOW_API_KEY=your_api_key
ROBOFLOW_PROJECT=your-project-name
ROBOFLOW_VERSION=1
USE_ROBOFLOW_VIDEO=true
```

`USE_ROBOFLOW_VIDEO=false` disables the feature cleanly.

## Quick Start

```bash
pip install -r requirements.txt
pytest

pip install -r requirements-runtime.txt
python main.py --source 0
```

