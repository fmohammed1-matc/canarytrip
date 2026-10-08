"""Tests for engine.alerts — no network, tmp log files only."""

import json

from engine.alerts import AlertDispatcher


def _alert():
    return {"type": "mass_encryption_burst", "level": "HIGH",
            "severity": 72.5, "files_affected": 6, "canary_hits": 1}


def test_dispatch_writes_jsonl(tmp_path, capsys):
    log = str(tmp_path / "alerts.jsonl")
    d = AlertDispatcher(log_path=log, console_alerts=False)
    out = d.dispatch(_alert())
    assert "detected_at" in out
    lines = open(log).read().strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["severity"] == 72.5


def test_dispatch_console(capsys):
    d = AlertDispatcher(log_path="", console_alerts=True)
    d.dispatch(_alert())
    captured = capsys.readouterr()
    assert "CanaryTrip" in captured.out


def test_dispatch_no_log_path_ok(tmp_path):
    d = AlertDispatcher(log_path="", webhook_url="", console_alerts=False)
    out = d.dispatch(_alert())  # must not raise
    assert out["level"] == "HIGH"


def test_webhook_failure_does_not_raise():
    d = AlertDispatcher(log_path="", webhook_url="http://127.0.0.1:9/nope",
                        console_alerts=False)
    d.dispatch(_alert())  # refused connection must be swallowed
