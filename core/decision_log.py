"""Immutable, append-only log of every decision the EA makes — written before execution,
not after. Plain JSONL (one line per decision), content-hashed id so an entry can't be
silently edited later. Stdlib only.

ponytail: single flat file, no rotation/compaction. Add rotation when the file gets large
enough to matter (gigabytes, not megabytes) — not before.
"""
import hashlib
import json
import time
from pathlib import Path


def log_decision(log_path: str, record: dict) -> str:
    """Append `record` to the decision log. Returns a content-hash id for this entry.

    `record` should carry whatever the strategy used to decide (features, model output,
    rule-filter result, final action) — enough to reconstruct *why* later.
    """
    entry = dict(record)
    entry["logged_at"] = time.time()
    body = json.dumps(entry, sort_keys=True, default=str)
    entry["id"] = hashlib.sha256(body.encode()).hexdigest()[:16]

    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(entry, sort_keys=True, default=str) + "\n")
    return entry["id"]


def read_decisions(log_path: str) -> list[dict]:
    path = Path(log_path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
