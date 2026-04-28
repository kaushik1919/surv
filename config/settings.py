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
    display: bool = True
    weapon_labels: FrozenSet[str] = field(
        default_factory=lambda: frozenset({"knife", "gun", "weapon"})
    )
    restricted_zones: Tuple[Tuple[int, int, int, int], ...] = ()
