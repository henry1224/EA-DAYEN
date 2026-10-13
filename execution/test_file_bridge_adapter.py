"""Self-check for FileBridgeAdapter — no MT5 needed, simulates the EA side by writing the
same files it would write. Run from the repo root:

    python -m execution.test_file_bridge_adapter
"""
import json
import tempfile
import threading
import time
from pathlib import Path

from .file_bridge_adapter import BridgeError, BridgeTimeout, FileBridgeAdapter


def test_get_price_and_candles():
    with tempfile.TemporaryDirectory() as d:
        snap = {
            "symbol": "EURUSD",
            "time": "2026-10-14 08:00:00",
            "bid": 1.0950,
            "ask": 1.0952,
            "candles": [
                {"time": "2026-10-14 07:55:00", "open": 1.0, "high": 1.1, "low": 0.9, "close": 1.05, "volume": 10},
                {"time": "2026-10-14 08:00:00", "open": 1.05, "high": 1.06, "low": 1.04, "close": 1.055, "volume": 12},
            ],
        }
        Path(d, "snapshot.json").write_text(json.dumps(snap))
        adapter = FileBridgeAdapter(d)

        assert adapter.get_price("EURUSD") == (1.0950, 1.0952)

        candles = adapter.get_candles("EURUSD", 1)
        assert len(candles) == 1 and candles[0].close == 1.055

        try:
            adapter.get_price("GBPUSD")
            raise AssertionError("should reject mismatched symbol")
        except BridgeError:
            pass


def test_place_order_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        adapter = FileBridgeAdapter(d, poll_interval=0.05, timeout=2.0)

        def fake_ea():
            deadline = time.monotonic() + 2.0
            cmd_file = None
            while time.monotonic() < deadline:
                matches = list(Path(d).glob("cmd_*.cmd"))
                if matches:
                    cmd_file = matches[0]
                    break
                time.sleep(0.02)
            assert cmd_file is not None, "adapter never wrote a command file"
            cmd_id = cmd_file.stem.removeprefix("cmd_")
            Path(d, f"done_{cmd_id}.cmd").write_text("status=ok\nticket=123456\n")

        t = threading.Thread(target=fake_ea)
        t.start()
        ticket = adapter.place_order("EURUSD", "BUY", 0.10, 1.0900, 1.1000)
        t.join()
        assert ticket == 123456


def test_place_order_timeout():
    with tempfile.TemporaryDirectory() as d:
        adapter = FileBridgeAdapter(d, poll_interval=0.05, timeout=0.2)
        try:
            adapter.place_order("EURUSD", "BUY", 0.10, 1.0900, 1.1000)
            raise AssertionError("should have timed out")
        except BridgeTimeout:
            pass


if __name__ == "__main__":
    test_get_price_and_candles()
    test_place_order_roundtrip()
    test_place_order_timeout()
    print("OK — all FileBridgeAdapter self-checks passed")
