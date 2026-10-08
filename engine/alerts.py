"""Alert dispatch: console, JSON-lines log, optional webhook."""

from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

LEVEL_COLORS = {
    "CRITICAL": "\033[91m",  # red
    "HIGH": "\033[93m",      # yellow
    "MEDIUM": "\033[94m",    # blue
}
RESET = "\033[0m"


class AlertDispatcher:
    def __init__(self, log_path: str = "alerts.jsonl", webhook_url: str = "",
                 console_alerts: bool = True) -> None:
        self.log_path = log_path
        self.webhook_url = webhook_url
        self.console_alerts = console_alerts

    def dispatch(self, alert: dict) -> dict:
        """Send *alert* to every configured channel. Returns the alert with a
        UTC timestamp attached."""
        alert = dict(alert)
        alert["detected_at"] = datetime.now(timezone.utc).isoformat()

        if self.console_alerts:
            color = LEVEL_COLORS.get(alert.get("level", ""), "")
            print(
                f"{color}[CanaryTrip {alert.get('level', 'ALERT')}] "
                f"severity={alert.get('severity')} "
                f"files={alert.get('files_affected')} "
                f"canaries={alert.get('canary_hits')}{RESET}"
            )
        if self.log_path:
            try:
                with open(self.log_path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(alert) + "\n")
            except OSError:
                pass
        if self.webhook_url:
            self._post_webhook(alert)
        return alert

    def _post_webhook(self, alert: dict) -> None:
        try:
            req = urllib.request.Request(
                self.webhook_url,
                data=json.dumps(alert).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp.read(1024)
        except Exception:
            # Alerting must never crash the monitor.
            pass
