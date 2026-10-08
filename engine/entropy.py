"""Shannon entropy helpers.

Encrypted / compressed-then-encrypted content looks statistically close to
uniform random bytes, which is why per-file Shannon entropy is a classic
ransomware signal. Plaintext documents, source code and spreadsheets sit far
lower on the 0-8 bit scale.
"""

import math
from collections import Counter
from pathlib import Path

MAX_ENTROPY = 8.0  # bits per byte, the theoretical ceiling


def shannon_entropy(data: bytes) -> float:
    """Return the Shannon entropy of *data* in bits per byte (0-8)."""
    if not data:
        return 0.0
    counts = Counter(data)
    length = len(data)
    return -sum((c / length) * math.log2(c / length) for c in counts.values())


def file_entropy(path: str | Path, sample_bytes: int = 65536) -> float:
    """Estimate a file's entropy from its first *sample_bytes* bytes.

    Sampling keeps this cheap on large files; ransomware encrypts from the
    start of a file, so the head of the file is representative.
    """
    p = Path(path)
    try:
        with p.open("rb") as fh:
            chunk = fh.read(sample_bytes)
    except (OSError, PermissionError):
        return 0.0
    return shannon_entropy(chunk)
