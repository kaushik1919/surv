from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class BoundingBox:
    x1: float
    y1: float
    x2: float
    y2: float

    def as_xyxy(self) -> Tuple[float, float, float, float]:
        return self.x1, self.y1, self.x2, self.y2


@dataclass(frozen=True)
class Detection:
    bbox: BoundingBox
    label: str
    confidence: float

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


@dataclass(frozen=True)
class Track:
    track_id: int
    bbox: BoundingBox
    label: str


@dataclass(frozen=True)
class ThreatEvent:
    event_id: str
    track_id: Optional[int]
    label: str
    level: str
    reason: str
    timestamp: float
