from abc import ABC, abstractmethod


class BaseDetector(ABC):
    @abstractmethod
    def detect(self, frame):
        """Return normalized detections for a frame."""


class BaseTracker(ABC):
    @abstractmethod
    def update(self, frame, detections):
        """Return normalized tracks for a frame and detections."""


class BaseAlertManager(ABC):
    @abstractmethod
    def handle(self, event):
        """Handle one threat event."""
