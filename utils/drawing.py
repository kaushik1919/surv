from collections import deque


def _as_int_xyxy(bbox):
    return tuple(int(value) for value in bbox)


def _threat_color(level):
    normalized = (level or "").lower()
    if normalized == "high":
        return (0, 0, 255)
    if normalized == "medium":
        return (0, 165, 255)
    return (0, 255, 255)


class Visualizer:
    def __init__(self):
        self._trail_history = {}

    def _get_cv2(self):
        try:
            import cv2
        except ImportError:
            return None
        return cv2

    def _update_trail(self, track, trail_length):
        center_x = (track.bbox.x1 + track.bbox.x2) / 2.0
        center_y = (track.bbox.y1 + track.bbox.y2) / 2.0
        trail = self._trail_history.get(track.track_id)
        if trail is None or trail.maxlen != trail_length:
            trail = deque(maxlen=trail_length)
            self._trail_history[track.track_id] = trail
        trail.append((int(center_x), int(center_y)))
        return trail

    def draw(self, frame, tracks, events, settings):
        cv2 = self._get_cv2()
        if cv2 is None or not getattr(settings, "visualization_enabled", True):
            return frame

        event_levels = {
            event.track_id: getattr(event, "level", "")
            for event in events or []
            if event.track_id is not None
        }
        event_labels = {
            event.track_id: getattr(event, "label", "")
            for event in events or []
            if event.track_id is not None
        }
        trail_length = max(1, int(getattr(settings, "trail_length", 10)))

        for zone in getattr(settings, "restricted_zones", ()) or ():
            x1, y1, x2, y2 = _as_int_xyxy(zone)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 1)

        for track in tracks:
            x1, y1, x2, y2 = _as_int_xyxy(track.bbox.as_xyxy())
            level = event_levels.get(track.track_id, "low")
            color = _threat_color(level)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            label = event_labels.get(track.track_id, track.label)
            text = f"{track.track_id} {label} {level}".strip()
            cv2.putText(
                frame,
                text,
                (x1, max(0, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
                cv2.LINE_AA,
            )

            trail = self._update_trail(track, trail_length)
            if len(trail) > 1:
                for index in range(1, len(trail)):
                    cv2.line(frame, trail[index - 1], trail[index], color, 1)

        return frame


def draw_tracks(frame, tracks, events=None, settings=None):
    visualizer = Visualizer()
    if settings is None:
        class _Settings:
            visualization_enabled = True
            restricted_zones = ()
            trail_length = 10

        settings = _Settings()
    return visualizer.draw(frame, tracks, events or [], settings)
