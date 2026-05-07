from dataclasses import dataclass, field
from typing import FrozenSet, Tuple


@dataclass(frozen=True)
class Settings:
    source: str = "0"
    model_path: str = "yolov8n.pt"
    confidence_threshold: float = 0.25
    loitering_seconds: float = 30.0
    frame_width: int = 640
    frame_skip: int = 0
    tracker_max_age: int = 30
    tracker_n_init: int = 3
    display: bool = True
    visualization_enabled: bool = True
    log_events: bool = False
    event_log_path: str = "events.jsonl"
    trail_length: int = 10
    weapon_labels: FrozenSet[str] = field(
        default_factory=lambda: frozenset({"knife", "gun", "weapon"})
    )
    restricted_zones: Tuple[Tuple[int, int, int, int], ...] = ()
