"""CLI entry point: python -m engine.monitor_cli [config.yaml]"""

import sys

from .config import load_config
from .monitor import CanaryMonitor


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    config_path = argv[0] if argv else "config.yaml"
    config = load_config(config_path)
    if not config.watch_dirs:
        print("No watch_dirs configured — copy config.example.yaml to config.yaml first.")
        return 2
    monitor = CanaryMonitor(config)
    print(f"[CanaryTrip] watching {len(config.watch_dirs)} dir(s), "
          f"{len(monitor.canaries)} canary file(s). Ctrl+C to stop.")
    monitor.run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
