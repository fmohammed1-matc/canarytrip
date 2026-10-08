"""Filesystem monitor: watchdog -> entropy -> burst heuristic -> alerts."""

from __future__ import annotations

import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .actions import maybe_kill_suspect
from .alerts import AlertDispatcher
from .canary import deploy_canaries, is_canary
from .config import TripwireConfig
from .entropy import file_entropy
from .heuristics import BurstDetector


class _Handler(FileSystemEventHandler):
    def __init__(self, monitor: "CanaryMonitor") -> None:
        self.monitor = monitor
        self._last_seen: dict[str, float] = {}

    def _debounced(self, path: str) -> bool:
        now = time.time()
        if now - self._last_seen.get(path, 0.0) < 1.0:
            return True
        self._last_seen[path] = now
        return False

    def on_modified(self, event) -> None:
        if event.is_directory:
            return
        self.monitor.handle_change(event.src_path)

    def on_created(self, event) -> None:
        if event.is_directory:
            return
        self.monitor.handle_change(event.src_path)

    # watchdog calls on_modified for every write; thin wrapper keeps the
    # debounce logic in one place for tests.
    def emit(self, path: str) -> None:
        if not self._debounced(path):
            self.monitor.handle_change(path)


class CanaryMonitor:
    """Deploy canaries, watch directories, and raise alerts on bursts."""

    def __init__(self, config: TripwireConfig) -> None:
        self.config = config
        self.canaries = set(deploy_canaries(config.canary_files))
        self.detector = BurstDetector(
            window_seconds=config.window_seconds,
            min_files=config.min_files,
            entropy_threshold=config.entropy_threshold,
        )
        self.dispatcher = AlertDispatcher(
            log_path=config.log_path,
            webhook_url=config.webhook_url,
            console_alerts=config.console_alerts,
        )
        self.handler = _Handler(self)
        self.observer = Observer()
        self.alerts_raised: list[dict] = []

    # -- lifecycle ------------------------------------------------------
    def start(self) -> None:
        for d in self.config.watch_dirs:
            p = Path(d).expanduser()
            p.mkdir(parents=True, exist_ok=True)
            self.observer.schedule(self.handler, str(p), recursive=True)
        self.observer.start()

    def stop(self) -> None:
        self.observer.stop()
        self.observer.join(timeout=5)

    def run_forever(self) -> None:
        self.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    # -- event pipeline ---------------------------------------------------
    def handle_change(self, path: str) -> dict | None:
        """Process one changed file through entropy -> heuristic -> alert."""
        entropy = file_entropy(path)
        canary = path in self.canaries or is_canary(path)
        alert = self.detector.record(path, entropy, is_canary=canary)
        if alert:
            alert = self.dispatcher.dispatch(alert)
            self.alerts_raised.append(alert)
            if self.config.kill_suspect_process:
                killed = maybe_kill_suspect(path, enabled=True)
                if killed:
                    print(f"[CanaryTrip] terminated suspect PIDs: {killed}")
        return alert
