import importlib

from config.settings import Settings


def test_main_import_is_safe_without_runtime_dependencies():
    importlib.import_module("main")


def test_settings_include_ci_safe_defaults():
    settings = Settings()

    assert settings.confidence_threshold > 0
    assert "knife" in settings.weapon_labels
    assert settings.loitering_seconds > 0
