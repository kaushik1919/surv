# Runtime Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add runtime YOLOv8, DeepSORT, and video input wiring while preserving import safety and local-only validation.

**Architecture:** Runtime packages remain isolated behind adapters and runtime entrypoint functions. Core domain models, interfaces, threat rules, and pipeline logic remain unchanged. Tests use fake runtime modules and monkeypatching instead of installing heavy dependencies.

**Tech Stack:** Python 3, pytest, flake8, optional runtime packages in `requirements-runtime.txt`.

---

## Task 1: YOLOv8 Runtime Adapter

**Files:**
- Modify: `detector/yolo.py`
- Test: `tests/test_yolo_adapter.py`

- [ ] Write tests that inject a fake `ultralytics` module and assert normalized `Detection` output.
- [ ] Verify tests fail before implementation.
- [ ] Implement adapter normalization without module-level `ultralytics` imports.
- [ ] Run `python -m pytest tests/test_yolo_adapter.py -v`.
- [ ] Commit `feat: implement YOLOv8 runtime adapter`.

## Task 2: DeepSORT Runtime Adapter

**Files:**
- Modify: `tracker/deepsort_tracker.py`
- Test: `tests/test_deepsort_adapter.py`

- [ ] Write tests that inject a fake `deep_sort_realtime.deepsort_tracker` module and assert normalized `Track` output.
- [ ] Verify tests fail before implementation.
- [ ] Implement adapter normalization without module-level DeepSORT imports.
- [ ] Run `python -m pytest tests/test_deepsort_adapter.py -v`.
- [ ] Commit `feat: integrate DeepSORT tracking adapter`.

## Task 3: Video Input And Runtime Wiring

**Files:**
- Modify: `config/settings.py`
- Modify: `main.py`
- Test: `tests/test_main_runtime.py`

- [ ] Write tests for CLI settings, webcam/file source parsing, frame resize defaults, frame skipping defaults, and import-safe `main`.
- [ ] Verify tests fail before implementation.
- [ ] Keep `main.py` thin by adding runtime construction and video-loop helpers without business logic.
- [ ] Import OpenCV only inside runtime helpers.
- [ ] Run `python -m pytest tests/test_main_runtime.py -v`.
- [ ] Commit `feat: add video input handling in main`.

## Final Validation

- [ ] Run `python -m pip install -r requirements.txt`.
- [ ] Run `python -m flake8 .`.
- [ ] Run `python -m pytest -v`.
- [ ] Push `feature/runtime-integration` to `https://github.com/kaushik1919/surv.git`.
