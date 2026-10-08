"""End-to-end demo: stage a fake 'encryption burst' in /tmp and watch the
tripwire catch it. Touches NOTHING outside /tmp/canarytrip-demo.

Usage:
    python -m demo.simulate_burst
"""

import os
import shutil
import sys
import tempfile
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import (  # noqa: E402
    AlertDispatcher,
    BurstDetector,
    TripwireConfig,
    deploy_canaries,
    shannon_entropy,
)

SCRATCH = os.path.join(tempfile.gettempdir(), "canarytrip-demo")


def stage_vault() -> list[str]:
    """Create a scratch vault with canaries + ordinary decoy documents."""
    shutil.rmtree(SCRATCH, ignore_errors=True)
    vault = os.path.join(SCRATCH, "vault")
    os.makedirs(vault, exist_ok=True)

    canaries = [os.path.join(vault, name) for name in (
        "passwords_backup.txt", "client_records.csv", "project_plan.docx",
    )]
    deploy_canaries(canaries)

    # Ordinary low-entropy documents a burst would also "encrypt".
    for i in range(9):
        with open(os.path.join(vault, f"report_{i:02d}.txt"), "w") as fh:
            fh.write(("Quarterly summary line %d.\n" % i) * 40)
    return canaries


def fake_encrypt(path: str) -> float:
    """Overwrite a file with random bytes (what ransomware does) and return
    the resulting entropy. Scratch files only."""
    with open(path, "wb") as fh:
        fh.write(os.urandom(4096))
    with open(path, "rb") as fh:
        return shannon_entropy(fh.read())


def main() -> int:
    from engine.canary import is_canary

    canaries = stage_vault()
    print(f"[demo] staged scratch vault at {SCRATCH}")

    detector = BurstDetector(window_seconds=10, min_files=5, entropy_threshold=7.0)
    dispatcher = AlertDispatcher(log_path=os.path.join(SCRATCH, "alerts.jsonl"))

    vault = os.path.join(SCRATCH, "vault")
    targets = sorted(
        os.path.join(vault, f) for f in os.listdir(vault) if f.endswith((".txt", ".csv", ".docx"))
    )
    print(f"[demo] simulating encryption burst over {len(targets)} files...")

    alert = None
    for path in targets:  # rapid-fire, like real ransomware
        was_canary = is_canary(path)  # check before content is destroyed
        entropy = fake_encrypt(path)
        print(f"  modified {os.path.basename(path):24s} entropy={entropy:.2f}")
        alert = detector.record(path, entropy, is_canary=was_canary) or alert
        time.sleep(0.05)

    if alert:
        dispatcher.dispatch(alert)
        print(f"\n[demo] TRIPWIRE FIRED: level={alert['level']} "
              f"severity={alert['severity']} files={alert['files_affected']} "
              f"canaries={alert['canary_hits']}")
        print(f"[demo] alert log: {os.path.join(SCRATCH, 'alerts.jsonl')}")
        return 0
    print("\n[demo] no alert raised (unexpected)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
