"""CanaryTrip live dashboard — FastAPI + WebSocket + Three.js frontend.

Demo mode (default): seeds a synthetic file set and streams ambient file
events so the 3D view looks alive. POST /api/simulate fires a staged burst.
POST /api/events ingests real engine events (e.g. from engine.monitor via a
webhook pointed here), so the same dashboard visualizes a live deployment.
"""

from __future__ import annotations

import asyncio
import math
import random
import time
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

STATIC = Path(__file__).parent / "static"

app = FastAPI(title="CanaryTrip Dashboard")

# ---------------------------------------------------------------- state ---
files: dict[str, dict] = {}     # path -> {entropy, tampered, is_canary, last_event}
events: list[dict] = []         # ring buffer of recent file events
alerts: list[dict] = []         # recent alerts, newest last
status = {"state": "SAFE", "since": time.time()}
_subscribers: set[WebSocket] = set()


def _seed_files() -> None:
    random.seed(7)
    vaults = ["Documents", "Projects", "Backups"]
    for i in range(42):
        v = vaults[i % 3]
        name = f"file_{i:02d}.{'txt' if i % 3 else 'csv' if i % 3 == 1 else 'docx'}"
        path = f"{v}/{name}"
        files[path] = {
            "path": path,
            "entropy": round(random.uniform(2.5, 5.5), 2),
            "tampered": False,
            "is_canary": False,
            "last_event": None,
        }
    for c in ("passwords_backup.txt", "client_records.csv", "project_plan.docx"):
        path = f"Documents/{c}"
        files[path] = {
            "path": path, "entropy": 3.1, "tampered": False,
            "is_canary": True, "last_event": None,
        }


async def _broadcast(msg: dict) -> None:
    dead = set()
    for ws in _subscribers:
        try:
            await ws.send_json(msg)
        except Exception:
            dead.add(ws)
    _subscribers.difference_update(dead)


def _push_event(path: str, entropy: float, tampered: bool = False) -> None:
    now = time.time()
    info = files.setdefault(path, {
        "path": path, "entropy": 0.0, "tampered": False,
        "is_canary": False, "last_event": None,
    })
    info["entropy"] = round(entropy, 2)
    info["tampered"] = tampered
    info["last_event"] = now
    ev = {"type": "file_event", "path": path, "entropy": info["entropy"],
          "tampered": tampered, "is_canary": info["is_canary"], "ts": now}
    events.append(ev)
    del events[:-200]
    asyncio.get_event_loop().create_task(_broadcast(ev))


async def _raise_alert(severity: float, n_files: int, canary_hits: int) -> None:
    status["state"] = "UNDER ATTACK"
    status["since"] = time.time()
    alert = {"type": "alert", "level": "CRITICAL" if severity >= 80 else "HIGH",
             "severity": round(severity, 1), "files_affected": n_files,
             "canary_hits": canary_hits, "ts": time.time()}
    alerts.append(alert)
    del alerts[:-50]
    await _broadcast(alert)
    await _broadcast({"type": "status", **status})


async def _ambient_loop() -> None:
    """Gentle background activity so the dashboard breathes."""
    while True:
        await asyncio.sleep(random.uniform(1.2, 3.0))
        if status["state"] != "SAFE":
            continue
        path = random.choice(list(files.keys()))
        _push_event(path, random.uniform(2.5, 5.8))


async def _recover_loop() -> None:
    while True:
        await asyncio.sleep(5)
        if status["state"] == "UNDER ATTACK" and time.time() - status["since"] > 30:
            status["state"] = "SAFE"
            status["since"] = time.time()
            for f in files.values():
                f["tampered"] = False
            await _broadcast({"type": "status", **status})
            await _broadcast({"type": "files_reset"})


@app.on_event("startup")
async def _startup() -> None:
    _seed_files()
    asyncio.create_task(_ambient_loop())
    asyncio.create_task(_recover_loop())


# ------------------------------------------------------------------ API ---
@app.get("/api/status")
def api_status():
    return {**status,
            "files_watched": len(files),
            "canaries": sum(1 for f in files.values() if f["is_canary"]),
            "alerts_total": len(alerts)}


@app.get("/api/files")
def api_files():
    return list(files.values())


@app.get("/api/alerts")
def api_alerts():
    return list(reversed(alerts[-50:]))


@app.post("/api/simulate")
async def api_simulate():
    """Stage a fake encryption burst (demo)."""
    targets = random.sample(
        [p for p, f in files.items() if not f["tampered"]],
        k=min(9, len(files)),
    )
    canary_hits = 0
    for i, path in enumerate(targets):
        await asyncio.sleep(0.06)
        tampered = True
        if files[path]["is_canary"]:
            canary_hits += 1
        _push_event(path, random.uniform(7.4, 7.99), tampered=tampered)
    n = len(targets)
    severity = min(50 + n * 4 + canary_hits * 5, 99.5)
    await _raise_alert(severity, n, canary_hits)
    return {"ok": True, "files": n, "canary_hits": canary_hits}


@app.post("/api/events")
async def api_events(payload: dict):
    """Ingest a real engine event: {"path":..., "entropy":..., "alert": {...}}."""
    path = str(payload.get("path", "unknown"))
    entropy = float(payload.get("entropy", 0.0))
    _push_event(path, entropy)
    if payload.get("alert"):
        a = payload["alert"]
        await _raise_alert(float(a.get("severity", 50)),
                           int(a.get("files_affected", 1)),
                           int(a.get("canary_hits", 0)))
    return {"ok": True}


@app.websocket("/ws/events")
async def ws_events(ws: WebSocket):
    await ws.accept()
    _subscribers.add(ws)
    try:
        await ws.send_json({"type": "status", **status})
        await ws.send_json({"type": "snapshot",
                            "files": list(files.values()),
                            "alerts": list(reversed(alerts[-20:]))})
        while True:
            await ws.receive_text()  # keepalive; client may ping
    except WebSocketDisconnect:
        pass
    finally:
        _subscribers.discard(ws)


app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")
