from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config.settings import Settings  # noqa: E402
from event_logging.event_logger import FileEventLogger  # noqa: E402
from pipeline.pipeline import SurveillancePipeline  # noqa: E402
from surveillance.domain import (  # noqa: E402
    BoundingBox,
    Detection,
    ThreatEvent,
    Track,
)
from threats.rules import ThreatEngine  # noqa: E402
from utils.visualization import Visualizer  # noqa: E402


FRAME_COUNT = 200
DEFAULT_FPS = 10
DEFAULT_WIDTH = 960
DEFAULT_HEIGHT = 540


@dataclass(frozen=True)
class DemoObject:
    object_id: str
    track_id: int
    label: str
    start_frame: int
    end_frame: int
    confidence: float


@dataclass(frozen=True)
class LoggableEvent:
    timestamp: float
    event_id: str
    track_id: int | None
    label: str
    level: str
    reason: str
    bbox: BoundingBox


class DemoState:
    def __init__(self):
        self.frame_index = 0


class NullAlertManager:
    def handle(self, event):
        return None


class DemoScenario:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.zone = (
            int(width * 0.60),
            int(height * 0.28),
            int(width * 0.92),
            int(height * 0.84),
        )
        self.objects = (
            DemoObject("stationary", 1, "person", 0, 140, 0.97),
            DemoObject("moving", 2, "person", 40, 175, 0.94),
            DemoObject("weapon", 3, "knife", 150, 170, 0.98),
        )

    def track1_bbox(self, frame_index: int) -> BoundingBox:
        x1 = int(self.width * 0.12)
        y1 = int(self.height * 0.52)
        return BoundingBox(x1, y1, x1 + 110, y1 + 160)

    def track2_bbox(self, frame_index: int) -> BoundingBox:
        start_x = int(self.width * 0.08)
        end_x = int(self.zone[2] - 120)
        travel_frames = 70
        if frame_index <= 40:
            progress = 0.0
        else:
            progress = min(1.0, (frame_index - 40) / travel_frames)
        x1 = int(start_x + ((end_x - start_x) * progress))
        y1 = int(self.height * 0.40)
        return BoundingBox(x1, y1, x1 + 100, y1 + 140)

    def track3_bbox(self, frame_index: int) -> BoundingBox:
        x1 = int(self.width * 0.16)
        y1 = int(self.height * 0.16)
        return BoundingBox(x1, y1, x1 + 80, y1 + 110)

    def active_objects(self, frame_index: int):
        objects = []
        if (
            self.objects[0].start_frame
            <= frame_index
            < self.objects[0].end_frame
        ):
            objects.append(self.objects[0])
        if (
            self.objects[1].start_frame
            <= frame_index
            < self.objects[1].end_frame
        ):
            objects.append(self.objects[1])
        if (
            self.objects[2].start_frame
            <= frame_index
            < self.objects[2].end_frame
        ):
            objects.append(self.objects[2])
        return objects

    def bounding_box_for(self, object_id: str, frame_index: int) -> BoundingBox:
        if object_id == "stationary":
            return self.track1_bbox(frame_index)
        if object_id == "moving":
            return self.track2_bbox(frame_index)
        if object_id == "weapon":
            return self.track3_bbox(frame_index)
        raise KeyError(object_id)


class SyntheticDetector:
    def __init__(self, scenario: DemoScenario, state: DemoState):
        self.scenario = scenario
        self.state = state

    def detect(self, frame):
        detections = []
        for item in self.scenario.active_objects(self.state.frame_index):
            bbox = self.scenario.bounding_box_for(
                item.object_id,
                self.state.frame_index,
            )
            detections.append(
                Detection(
                    bbox=bbox,
                    label=item.label,
                    confidence=item.confidence,
                )
            )
        return detections


class SyntheticTracker:
    def __init__(self, scenario: DemoScenario, state: DemoState):
        self.scenario = scenario
        self.state = state

    def update(self, frame, detections):
        tracks = []
        for item in self.scenario.active_objects(self.state.frame_index):
            bbox = self.scenario.bounding_box_for(
                item.object_id,
                self.state.frame_index,
            )
            tracks.append(
                Track(track_id=item.track_id, bbox=bbox, label=item.label)
            )
        return tracks


class RealRuntimeProbe:
    def __init__(self, settings: Settings):
        self.settings = settings

    def build(self):
        model_path = Path(self.settings.model_path)
        if not model_path.exists():
            return None

        try:
            from detector.yolo import YOLODetector
            from tracker.deepsort_tracker import DeepSortTracker
        except Exception:
            return None

        try:
            detector = YOLODetector(
                model_path=self.settings.model_path,
                confidence_threshold=self.settings.confidence_threshold,
            )
            tracker = DeepSortTracker(
                max_age=self.settings.tracker_max_age,
                n_init=self.settings.tracker_n_init,
            )
        except Exception:
            return None

        return detector, tracker


def ensure_assets_dir(base_dir: Path) -> Path:
    assets_dir = base_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    return assets_dir


def make_settings(scenario: DemoScenario) -> Settings:
    return Settings(
        visualization_enabled=True,
        log_events=False,
        event_log_path="assets/sample_events.jsonl",
        trail_length=14,
        restricted_zones=(scenario.zone,),
    )


def build_background(frame_index: int, width: int, height: int):
    import cv2

    frame = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        ratio = y / max(1, height - 1)
        frame[y, :, 0] = int(26 + (18 * ratio))
        frame[y, :, 1] = int(28 + (24 * ratio))
        frame[y, :, 2] = int(34 + (26 * ratio))

    cv2.rectangle(
        frame,
        (0, int(height * 0.66)),
        (width, height),
        (20, 20, 24),
        -1,
    )
    cv2.line(
        frame,
        (0, int(height * 0.66)),
        (width, int(height * 0.66)),
        (58, 58, 68),
        2,
    )
    for x in range(0, width, 120):
        cv2.line(frame, (x, int(height * 0.66)), (x + 20, height), (40, 40, 48), 1)

    cv2.putText(
        frame,
        f"Frame {frame_index:03d}",
        (24, 36),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (210, 210, 210),
        2,
        cv2.LINE_AA,
    )
    return frame


def enrich_event(event: ThreatEvent, track_map: dict[int, Track]) -> LoggableEvent:
    track = track_map.get(event.track_id)
    bbox = track.bbox if track is not None else BoundingBox(0, 0, 0, 0)
    return LoggableEvent(
        timestamp=event.timestamp,
        event_id=event.event_id,
        track_id=event.track_id,
        label=event.label,
        level=event.level,
        reason=event.reason,
        bbox=bbox,
    )


def build_pipeline(settings: Settings, state: DemoState, scenario: DemoScenario):
    synthetic_detector = SyntheticDetector(scenario, state)
    synthetic_tracker = SyntheticTracker(scenario, state)
    threat_engine = ThreatEngine(
        time_provider=lambda: float(state.frame_index),
        weapon_labels=settings.weapon_labels,
        loitering_seconds=settings.loitering_seconds,
        movement_threshold=5.0,
        restricted_zones=settings.restricted_zones,
    )
    alert_manager = NullAlertManager()

    real_probe = RealRuntimeProbe(settings)
    real_runtime = real_probe.build()
    if real_runtime is None:
        return (
            SurveillancePipeline(
                synthetic_detector,
                synthetic_tracker,
                threat_engine,
                alert_manager,
            ),
            synthetic_detector,
            synthetic_tracker,
            "synthetic",
        )

    detector, tracker = real_runtime
    return (
        SurveillancePipeline(detector, tracker, threat_engine, alert_manager),
        detector,
        tracker,
        "real",
    )


def maybe_create_gif(mp4_path: Path, gif_path: Path):
    if shutil.which("ffmpeg") is None:
        return

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(mp4_path),
            "-vf",
            "fps=10,scale=960:-1:flags=lanczos",
            str(gif_path),
        ],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def maybe_create_roboflow_overlay(assets_path: Path):
    demo_video = assets_path / "demo_video.mp4"
    if not demo_video.exists():
        return None

    try:
        from utils.roboflow_video import (  # noqa: E402
            overlay_roboflow_results,
            parse_roboflow_results,
            run_roboflow_video_inference,
        )
    except Exception:
        return None

    results = run_roboflow_video_inference(str(demo_video))
    if not results:
        return None

    parsed = parse_roboflow_results(results)
    output_path = assets_path / "demo_video_with_violence.mp4"
    overlay_roboflow_results(str(demo_video), parsed, str(output_path))
    return output_path


def generate_assets(frame_count=FRAME_COUNT, fps=DEFAULT_FPS, assets_dir=None):
    import cv2

    repo_root = REPO_ROOT
    assets_path = ensure_assets_dir(
        repo_root if assets_dir is None else Path(assets_dir)
    )

    scenario = DemoScenario(DEFAULT_WIDTH, DEFAULT_HEIGHT)
    settings = make_settings(scenario)
    state = DemoState()
    pipeline, _detector, _tracker, runtime_mode = build_pipeline(
        settings,
        state,
        scenario,
    )
    visualizer = Visualizer()
    event_logger = FileEventLogger(assets_path / "sample_events.jsonl")

    video_path = assets_path / "demo.mp4"
    writer = cv2.VideoWriter(
        str(video_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        float(fps),
        (DEFAULT_WIDTH, DEFAULT_HEIGHT),
    )
    if not writer.isOpened():
        raise RuntimeError("Unable to open VideoWriter for demo.mp4")

    tracking_saved = False
    zone_saved = False
    weapon_saved = False
    logged_events = 0

    for frame_index in range(frame_count):
        state.frame_index = frame_index
        frame = build_background(frame_index, DEFAULT_WIDTH, DEFAULT_HEIGHT)
        result = pipeline.process(frame)

        track_map = {track.track_id: track for track in result.tracks}
        enriched_events = [enrich_event(event, track_map) for event in result.events]

        for event in enriched_events:
            event_logger.log(event)
            logged_events += 1

        output = visualizer.draw(frame, result.tracks, result.events, settings)
        writer.write(output)

        if not tracking_saved and frame_index >= 60:
            cv2.imwrite(str(assets_path / "tracking.png"), output)
            tracking_saved = True

        if not zone_saved and any(
            event.label in {"zone_entry", "zone_presence"}
            for event in result.events
        ):
            cv2.imwrite(str(assets_path / "zone.png"), output)
            zone_saved = True

        if not weapon_saved and any(event.label == "weapon" for event in result.events):
            cv2.imwrite(str(assets_path / "weapon.png"), output)
            weapon_saved = True

    writer.release()
    event_logger.flush()

    if not tracking_saved:
        fallback_frame = build_background(
            frame_count - 1,
            DEFAULT_WIDTH,
            DEFAULT_HEIGHT,
        )
        state.frame_index = frame_count - 1
        result = pipeline.process(fallback_frame)
        output = visualizer.draw(fallback_frame, result.tracks, result.events, settings)
        cv2.imwrite(str(assets_path / "tracking.png"), output)

    if not zone_saved:
        fallback_frame = build_background(
            frame_count - 1,
            DEFAULT_WIDTH,
            DEFAULT_HEIGHT,
        )
        state.frame_index = frame_count - 1
        result = pipeline.process(fallback_frame)
        output = visualizer.draw(fallback_frame, result.tracks, result.events, settings)
        cv2.imwrite(str(assets_path / "zone.png"), output)

    if not weapon_saved:
        fallback_frame = build_background(
            frame_count - 1,
            DEFAULT_WIDTH,
            DEFAULT_HEIGHT,
        )
        state.frame_index = frame_count - 1
        result = pipeline.process(fallback_frame)
        output = visualizer.draw(fallback_frame, result.tracks, result.events, settings)
        cv2.imwrite(str(assets_path / "weapon.png"), output)

    maybe_create_gif(video_path, assets_path / "demo.gif")
    maybe_create_roboflow_overlay(assets_path)
    return {
        "assets_dir": assets_path,
        "mode": runtime_mode,
        "events": logged_events,
        "video": video_path,
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Generate reproducible demo assets")
    parser.add_argument("--frames", type=int, default=FRAME_COUNT)
    parser.add_argument("--fps", type=int, default=DEFAULT_FPS)
    parser.add_argument("--assets-dir", default=None)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    result = generate_assets(
        frame_count=args.frames,
        fps=args.fps,
        assets_dir=args.assets_dir,
    )
    print(f"Generated demo assets in {result['assets_dir']}")
    print(f"Runtime mode: {result['mode']}")
    print(f"Events logged: {result['events']}")


if __name__ == "__main__":
    main()
