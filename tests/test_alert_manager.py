from alerts.alert_manager import AlertManager
from surveillance.domain import ThreatEvent


def test_alert_manager_stores_events_in_memory(capsys):
    manager = AlertManager(console=True)
    event = ThreatEvent(
        "evt-1",
        1,
        "weapon",
        "critical",
        "weapon label detected",
        2.0,
    )

    manager.handle(event)

    assert manager.events == [event]
    assert "critical" in capsys.readouterr().out


def test_alert_manager_can_disable_console_output(capsys):
    manager = AlertManager(console=False)
    event = ThreatEvent("evt-2", None, "system", "low", "test event", 3.0)

    manager.handle(event)

    assert manager.events == [event]
    assert capsys.readouterr().out == ""
