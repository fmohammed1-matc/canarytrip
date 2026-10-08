"""Tests for the FastAPI dashboard — in-memory state, no real files."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from dashboard.main import app  # noqa: E402


def _client():
    return TestClient(app)


def test_index_serves_html():
    with _client() as c:
        r = c.get("/")
    assert r.status_code == 200
    assert "CanaryTrip" in r.text
    assert "text/html" in r.headers["content-type"]


def test_status_endpoint():
    with _client() as c:
        r = c.get("/api/status")
    assert r.status_code == 200
    body = r.json()
    assert body["state"] in ("SAFE", "UNDER ATTACK")
    assert body["files_watched"] > 0
    assert body["canaries"] >= 3


def test_files_endpoint_shape():
    with _client() as c:
        files = c.get("/api/files").json()
    assert isinstance(files, list) and files
    f0 = files[0]
    assert {"path", "entropy", "tampered", "is_canary"} <= set(f0)


def test_alerts_endpoint_empty_initially():
    with _client() as c:
        assert c.get("/api/alerts").json() == []


def test_simulate_triggers_attack_state():
    with _client() as c:
        r = c.post("/api/simulate")
        assert r.status_code == 200
        assert r.json()["ok"] is True
        status = c.get("/api/status").json()
        assert status["state"] == "UNDER ATTACK"
        alerts = c.get("/api/alerts").json()
        assert alerts and alerts[0]["files_affected"] >= 5


def test_ingest_external_event():
    with _client() as c:
        r = c.post("/api/events", json={"path": "Documents/probe.txt", "entropy": 3.3})
        assert r.status_code == 200 and r.json()["ok"] is True
        paths = [f["path"] for f in c.get("/api/files").json()]
        assert "Documents/probe.txt" in paths


def test_websocket_snapshot():
    with _client() as c:
        with c.websocket_connect("/ws/events") as ws:
            status = ws.receive_json()
            assert status["type"] == "status"
            snap = ws.receive_json()
            assert snap["type"] == "snapshot"
            assert isinstance(snap["files"], list) and snap["files"]
