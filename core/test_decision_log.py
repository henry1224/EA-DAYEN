"""Self-check for decision_log. Run from repo root: python -m core.test_decision_log"""
import tempfile
from pathlib import Path

from .decision_log import log_decision, read_decisions


def test_append_only_and_hash_id():
    with tempfile.TemporaryDirectory() as d:
        path = str(Path(d, "decisions.jsonl"))

        id1 = log_decision(path, {"symbol": "EURUSD", "action": "BUY", "confidence": 0.7})
        id2 = log_decision(path, {"symbol": "EURUSD", "action": "WAIT", "confidence": 0.4})
        assert id1 != id2, "different decisions must get different ids"

        rows = read_decisions(path)
        assert len(rows) == 2
        assert rows[0]["action"] == "BUY"
        assert rows[1]["action"] == "WAIT"
        assert rows[0]["id"] == id1


def test_file_is_append_only_on_disk():
    with tempfile.TemporaryDirectory() as d:
        path = str(Path(d, "decisions.jsonl"))
        log_decision(path, {"action": "BUY"})
        before = Path(path).read_text()
        log_decision(path, {"action": "SELL"})
        after = Path(path).read_text()
        assert after.startswith(before), "existing lines must never be rewritten"


if __name__ == "__main__":
    test_append_only_and_hash_id()
    test_file_is_append_only_on_disk()
    print("OK — decision_log self-checks passed")
