"""Configuration loading for CanaryTrip."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class TripwireConfig:
    # Canary files to deploy (created if missing).
    canary_files: list[str] = field(default_factory=list)
    # Directories to watch recursively (canaries should live inside these).
    watch_dirs: list[str] = field(default_factory=list)
    # --- detection tuning ---
    entropy_threshold: float = 7.0      # bits/byte; at/above counts as suspicious
    window_seconds: float = 10.0        # sliding window for burst detection
    min_files: int = 5                  # suspicious files in window to raise alert
    # --- alerting ---
    log_path: str = "alerts.jsonl"      # JSON-lines alert log ("" disables)
    webhook_url: str = ""               # POST alerts here if set
    console_alerts: bool = True
    # --- response (OFF by default; defensive kill of the encrypting process) ---
    kill_suspect_process: bool = False


def load_config(path: str | Path) -> TripwireConfig:
    """Load a YAML config file, filling in defaults for missing keys."""
    raw: dict = {}
    p = Path(path)
    if p.exists():
        with p.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
    known = {f.name for f in TripwireConfig.__dataclass_fields__.values()}
    filtered = {k: v for k, v in raw.items() if k in known}
    return TripwireConfig(**filtered)
