from collections import deque
from dataclasses import dataclass, field
from math import hypot
from typing import Callable, Deque, Dict, Iterable, Sequence, Tuple

from surveillance.domain import BoundingBox, ThreatEvent


Zone = Tuple[float, float, float, float]


def _bbox_center(bbox: BoundingBox) -> Tuple[float, float]:
    return ((bbox.x1 + bbox.x2) / 2.0, (bbox.y1 + bbox.y2) / 2.0)


def compute_movement(history: Sequence[BoundingBox]) -> float:
    history_list = list(history)
    if len(history_list) < 2:
        return 0.0

    origin_x, origin_y = _bbox_center(history_list[0])
    return max(
        hypot(center_x - origin_x, center_y - origin_y)
        for center_x, center_y in (_bbox_center(bbox) for bbox in history_list[1:])
    )


def is_static(history: Sequence[BoundingBox], threshold: float) -> bool:
    return compute_movement(history) < threshold


def is_inside_zone(bbox: BoundingBox, zone: Zone) -> bool:
    x1, y1, x2, y2 = zone
    center_x, center_y = _bbox_center(bbox)
    return x1 <= center_x <= x2 and y1 <= center_y <= y2


@dataclass
class TrackHistory:
    first_seen: float
    loitering_since: float
    position_history: Deque[BoundingBox] = field(
        default_factory=lambda: deque(maxlen=15)
    )
    timestamp_history: Deque[float] = field(
        default_factory=lambda: deque(maxlen=15)
    )
    last_label: str = ""
    emitted_events: Dict[str, float] = field(default_factory=dict)
    zone_state: Dict[int, bool] = field(default_factory=dict)
    zone_entered_at: Dict[int, float] = field(default_factory=dict)

    def reset_transient_state(self, timestamp: float, label: str):
        self.first_seen = timestamp
        self.loitering_since = timestamp
        self.position_history.clear()
        self.timestamp_history.clear()
        self.emitted_events.clear()
        self.zone_state.clear()
        self.zone_entered_at.clear()
        self.last_label = label


class ThreatEngine:
    def __init__(
        self,
        time_provider: Callable[[], float],
        weapon_labels: Iterable[str] = (),
        loitering_seconds: float = 30.0,
        movement_threshold: float = 5.0,
        restricted_zones: Iterable[Zone] = (),
        history_size: int = 15,
    ):
        self.time_provider = time_provider
        self.weapon_labels = {label.lower() for label in weapon_labels}
        self.loitering_seconds = loitering_seconds
        self.movement_threshold = movement_threshold
        self.restricted_zones = tuple(restricted_zones)
        self.history_size = max(2, int(history_size))
        self.track_history: Dict[int, TrackHistory] = {}

    def __call__(self, tracks, detections):
        return self.evaluate(tracks, detections)

    def _history_for(self, track_id: int, timestamp: float, label: str) -> TrackHistory:
        history = self.track_history.get(track_id)
        if history is None:
            history = TrackHistory(
                first_seen=timestamp,
                loitering_since=timestamp,
                last_label=label,
            )
            history.position_history = deque(maxlen=self.history_size)
            history.timestamp_history = deque(maxlen=self.history_size)
            self.track_history[track_id] = history
            return history

        if history.last_label and history.last_label != label:
            history.reset_transient_state(timestamp, label)
            history.position_history = deque(maxlen=self.history_size)
            history.timestamp_history = deque(maxlen=self.history_size)
            return history

        history.last_label = label
        return history

    def _track_ids(self, tracks):
        return {track.track_id for track in tracks}

    def _prune_disappeared_tracks(self, current_track_ids):
        disappeared = set(self.track_history) - current_track_ids
        for track_id in disappeared:
            self.track_history.pop(track_id, None)

    def _record_track_observation(
        self,
        history: TrackHistory,
        timestamp: float,
        bbox: BoundingBox,
    ):
        if history.position_history.maxlen != self.history_size:
            history.position_history = deque(
                history.position_history,
                maxlen=self.history_size,
            )
            history.timestamp_history = deque(
                history.timestamp_history,
                maxlen=self.history_size,
            )

        history.position_history.append(bbox)
        history.timestamp_history.append(timestamp)

    def _reanchor_history(
        self,
        history: TrackHistory,
        timestamp: float,
        bbox: BoundingBox,
    ):
        history.position_history = deque([bbox], maxlen=self.history_size)
        history.timestamp_history = deque([timestamp], maxlen=self.history_size)

    def evaluate(self, tracks, detections):
        timestamp = float(self.time_provider())
        current_track_ids = self._track_ids(tracks)
        self._prune_disappeared_tracks(current_track_ids)

        events = []
        events.extend(self._weapon_events(tracks, detections, timestamp))
        events.extend(self._zone_events(tracks, timestamp))
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
            if track.label.lower() not in weapon_labels:
                continue

            history = self._history_for(track.track_id, timestamp, track.label)
            self._record_track_observation(history, timestamp, track.bbox)

            event_type = "weapon"
            if event_type in history.emitted_events:
                continue

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
            history.emitted_events[event_type] = timestamp
        return events

    def _zone_events(self, tracks, timestamp):
        events = []
        if not self.restricted_zones:
            return events

        for track in tracks:
            history = self._history_for(track.track_id, timestamp, track.label)
            self._record_track_observation(history, timestamp, track.bbox)

            movement = compute_movement(history.position_history)
            if movement >= self.movement_threshold:
                history.emitted_events.pop("loitering", None)
                history.loitering_since = timestamp
                self._reanchor_history(history, timestamp, track.bbox)

            for zone_index, zone in enumerate(self.restricted_zones):
                entry_key = f"zone_entry:{zone_index}"
                presence_key = f"zone_presence:{zone_index}"
                inside_zone = is_inside_zone(track.bbox, zone)
                was_inside_zone = history.zone_state.get(zone_index, False)

                if inside_zone and not was_inside_zone:
                    history.zone_state[zone_index] = True
                    history.zone_entered_at[zone_index] = timestamp
                    if entry_key not in history.emitted_events:
                        history.emitted_events[entry_key] = timestamp
                        events.append(
                            ThreatEvent(
                                event_id=(
                                    f"zone-entry-{track.track_id}-"
                                    f"{zone_index}-{timestamp}"
                                ),
                                track_id=track.track_id,
                                label="zone_entry",
                                level="high",
                                reason=(
                                    f"track entered restricted zone "
                                    f"{zone_index}"
                                ),
                                timestamp=timestamp,
                            )
                        )
                    continue

                if not inside_zone and was_inside_zone:
                    history.zone_state[zone_index] = False
                    history.zone_entered_at.pop(zone_index, None)
                    history.emitted_events.pop(entry_key, None)
                    history.emitted_events.pop(presence_key, None)
                    continue

                if not inside_zone:
                    continue

                entered_at = history.zone_entered_at.get(zone_index, timestamp)
                if timestamp - entered_at < self.loitering_seconds:
                    continue

                if presence_key in history.emitted_events:
                    continue

                history.emitted_events[presence_key] = timestamp
                history.zone_state[zone_index] = True
                events.append(
                    ThreatEvent(
                        event_id=(
                            f"zone-presence-{track.track_id}-{zone_index}-{timestamp}"
                        ),
                        track_id=track.track_id,
                        label="zone_presence",
                        level="high",
                        reason=(
                            f"track remained in restricted zone {zone_index} "
                            f"for {timestamp - entered_at:.1f}s"
                        ),
                        timestamp=timestamp,
                    )
                )

        return events

    def _loitering_events(self, tracks, timestamp):
        events = []
        for track in tracks:
            history = self._history_for(track.track_id, timestamp, track.label)
            self._record_track_observation(history, timestamp, track.bbox)

            movement = compute_movement(history.position_history)
            if movement >= self.movement_threshold:
                history.emitted_events.pop("loitering", None)
                history.loitering_since = timestamp
                self._reanchor_history(history, timestamp, track.bbox)
                continue

            observed_seconds = timestamp - history.loitering_since
            if observed_seconds < self.loitering_seconds:
                continue

            if "loitering" in history.emitted_events:
                continue

            history.emitted_events["loitering"] = timestamp
            events.append(
                ThreatEvent(
                    event_id=f"loitering-{track.track_id}-{timestamp}",
                    track_id=track.track_id,
                    label="loitering",
                    level="medium",
                    reason=(
                        f"track observed for {observed_seconds:.1f}s; "
                        f"movement={movement:.1f}px"
                    ),
                    timestamp=timestamp,
                )
            )
        return events
