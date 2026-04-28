from __future__ import annotations

import os

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency fallback

    def load_dotenv(*args, **kwargs):
        return False


load_dotenv()

API_KEY = os.getenv("ROBOFLOW_API_KEY")
PROJECT = os.getenv("ROBOFLOW_PROJECT", "violence-p1mqm")
VERSION = int(os.getenv("ROBOFLOW_VERSION", "1"))
USE_ROBOFLOW = os.getenv("USE_ROBOFLOW_VIDEO", "false").lower() == "true"


def run_roboflow_video_inference(video_path):
    if not USE_ROBOFLOW:
        return None

    if not API_KEY:
        print("Roboflow API key not set, skipping...")
        return None

    try:
        from roboflow import Roboflow
    except ImportError:
        print("Roboflow package not installed, skipping...")
        return None

    rf = Roboflow(api_key=API_KEY)
    project = rf.workspace().project(PROJECT)
    model = project.version(VERSION).model

    job_id, _signed_url, _expire_time = model.predict_video(
        video_path,
        fps=5,
        prediction_type="batch-video",
    )

    return model.poll_until_video_results(job_id)


def parse_roboflow_results(results):
    parsed = {}

    for frame in results.get("predictions", []):
        frame_id = frame.get("frame", 0)
        detections = []

        for pred in frame.get("predictions", []):
            x = pred["x"]
            y = pred["y"]
            width = pred["width"]
            height = pred["height"]

            x1 = int(x - width / 2)
            y1 = int(y - height / 2)
            x2 = int(x + width / 2)
            y2 = int(y + height / 2)

            detections.append(
                {
                    "bbox": (x1, y1, x2, y2),
                    "label": "violence",
                    "confidence": pred["confidence"],
                }
            )

        parsed[frame_id] = detections

    return parsed


def overlay_roboflow_results(input_video, parsed_results, output_path):
    import cv2

    cap = cv2.VideoCapture(input_video)
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open input video: {input_video}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    if not out.isOpened():
        cap.release()
        raise RuntimeError(f"Unable to open output video: {output_path}")

    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx in parsed_results:
            for det in parsed_results[frame_idx]:
                x1, y1, x2, y2 = det["bbox"]

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(
                    frame,
                    "violence",
                    (x1, max(0, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2,
                )

        out.write(frame)
        frame_idx += 1

    cap.release()
    out.release()