"""Defensive response actions (all opt-in, all guarded).

The only automated response CanaryTrip offers is terminating the process that
is actively encrypting files — a purely defensive containment step. It is OFF
by default and must be enabled explicitly in the config.
"""

from __future__ import annotations

import os

import psutil


def processes_touching(path: str) -> list[psutil.Process]:
    """Return processes (other than us) holding *path* open right now."""
    found: list[psutil.Process] = []
    me = os.getpid()
    for proc in psutil.process_iter(["pid", "name"]):
        if proc.info["pid"] in (me, 1):
            continue
        try:
            for f in proc.open_files():
                if f.path == path:
                    found.append(proc)
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return found


def maybe_kill_suspect(path: str, enabled: bool) -> list[int]:
    """Kill processes currently writing to *path* — only if *enabled*.

    Never touches our own process or PID 1. Returns killed PIDs.
    """
    if not enabled:
        return []
    killed: list[int] = []
    for proc in processes_touching(path):
        try:
            proc.terminate()
            killed.append(proc.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return killed
