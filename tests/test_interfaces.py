from surveillance.interfaces import BaseAlertManager, BaseDetector, BaseTracker


def test_base_interfaces_define_required_methods():
    assert hasattr(BaseDetector, "detect")
    assert hasattr(BaseTracker, "update")
    assert hasattr(BaseAlertManager, "handle")
