# CanaryTrip — Ransomware Canary Tripwire

A behavioral, host-based ransomware tripwire. CanaryTrip plants decoy files where
ransomware strikes first, watches the filesystem, and fires an alert when it sees
ransomware's unmistakable fingerprint: **many files rewritten with high-entropy
content in a short window**.

Strictly defensive: it detects, analyzes, and alerts. It never attacks anything.

## How it works

```
 ┌──────────────┐   ┌───────────────┐   ┌──────────────────┐   ┌───────────┐
 │ Canary files │──▶│ FS watcher    │──▶│ Shannon entropy  │──▶│  Alerts   │
 │ (decoys)     │   │ (watchdog)    │   │ + burst heuristic│   │ console / │
 └──────────────┘   └───────────────┘   │ 0–100 severity   │   │ JSON /    │
                                        └──────────────────┘   │ webhook   │
                                                               └───────────┘
```

1. **Deploy** — believable decoy files (`passwords_backup.txt`, `client_records.csv`, …)
   are created inside the directories you want to protect.
2. **Watch** — `watchdog` monitors every create/modify event recursively.
3. **Measure** — each changed file's Shannon entropy is sampled (0–8 bits/byte).
   Encrypted content clusters near 8.0; normal documents sit far below.
4. **Score** — a sliding-window burst detector counts high-entropy modifications.
   Hit the threshold (default: 5 files in 10 s above 7.0 bits) and you get a
   severity-scored alert (volume + entropy margin + speed, with a bonus when a
   canary itself is touched).
5. **Respond** — alerts go to console, a JSON-lines log, and an optional webhook.
   An opt-in, default-off action can terminate the encrypting process.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1. See it catch a simulated burst (scratch files in /tmp only):
python -m demo.simulate_burst

# 2. Launch the 3D live dashboard:
uvicorn dashboard.main:app --reload
# open http://127.0.0.1:8000 — hit "SIMULATE ATTACK" and watch the tripwire fire

# 3. Run it for real (edit config first!):
cp config.example.yaml config.yaml
python -m engine.monitor_cli config.yaml   # see "Live monitor" below
```

### Live monitor

```python
from engine import TripwireConfig, load_config, CanaryMonitor

config = load_config("config.yaml")
monitor = CanaryMonitor(config)
monitor.run_forever()   # Ctrl+C to stop
```

Point the dashboard at a live monitor by POSTing engine events to
`/api/events`, or set your webhook URL to the dashboard — same schema.

### Configuration (`config.example.yaml`)

| Key | Default | Meaning |
|---|---|---|
| `canary_files` | `[]` | decoy paths to create |
| `watch_dirs` | `[]` | directories watched recursively |
| `entropy_threshold` | `7.0` | bits/byte at which a file counts as suspicious |
| `window_seconds` | `10.0` | sliding window for burst detection |
| `min_files` | `5` | suspicious files in window to alert |
| `log_path` | `alerts.jsonl` | JSON-lines alert log (`""` disables) |
| `webhook_url` | `""` | POST alerts here (Slack/Teams/etc.) |
| `kill_suspect_process` | `false` | **off by default** — terminate the encrypting process |

## Dashboard

Dark cyber-ops UI with a Three.js **file-system particle field**: every watched
file is a node, canaries glow cyan, tampered nodes flash red with an expanding
shockwave ring. Live per-canary entropy gauges, event timeline, SAFE / UNDER
ATTACK banner, and a WebSocket event stream. Boot-sequence intro included.

## Project structure

```
canarytrip/
├── engine/            # detection engine (no UI deps)
│   ├── config.py      # YAML config + defaults
│   ├── canary.py      # decoy file deployment
│   ├── entropy.py     # Shannon entropy
│   ├── heuristics.py  # sliding-window burst detector + severity scoring
│   ├── monitor.py     # watchdog wiring: events → entropy → alerts
│   ├── alerts.py      # console / JSONL / webhook dispatch
│   └── actions.py     # opt-in suspect-process termination (default off)
├── dashboard/         # FastAPI + Three.js live UI
├── demo/              # safe burst simulator (touches /tmp only)
├── tests/             # pytest suite (synthetic data only)
└── config.example.yaml
```

## Ethical use

CanaryTrip is a **defensive** tool: deploy it on systems you own or are
authorized to protect. The process-termination action is deliberately
opt-in. Do not deploy canaries or monitoring on systems without permission.

## License

MIT — see [LICENSE](LICENSE).
