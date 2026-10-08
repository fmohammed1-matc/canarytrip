"""Canary file deployment.

Canaries are ordinary-looking decoy files placed where ransomware would strike
first (Documents-style folders, shared drives). They carry a marker comment so
the tripwire can tell them apart from real user data.
"""

from __future__ import annotations

from pathlib import Path

MARKER = "CANARYTRIP_CANARY_FILE :: decoy - do not modify - monitored by CanaryTrip"

# Believable decoy bodies so the files blend in with real documents.
DECOY_BODIES = {
    ".txt": (
        "Quarterly planning notes\n"
        "=======================\n"
        "- Review vendor contracts before Friday.\n"
        "- Draft budget forecast for Q3.\n"
        "- Schedule team offsite and book the conference room.\n"
    ),
    ".docx": "Client contact sheet (placeholder)\nName, phone, email, notes...\n",
    ".csv": "id,name,department,joined\n101,A. Rivera,Sales,2021-03-14\n102,J. Chen,Support,2022-07-01\n",
    ".pdf": "%PDF-1.4 placeholder decoy document\n",
}


def _decoy_body(path: Path) -> str:
    return DECOY_BODIES.get(path.suffix.lower(), DECOY_BODIES[".txt"])


def deploy_canaries(canary_files: list[str]) -> list[str]:
    """Create every canary in *canary_files* (with parents). Idempotent.

    Returns the list of canary paths as strings. Existing files are left
    untouched unless they already carry our marker (then refreshed).
    """
    deployed: list[str] = []
    for raw in canary_files:
        path = Path(raw).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        body = f"{MARKER}\n{_decoy_body(path)}"
        if path.exists():
            try:
                if MARKER in path.read_text(encoding="utf-8", errors="ignore"):
                    path.write_text(body, encoding="utf-8")
            except OSError:
                pass
        else:
            try:
                path.write_text(body, encoding="utf-8")
            except OSError:
                continue
        deployed.append(str(path))
    return deployed


def is_canary(path: str | Path) -> bool:
    """Best-effort check: does this file carry the canary marker?"""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            head = fh.read(len(MARKER) + 64)
        return MARKER in head
    except OSError:
        return False
