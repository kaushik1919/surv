def draw_tracks(frame, tracks, events=None):
    try:
        import cv2
    except ImportError:
        return frame

    event_track_ids = {
        event.track_id
        for event in events or []
        if event.track_id is not None
    }
    for track in tracks:
        x1, y1, x2, y2 = _as_int_xyxy(track.bbox.as_xyxy())
        color = (0, 0, 255) if track.track_id in event_track_ids else (0, 255, 0)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            frame,
            f"{track.label} #{track.track_id}",
            (x1, max(0, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1,
            cv2.LINE_AA,
        )
    return frame


def _as_int_xyxy(bbox):
    return tuple(int(value) for value in bbox)
