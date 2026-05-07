class FakeDetector:
    def __init__(self, detections, calls=None):
        self.detections = detections
        self.calls = calls

    def detect(self, frame):
        if self.calls is not None:
            self.calls.append("detector")
        return self.detections


class FakeTracker:
    def __init__(self, tracks, calls=None):
        self.tracks = tracks
        self.calls = calls

    def update(self, frame, detections):
        if self.calls is not None:
            self.calls.append("tracker")
        return self.tracks


class FakeAlertManager:
    def __init__(self, calls=None):
        self.events = []
        self.calls = calls

    def handle(self, event):
        if self.calls is not None:
            self.calls.append("alert_manager")
        self.events.append(event)
