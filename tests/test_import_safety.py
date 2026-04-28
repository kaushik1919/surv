import importlib


def test_runtime_adapters_are_import_safe_without_heavy_dependencies():
    importlib.import_module("detector.yolo")
    importlib.import_module("tracker.deepsort_tracker")
    importlib.import_module("utils.drawing")
