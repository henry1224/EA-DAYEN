"""Self-check for data/store.py. Run from repo root: python -m data.test_store"""
import tempfile

from execution.broker_base import Candle
from .store import append_candles, gap_path, raw_path


def _candle(t, close=1.0):
    return Candle(t, close, close, close, close, 10)


def test_append_is_idempotent_on_overlap():
    with tempfile.TemporaryDirectory() as d:
        batch1 = [_candle("2026.10.14 08:00:00"), _candle("2026.10.14 08:05:00")]
        n1 = append_candles(d, "EURUSD", "M5", batch1, expected_gap_seconds=300)
        assert n1 == 2

        # next poll re-sends an overlapping window
        batch2 = [_candle("2026.10.14 08:00:00"), _candle("2026.10.14 08:05:00"), _candle("2026.10.14 08:10:00")]
        n2 = append_candles(d, "EURUSD", "M5", batch2, expected_gap_seconds=300)
        assert n2 == 1, "only the strictly-newer candle should be written"

        rows = raw_path(d, "EURUSD", "M5").read_text().strip().splitlines()
        assert len(rows) == 4  # header + 3 candles


def test_gap_is_recorded_not_silently_filled():
    with tempfile.TemporaryDirectory() as d:
        batch = [_candle("2026.10.14 08:00:00"), _candle("2026.10.14 08:30:00")]  # missing 5 bars of M5
        append_candles(d, "EURUSD", "M5", batch, expected_gap_seconds=300)

        raw_rows = raw_path(d, "EURUSD", "M5").read_text().strip().splitlines()
        assert len(raw_rows) == 3  # header + 2 candles — nothing invented in between

        gap_file = gap_path(d, "EURUSD", "M5")
        assert gap_file.exists()
        gap_rows = gap_file.read_text().strip().splitlines()
        assert len(gap_rows) == 2  # header + 1 gap row


if __name__ == "__main__":
    test_append_is_idempotent_on_overlap()
    test_gap_is_recorded_not_silently_filled()
    print("OK — data/store self-checks passed")
