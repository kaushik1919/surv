from surveillance.domain import BoundingBox, Track
from surveillance.interfaces import BaseTracker


class DeepSortTracker(BaseTracker):
    def __init__(self):
        from deep_sort_realtime.deepsort_tracker import DeepSort

        self.tracker = DeepSort()

    def update(self, frame, detections):
        tracker_inputs = [
            (
                _xyxy_to_xywh(detection.bbox.as_xyxy()),
                detection.confidence,
                detection.label,
            )
            for detection in detections
        ]
        tracks = self.tracker.update_tracks(tracker_inputs, frame=frame)
        normalized = []
        for track in tracks:
            if not track.is_confirmed():
                continue
            x1, y1, x2, y2 = track.to_ltrb()
            normalized.append(
                Track(
                    track_id=int(track.track_id),
                    bbox=BoundingBox(float(x1), float(y1), float(x2), float(y2)),
                    label=str(track.get_det_class()),
                )
            )
        return normalized


def _xyxy_to_xywh(bbox):
    x1, y1, x2, y2 = bbox
    return [x1, y1, x2 - x1, y2 - y1]
