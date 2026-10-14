"""Append-only local storage for candle history. CSV, one file per symbol+timeframe — simple
enough to inspect by eye, no new dependency. Existing rows are never rewritten (raw data
immutable, per docs/data-contracts.md); only strictly-newer candles get appended, so feeding
it an overlapping window (every bridge poll re-sends the same last N candles) is naturally
idempotent. Missing bars are recorded to a sidecar `.gaps.csv`, never interpolated.

ponytail: CSV + full-file read to find the last timestamp. Fine up to a few hundred thousand
rows; move to SQLite/parquet when a file gets large enough that read-the-tail matters.
"""
import csv
from datetime import datetime
from pathlib import Path

from execution.broker_base import Candle

_FIELDS = ["time", "open", "high", "low", "close", "volume"]
# Matches MT5's TimeToString(TIME_DATE|TIME_SECONDS) output exactly — see docs/bridge-protocol.md.
_TIME_FMT = "%Y.%m.%d %H:%M:%S"


def raw_path(data_dir: str, symbol: str, timeframe: str) -> Path:
    return Path(data_dir, "raw", f"{symbol}_{timeframe}.csv")


def gap_path(data_dir: str, symbol: str, timeframe: str) -> Path:
    return Path(data_dir, "raw", f"{symbol}_{timeframe}.gaps.csv")


def _parse(t: str) -> datetime:
    return datetime.strptime(t, _TIME_FMT)


def last_time(path: Path) -> str | None:
    if not path.exists():
        return None
    with path.open() as f:
        rows = list(csv.DictReader(f))
    return rows[-1]["time"] if rows else None


def append_candles(data_dir: str, symbol: str, timeframe: str, candles: list[Candle],
                    expected_gap_seconds: float | None = None) -> int:
    """Append candles newer than what's already stored. Returns how many were written."""
    path = raw_path(data_dir, symbol, timeframe)
    path.parent.mkdir(parents=True, exist_ok=True)

    last = last_time(path)
    new_rows = [c for c in candles if last is None or c.time > last]
    if not new_rows:
        return 0

    is_new_file = not path.exists()
    with path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDS)
        if is_new_file:
            writer.writeheader()
        for c in new_rows:
            writer.writerow({"time": c.time, "open": c.open, "high": c.high,
                              "low": c.low, "close": c.close, "volume": c.volume})

    if expected_gap_seconds:
        gaps = []
        prev_time = last
        for c in new_rows:
            if prev_time is not None:
                delta = (_parse(c.time) - _parse(prev_time)).total_seconds()
                if delta > expected_gap_seconds * 1.5:
                    missing = round(delta / expected_gap_seconds) - 1
                    gaps.append((prev_time, c.time, missing))
            prev_time = c.time
        if gaps:
            _write_gaps(data_dir, symbol, timeframe, gaps)

    return len(new_rows)


def _write_gaps(data_dir: str, symbol: str, timeframe: str, gaps: list[tuple[str, str, int]]) -> None:
    path = gap_path(data_dir, symbol, timeframe)
    is_new = not path.exists()
    with path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["from_time", "to_time", "missing_bars_estimate"])
        if is_new:
            writer.writeheader()
        for from_time, to_time, missing in gaps:
            writer.writerow({"from_time": from_time, "to_time": to_time, "missing_bars_estimate": missing})
