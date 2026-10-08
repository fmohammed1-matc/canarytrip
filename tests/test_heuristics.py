"""Tests for engine.heuristics.BurstDetector — synthetic events only."""

import time

from engine.heuristics import BurstDetector


def make_detector(**kw):
    kw.setdefault("window_seconds", 10.0)
    kw.setdefault("min_files", 5)
    kw.setdefault("entropy_threshold", 7.0)
    return BurstDetector(**kw)


def test_quiet_period_no_alert():
    d = make_detector()
    now = time.time()
    for i in range(4):
        assert d.record(f"/tmp/f{i}.txt", 4.2, ts=now + i * 0.1) is None


def test_low_entropy_burst_no_alert():
    d = make_detector()
    now = time.time()
    for i in range(12):  # many files, but all low entropy
        assert d.record(f"/tmp/f{i}.txt", 3.9, ts=now + i * 0.05) is None


def test_encryption_burst_fires():
    d = make_detector()
    now = time.time()
    alert = None
    for i in range(6):
        alert = d.record(f"/tmp/f{i}.txt", 7.8, ts=now + i * 0.1) or alert
    assert alert is not None
    assert alert["type"] == "mass_encryption_burst"
    assert alert["files_affected"] >= 5
    assert 0 < alert["severity"] <= 100
    assert alert["level"] in ("MEDIUM", "HIGH", "CRITICAL")


def test_canary_touch_boosts_severity():
    d1, d2 = make_detector(), make_detector()
    now = time.time()
    a1 = a2 = None
    for i in range(6):
        a1 = d1.record(f"/tmp/f{i}.txt", 7.8, ts=now + i * 0.1) or a1
        a2 = d2.record(f"/tmp/f{i}.txt", 7.8, is_canary=(i == 0), ts=now + i * 0.1) or a2
    assert a1 and a2
    assert a2["severity"] >= a1["severity"]
    assert a2["canary_hits"] == 1


def test_window_pruning_forgets_old_events():
    d = make_detector(window_seconds=2.0)
    old = time.time() - 30
    for i in range(6):
        d.record(f"/tmp/old{i}.txt", 7.9, ts=old + i * 0.05)
    # stale burst must not fire on a fresh low-entropy event
    assert d.record("/tmp/new.txt", 4.0, ts=time.time()) is None
    assert d.suspicious_events() == []


def test_reset_clears_state():
    d = make_detector()
    now = time.time()
    for i in range(6):
        d.record(f"/tmp/f{i}.txt", 7.9, ts=now + i * 0.05)
    d.reset()
    assert d.suspicious_events() == []
