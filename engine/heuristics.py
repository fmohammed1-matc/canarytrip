"""Mass-encryption burst heuristic.

Ransomware's behavioral fingerprint is speed + randomness: many files rewritten
with high-entropy content inside a short window. ``BurstDetector`` keeps a
sliding window of per-file modification events and scores the burst.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class FileEvent:
    path: str
    entropy: float
    ts: float = field(default_factory=time.time)
    is_canary: bool = False


class BurstDetector:
    """Sliding-window detector for ransomware-like encryption bursts."""

    def __init__(
        self,
        window_seconds: float = 10.0,
        min_files: int = 5,
        entropy_threshold: float = 7.0,
    ) -> None:
        self.window_seconds = window_seconds
        self.min_files = min_files
        self.entropy_threshold = entropy_threshold
        self._events: list[FileEvent] = []

    # -- ingest -----------------------------------------------------------
    def record(self, path: str, entropy: float, is_canary: bool = False,
               ts: float | None = None) -> dict | None:
        """Record a file-modification event; return an alert dict if a burst
        is detected, else None."""
        now = ts if ts is not None else time.time()
        self._events.append(FileEvent(path, entropy, now, is_canary))
        self._prune(now)
        return self.evaluate(now)

    def _prune(self, now: float) -> None:
        cutoff = now - self.window_seconds
        self._events = [e for e in self._events if e.ts >= cutoff]

    # -- scoring ----------------------------------------------------------
    def suspicious_events(self, now: float | None = None) -> list[FileEvent]:
        now = now if now is not None else time.time()
        self._prune(now)
        return [e for e in self._events if e.entropy >= self.entropy_threshold]

    def evaluate(self, now: float | None = None) -> dict | None:
        """Score the current window. Alert when enough high-entropy files
        changed inside the window. Severity is 0-100."""
        now = now if now is not None else time.time()
        sus = self.suspicious_events(now)
        if len(sus) < self.min_files:
            return None

        mean_entropy = sum(e.entropy for e in sus) / len(sus)
        canary_hits = sum(1 for e in sus if e.is_canary)
        span = max((e.ts for e in sus), default=now) - min((e.ts for e in sus), default=now)
        span = max(span, 0.5)  # avoid div-by-zero; sub-second bursts are hotter

        # 0-100 severity: volume (50) + entropy margin (30) + speed (20)
        volume = min(len(sus) / (self.min_files * 2), 1.0) * 50
        margin = min(max((mean_entropy - self.entropy_threshold) / (8.0 - self.entropy_threshold), 0.0), 1.0) * 30
        speed = min((len(sus) / span) / 10.0, 1.0) * 20
        severity = round(min(volume + margin + speed, 100.0), 1)
        if canary_hits:
            severity = min(severity + 10.0, 100.0)  # canary touch = strong signal

        level = "CRITICAL" if severity >= 80 else "HIGH" if severity >= 60 else "MEDIUM"
        return {
            "type": "mass_encryption_burst",
            "level": level,
            "severity": severity,
            "files_affected": len(sus),
            "canary_hits": canary_hits,
            "mean_entropy": round(mean_entropy, 3),
            "window_seconds": self.window_seconds,
            "paths": sorted({e.path for e in sus})[:25],
            "timestamp": now,
        }

    def reset(self) -> None:
        self._events.clear()
