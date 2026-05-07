"""
Run the real pipeline end-to-end on assets/input_video.mp4 and produce:
- assets/demo_video.mp4 (annotated via Visualizer)
- assets/sample_events.jsonl (events produced by the threat engine)
- assets/tracking.png, assets/zone.png, assets/alert.png (frames extracted from demo_video.mp4)

This script uses the real detector, tracker, threat engine, and Visualizer.
Do NOT use sample_events.jsonl for overlay drawing; overlays are produced live from pipeline results.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import cv2
from config.settings import Settings
from main import build_runtime_pipeline
from utils.visualization import Visualizer
from event_logging.event_logger import FileEventLogger
from utils.roboflow_video import (  # noqa: E402
    overlay_roboflow_results,
    parse_roboflow_results,
    run_roboflow_video_inference,
)

ROOT = os.path.dirname(os.path.dirname(__file__))
ASSETS = os.path.join(ROOT, "assets")
INPUT_VIDEO = os.path.join(ASSETS, "input_video.mp4")
DEMO_VIDEO = os.path.join(ASSETS, "demo_video.mp4")
EVENT_LOG = os.path.join(ASSETS, "sample_events.jsonl")
TRACK_IMG = os.path.join(ASSETS, "tracking.png")
ZONE_IMG = os.path.join(ASSETS, "zone.png")
ALERT_IMG = os.path.join(ASSETS, "alert.png")


def run_pipeline_and_write_video():
    settings = Settings(
        source=INPUT_VIDEO,
        visualization_enabled=True,
        log_events=True,
        event_log_path=EVENT_LOG,
        frame_width=0,  # keep original size
        display=False,
    )

    pipeline = build_runtime_pipeline(settings)
    visualizer = Visualizer()
    event_logger = FileEventLogger(settings.event_log_path)

    cap = cv2.VideoCapture(INPUT_VIDEO)
    if not cap.isOpened():
        raise SystemExit(f"cannot open input video {INPUT_VIDEO}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    tmp_out = DEMO_VIDEO + ".tmp.mp4"
    writer = cv2.VideoWriter(tmp_out, fourcc, fps, (width, height))

    frame_idx = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # process frame through pipeline
            result = pipeline.process(frame)

            # log events
            for ev in result.events:
                event_logger.log(ev)

            # draw overlays using the real Visualizer
            out_frame = visualizer.draw(frame, result.tracks, result.events, settings)

            writer.write(out_frame)
            frame_idx += 1
    finally:
        cap.release()
        writer.release()
        event_logger.flush()

    # replace demo video with the new one
    os.replace(tmp_out, DEMO_VIDEO)
    print("Wrote demo video:", DEMO_VIDEO)

    results = run_roboflow_video_inference(str(DEMO_VIDEO))
    if results:
        parsed = parse_roboflow_results(results)
        violence_video = os.path.join(ASSETS, "demo_video_with_violence.mp4")
        overlay_roboflow_results(
            str(DEMO_VIDEO),
            parsed,
            violence_video,
        )
        print("Wrote Roboflow overlay video:", violence_video)


def extract_screenshots_from_demo():
    if not os.path.exists(DEMO_VIDEO):
        raise SystemExit("demo video missing")

    cap = cv2.VideoCapture(DEMO_VIDEO)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = frame_count / fps if fps else 0

    # pick timestamps from event log if available
    timestamps = []
    if os.path.exists(EVENT_LOG):
        with open(EVENT_LOG, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    import json

                    ev = json.loads(line)
                    ts = ev.get("timestamp")
                    if ts is not None:
                        timestamps.append(ts)
                except Exception:
                    continue

    # if we have no events, fall back to evenly spaced timestamps
    if not timestamps:
        if duration <= 0:
            timestamps = [0.5, 1.0, 1.5]
        else:
            timestamps = [max(0, duration * 0.25), max(0, duration * 0.5), max(0, duration * 0.75)]

    # clamp timestamps
    timestamps = [min(max(0.0, t), max(0.0, duration - 1.0)) for t in timestamps[:3]]

    names = [TRACK_IMG, ZONE_IMG, ALERT_IMG]
    for ts, name in zip(timestamps, names):
        frame_no = int(round(ts * fps))
        frame_no = max(0, min(frame_no, frame_count - 1))
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
        ret, frame = cap.read()
        if not ret:
            print("failed to read frame at", ts)
            continue
        cv2.imwrite(name, frame)
        print("wrote", name)

    cap.release()


if __name__ == "__main__":
    os.makedirs(ASSETS, exist_ok=True)
    run_pipeline_and_write_video()
    extract_screenshots_from_demo()
    print("Done: generated demo_video and screenshots")
