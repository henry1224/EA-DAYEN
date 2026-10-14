"""Self-check for ShadowGuard. Run from repo root: python -m execution.test_shadow_guard"""
import tempfile
from pathlib import Path

from .broker_base import BrokerAdapter
from .shadow_guard import ShadowGuard
from core.decision_log import read_decisions


class _FakeBroker(BrokerAdapter):
    def __init__(self):
        self.live_calls = []

    def get_candles(self, symbol, count):
        return []

    def get_price(self, symbol):
        return (1.0, 1.0001)

    def place_order(self, symbol, side, lot, sl, tp):
        self.live_calls.append((symbol, side, lot, sl, tp))
        return 999

    def close_order(self, ticket):
        self.live_calls.append(("close", ticket))


def test_shadow_mode_never_calls_real_broker():
    with tempfile.TemporaryDirectory() as d:
        log_path = str(Path(d, "decisions.jsonl"))
        fake = _FakeBroker()
        guard = ShadowGuard(fake, log_path, mode="SHADOW")

        ticket = guard.place_order("EURUSD", "BUY", 0.1, 1.09, 1.11)

        assert ticket < 0, "shadow tickets must be obviously fake (negative)"
        assert fake.live_calls == [], "SHADOW must never reach the real broker"

        rows = read_decisions(log_path)
        assert len(rows) == 1 and rows[0]["mode"] == "SHADOW"


def test_live_mode_calls_through():
    with tempfile.TemporaryDirectory() as d:
        log_path = str(Path(d, "decisions.jsonl"))
        fake = _FakeBroker()
        guard = ShadowGuard(fake, log_path, mode="LIVE")

        ticket = guard.place_order("EURUSD", "BUY", 0.1, 1.09, 1.11)

        assert ticket == 999
        assert fake.live_calls == [("EURUSD", "BUY", 0.1, 1.09, 1.11)]

        rows = read_decisions(log_path)
        assert len(rows) == 1 and rows[0]["mode"] == "LIVE"


def test_rejects_invalid_mode():
    try:
        ShadowGuard(_FakeBroker(), "x.jsonl", mode="WHATEVER")
        raise AssertionError("should reject invalid mode")
    except ValueError:
        pass


if __name__ == "__main__":
    test_shadow_mode_never_calls_real_broker()
    test_live_mode_calls_through()
    test_rejects_invalid_mode()
    print("OK — ShadowGuard self-checks passed")
