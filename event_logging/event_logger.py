import json
from abc import ABC, abstractmethod
from pathlib import Path


class BaseEventLogger(ABC):
    @abstractmethod
    def log(self, event):
        raise NotImplementedError

    @abstractmethod
    def flush(self):
        raise NotImplementedError


EventLogger = BaseEventLogger


class FileEventLogger(BaseEventLogger):
    def __init__(self, file_path, max_bytes=1_048_576):
        self.file_path = Path(file_path)
        self.max_bytes = int(max_bytes)

    def _serialize_event(self, event):
        bbox = [0, 0, 0, 0]
        if getattr(event, "track_id", None) is not None:
            bbox_value = getattr(event, "bbox", None)
            if bbox_value is not None:
                if hasattr(bbox_value, "as_xyxy"):
                    bbox = [int(value) for value in bbox_value.as_xyxy()]
                else:
                    bbox = [int(value) for value in bbox_value]

        return {
            "timestamp": event.timestamp,
            "event_id": event.event_id,
            "track_id": event.track_id,
            "label": event.label,
            "level": event.level,
            "reason": event.reason,
            "bbox": bbox,
        }

    def _rotate_if_needed(self, line_size):
        if not self.file_path.exists():
            return

        current_size = self.file_path.stat().st_size
        if (
            current_size <= self.max_bytes
            and current_size + line_size <= self.max_bytes
        ):
            return

        rotated_path = self.file_path.with_name(self.file_path.name + ".1")
        if rotated_path.exists():
            rotated_path.unlink()
        self.file_path.replace(rotated_path)

    def log(self, event):
        payload = self._serialize_event(event)
        line = json.dumps(payload, sort_keys=True)
        encoded = (line + "\n").encode("utf-8")

        self._rotate_if_needed(len(encoded))
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with self.file_path.open("a", encoding="utf-8") as handle:
            handle.write(line)
            handle.write("\n")

    def flush(self):
        return None
