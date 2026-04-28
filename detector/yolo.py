from surveillance.domain import BoundingBox, Detection
from surveillance.interfaces import BaseDetector


class YOLODetector(BaseDetector):
    def __init__(self, model_path="yolov8n.pt", confidence_threshold=0.25):
        from ultralytics import YOLO

        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold

    def detect(self, frame):
        results = self.model(frame)
        detections = []
        for result in results:
            names = result.names
            for box in result.boxes:
                confidence = float(box.conf[0])
                if confidence < self.confidence_threshold:
                    continue
                cls_id = int(box.cls[0])
                x1, y1, x2, y2 = [float(value) for value in box.xyxy[0]]
                detections.append(
                    Detection(
                        bbox=BoundingBox(x1, y1, x2, y2),
                        label=str(names[cls_id]),
                        confidence=confidence,
                    )
                )
        return detections
