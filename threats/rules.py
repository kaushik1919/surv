from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Set

from surveillance.domain import ThreatEvent


@dataclass
class TrackHistory:
    first_seen: float
    positions: List[object] = field(default_factory=list)
    timestamps: List[float] = field(default_factory=list)
    emitted_labels: Set[str] = field(default_factory=set)


class ThreatEngine:
    def __init__(
        self,
        time_provider: Callable[[], float],
        weapon_labels: Iterable[str] = (),
        loitering_seconds: float = 30.0,
    ):
        self.time_provider = time_provider
        self.weapon_labels = {label.lower() for label in weapon_labels}
        self.loitering_seconds = loitering_seconds
        self.track_history: Dict[int, TrackHistory] = {}

    def __call__(self, tracks, detections):
        return self.evaluate(tracks, detections)

    def evaluate(self, tracks, detections):
        timestamp = float(self.time_provider())
        events = []
        events.extend(self._weapon_events(tracks, detections, timestamp))
        events.extend(self._loitering_events(tracks, timestamp))
        return events

    def _weapon_events(self, tracks, detections, timestamp):
        events = []
        weapon_labels = {
            detection.label.lower()
            for detection in detections
            if detection.label.lower() in self.weapon_labels
        }
        if not weapon_labels:
            return events

        for track in tracks:
            if track.label.lower() in weapon_labels:
                events.append(
                    ThreatEvent(
                        event_id=f"weapon-{track.track_id}-{timestamp}",
                        track_id=track.track_id,
                        label="weapon",
                        level="critical",
                        reason="weapon label detected",
                        timestamp=timestamp,
                    )
                )
        return events

    def _loitering_events(self, tracks, timestamp):
        events = []
        for track in tracks:
            history = self.track_history.get(track.track_id)
            if history is None:
                history = TrackHistory(first_seen=timestamp)
                self.track_history[track.track_id] = history

            history.positions.append(track.bbox)
            history.timestamps.append(timestamp)

            observed_seconds = timestamp - history.first_seen
            if observed_seconds < self.loitering_seconds:
                continue
            if "loitering" in history.emitted_labels:
                continue

            history.emitted_labels.add("loitering")
            events.append(
                ThreatEvent(
                    event_id=f"loitering-{track.track_id}-{timestamp}",
                    track_id=track.track_id,
                    label="loitering",
                    level="medium",
                    reason=f"track observed for {observed_seconds:.1f}s",
                    timestamp=timestamp,
                )
            )
        return events
