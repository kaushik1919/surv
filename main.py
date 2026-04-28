import argparse

from config.settings import Settings


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
        frame_width=defaults.frame_width,
        frame_skip=defaults.frame_skip,
        display=not args.no_display,
        weapon_labels=defaults.weapon_labels,
        restricted_zones=defaults.restricted_zones,
    )


def main():
    parser = build_parser()
    settings = settings_from_args(parser.parse_args())
    print(
        "Runtime adapters are configured separately. "
        f"source={settings.source}, model={settings.model_path}"
    )


if __name__ == "__main__":
    main()
