"""Self-check for core/pipeline.py. Run from repo root: python3 -m core.test_pipeline

End-to-end wiring check: model direction (synthetic here, no trained model yet) -> rules ->
risk -> ShadowGuard -> decision log. Proves the plumbing, not any trading edge -- SIDEWAYS/
quiet-hours cases must never reach the broker, BUY/SELL must log the right numbers.
"""
import tempfile
from pathlib import Path

from core.decision_log import read_decisions
from core.pipeline import run_signal
from execution.broker_base import BrokerAdapter
from execution.shadow_guard import ShadowGuard

class _FakeBroker(BrokerAdapter):
    def __init__(self):
        self.calls = []

    def get_candles(self, symbol, count):
        return []

    def get_price(self, symbol):
        return (1.0, 1.0001)

    def place_order(self, symbol, side, lot, sl, tp):
        self.calls.append((symbol, side, lot, sl, tp))
        return 999

    def close_order(self, ticket):
        pass

def _shadow_guard(tmp_dir):
    return ShadowGuard(_FakeBroker(), str(Path(tmp_dir, "decisions.jsonl")), mode="SHADOW")

def test_sideways_never_reaches_broker():
    with tempfile.TemporaryDirectory() as d:
        guard = _shadow_guard(d)
        result = run_signal(
            direction="SIDEWAYS", candle_time="2026.10.16 10:00:00", symbol="EURUSD",
            entry_price=1.0951, atr=0.0020, atr_mult=1.5, equity=10_000, risk_pct=0.01,
            pip_size=0.0001, pip_value_per_lot=10.0, broker=guard,
        )
        assert result == {"action": "WAIT"}
        assert guard.inner.calls == []
        assert read_decisions(str(Path(d, "decisions.jsonl"))) == []

def test_quiet_hours_blocks_even_a_directional_signal():
    with tempfile.TemporaryDirectory() as d:
        guard = _shadow_guard(d)
        result = run_signal(
            direction="UP", candle_time="2026.10.16 03:00:00", symbol="EURUSD",
            entry_price=1.0951, atr=0.0020, atr_mult=1.5, equity=10_000, risk_pct=0.01,
            pip_size=0.0001, pip_value_per_lot=10.0, broker=guard, quiet_hours=((0, 7),),
        )
        assert result == {"action": "WAIT"}
        assert guard.inner.calls == []

def test_up_signal_sizes_and_logs_through_shadow_guard():
    with tempfile.TemporaryDirectory() as d:
        guard = _shadow_guard(d)
        result = run_signal(
            direction="UP", candle_time="2026.10.16 10:00:00", symbol="EURUSD",
            entry_price=1.0951, atr=0.0020, atr_mult=1.5, equity=10_000, risk_pct=0.01,
            pip_size=0.0001, pip_value_per_lot=10.0, broker=guard,
        )
        # stop_distance = 0.0020*1.5 = 0.0030 -> lot = 100/(30*10) = 0.33 (see risk/test_position_sizing.py)
        assert result["action"] == "BUY"
        assert result["lot"] == 0.33
        assert result["sl"] == 1.0951 - 0.0020 * 1.5
        assert result["tp"] == 0.0
        assert result["ticket"] < 0, "SHADOW ticket must be obviously fake"

        # never reached the real broker underneath ShadowGuard...
        assert guard.inner.calls == []
        # ...but the decision is logged, with the numbers that would have been sent.
        rows = read_decisions(str(Path(d, "decisions.jsonl")))
        assert len(rows) == 1
        assert rows[0]["mode"] == "SHADOW"
        assert rows[0]["side"] == "BUY"
        assert rows[0]["lot"] == 0.33

def test_down_signal_puts_stop_above_entry():
    with tempfile.TemporaryDirectory() as d:
        guard = _shadow_guard(d)
        result = run_signal(
            direction="DOWN", candle_time="2026.10.16 10:00:00", symbol="EURUSD",
            entry_price=1.0951, atr=0.0020, atr_mult=1.5, equity=10_000, risk_pct=0.01,
            pip_size=0.0001, pip_value_per_lot=10.0, broker=guard,
        )
        assert result["action"] == "SELL"
        assert result["sl"] == 1.0951 + 0.0020 * 1.5

if __name__ == "__main__":
    test_sideways_never_reaches_broker()
    test_quiet_hours_blocks_even_a_directional_signal()
    test_up_signal_sizes_and_logs_through_shadow_guard()
    test_down_signal_puts_stop_above_entry()
    print("OK — core/pipeline.py self-checks passed")
