"""CanaryTrip engine — behavioral ransomware tripwire (defensive only)."""

from .config import TripwireConfig, load_config
from .entropy import shannon_entropy, file_entropy
from .canary import deploy_canaries
from .heuristics import BurstDetector
from .alerts import AlertDispatcher
from .actions import maybe_kill_suspect
from .monitor import CanaryMonitor

__all__ = [
    "TripwireConfig",
    "load_config",
    "shannon_entropy",
    "file_entropy",
    "deploy_canaries",
    "BurstDetector",
    "AlertDispatcher",
    "maybe_kill_suspect",
    "CanaryMonitor",
]

__version__ = "0.1.0"
