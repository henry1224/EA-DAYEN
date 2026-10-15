"""Self-check for data/status.py. Run from repo root: python -m data.test_status"""
import csv
import tempfile
import time
from pathlib import Path

from .status import render_html


def test_shows_live_for_recently_updated_symbol():
    with tempfile.TemporaryDirectory() as d:
        raw = Path(d, "raw")
        raw.mkdir()
        p = raw / "XAUUSD_M5.csv"
        with p.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["time", "open", "high", "low", "close", "volume"])
            w.writerow(["2026.10.15 04:00:00", 1, 1, 1, 1, 10])

        html = render_html(d)
        assert "XAUUSD" in html
        assert "LIVE" in html
        assert "1/8 simbol live" in html


def test_shows_missing_for_symbol_with_no_file():
    with tempfile.TemporaryDirectory() as d:
        html = render_html(d)
        assert "belum ada" in html
        assert "0/8 simbol live" in html


def test_shows_gap_count():
    with tempfile.TemporaryDirectory() as d:
        raw = Path(d, "raw")
        raw.mkdir()
        (raw / "EURUSD_M5.csv").write_text("time,open,high,low,close,volume\n2026.10.15 04:00:00,1,1,1,1,1\n")
        (raw / "EURUSD_M5.gaps.csv").write_text(
            "from_time,to_time,missing_bars_estimate\n2026.10.15 03:00:00,2026.10.15 03:30:00,5\n"
        )
        html = render_html(d)
        assert ">1<" in html  # 1 gap row rendered somewhere in the table


if __name__ == "__main__":
    test_shows_live_for_recently_updated_symbol()
    test_shows_missing_for_symbol_with_no_file()
    test_shows_gap_count()
    print("OK — status self-checks passed")
