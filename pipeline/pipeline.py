from dataclasses import dataclass
from typing import List

from surveillance.domain import ThreatEvent, Track


@dataclass(frozen=True)
class PipelineResult:
    tracks: List[Track]
    events: List[ThreatEvent]


class SurveillancePipeline:
    def __init__(self, detector, tracker, threat_engine, alert_manager):
        self.detector = detector
        self.tracker = tracker
        self.threat_engine = threat_engine
        self.alert_manager = alert_manager

    def process(self, frame):
        detections = self.detector.detect(frame)
        tracks = self.tracker.update(frame, detections)
        events = self.threat_engine(tracks, detections)

        for event in events:
            self.alert_manager.handle(event)

        return PipelineResult(tracks=tracks, events=events)
