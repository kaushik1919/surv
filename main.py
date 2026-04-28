import argparse

from alerts.alert_manager import AlertManager
from config.settings import Settings
from detector.yolo import YOLODetector
from pipeline.pipeline import SurveillancePipeline
from threats.rules import ThreatEngine
from tracker.deepsort_tracker import DeepSortTracker
from utils.drawing import draw_tracks


def build_parser():
    parser = argparse.ArgumentParser(
        description="Real-time surveillance and threat detection"
    )
    parser.add_argument("--source", default=None, help="Video source path or camera id")
    parser.add_argument("--model", default=None, help="YOLOv8 model path")
    parser.add_argument(
        "--confidence",
        type=float,
        default=None,
        help="Detection confidence threshold",
    )
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Disable runtime display window",
    )
    parser.add_argument(
        "--frame-width",
        type=int,
        default=None,
        help="Resize frames to this width before processing",
    )
    parser.add_argument(
        "--frame-skip",
        type=int,
        default=None,
        help="Process one frame, then skip this many frames",
    )
    return parser


def settings_from_args(args):
    defaults = Settings()
    return Settings(
        source=args.source if args.source is not None else defaults.source,
        model_path=args.model if args.model is not None else defaults.model_path,
        confidence_threshold=(
            args.confidence
            if args.confidence is not None
            else defaults.confidence_threshold
        ),
        loitering_seconds=defaults.loitering_seconds,
        frame_width=(
            args.frame_width
            if args.frame_width is not None
            else defaults.frame_width
        ),
        frame_skip=(
            args.frame_skip
            if args.frame_skip is not None
            else defaults.frame_skip
        ),
        tracker_max_age=defaults.tracker_max_age,
        tracker_n_init=defaults.tracker_n_init,
        display=not args.no_display,
        weapon_labels=defaults.weapon_labels,
        restricted_zones=defaults.restricted_zones,
    )


def parse_source(source):
    if isinstance(source, str) and source.isdigit():
        return int(source)
    return source


def open_video_source(settings):
    import cv2

    return cv2.VideoCapture(parse_source(settings.source))


def build_runtime_pipeline(settings):
    import time

    detector = YOLODetector(
        model_path=settings.model_path,
        confidence_threshold=settings.confidence_threshold,
    )
    tracker = DeepSortTracker(
        max_age=settings.tracker_max_age,
        n_init=settings.tracker_n_init,
    )
    threat_engine = ThreatEngine(
        time_provider=time.monotonic,
        weapon_labels=settings.weapon_labels,
        loitering_seconds=settings.loitering_seconds,
    )
    alert_manager = AlertManager(console=True)
    return SurveillancePipeline(detector, tracker, threat_engine, alert_manager)


def resize_frame(frame, frame_width):
    if frame_width <= 0:
        return frame

    current_width = frame.shape[1]
    if current_width == frame_width:
        return frame

    import cv2

    scale = frame_width / current_width
    height = int(frame.shape[0] * scale)
    return cv2.resize(frame, (frame_width, height))


def run_video_loop(settings, pipeline=None):
    import cv2

    capture = open_video_source(settings)
    runtime_pipeline = pipeline or build_runtime_pipeline(settings)
    frame_index = 0

    while capture.isOpened():
        ok, frame = capture.read()
        if not ok:
            break

        if settings.frame_skip and frame_index % (settings.frame_skip + 1) != 0:
            frame_index += 1
            continue

        frame = resize_frame(frame, settings.frame_width)
        result = runtime_pipeline.process(frame)
        output = draw_tracks(frame, result.tracks, result.events)

        if settings.display:
            cv2.imshow("Surveillance", output)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        frame_index += 1

    capture.release()
    if settings.display:
        cv2.destroyAllWindows()


def main():
    parser = build_parser()
    settings = settings_from_args(parser.parse_args())
    run_video_loop(settings)


if __name__ == "__main__":
    main()
