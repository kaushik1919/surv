from surveillance.interfaces import BaseAlertManager


class AlertManager(BaseAlertManager):
    def __init__(self, console=True):
        self.console = console
        self.events = []

    def handle(self, event):
        self.events.append(event)
        if self.console:
            print(
                f"[{event.level}] {event.label}: {event.reason} "
                f"(track={event.track_id}, time={event.timestamp})"
            )
