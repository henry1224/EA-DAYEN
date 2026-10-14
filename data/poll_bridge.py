"""Poll the MT5 file-bridge for new candles and append them to local storage. Run from the
repo root:

    python3 -m data.poll_bridge --bridge-dir "/path/to/Common/Files/EA-DAYEN" \
        --symbol EURUSD --timeframe M5

Ctrl+C to stop. Safe to re-run any time — append_candles only ever writes strictly-newer
rows (see data/store.py).
"""
import argparse
import time

from data.store import append_candles
from execution.file_bridge_adapter import BridgeError, FileBridgeAdapter

TIMEFRAME_SECONDS = {
    "M1": 60, "M5": 300, "M15": 900, "M30": 1800,
    "H1": 3600, "H4": 14400, "D1": 86400,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bridge-dir", required=True,
                         help="Folder Common Files MT5 tempat EADayenBridge.mq5 menulis (lihat docs/bridge-protocol.md)")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--timeframe", required=True, choices=sorted(TIMEFRAME_SECONDS),
                         help="Harus sama dengan input Timeframe di EADayenBridge.mq5")
    parser.add_argument("--data-dir", default="data_store", help="Folder output histori lokal (default: ./data_store)")
    parser.add_argument("--interval", type=float, default=30.0, help="Detik antar polling (default 30)")
    parser.add_argument("--count", type=int, default=50, help="Jumlah candle terbaru yang diambil tiap poll")
    args = parser.parse_args()

    adapter = FileBridgeAdapter(args.bridge_dir)
    expected_gap = TIMEFRAME_SECONDS[args.timeframe]

    print(f"polling {args.symbol} {args.timeframe} dari {args.bridge_dir} tiap {args.interval}s — Ctrl+C untuk stop")
    while True:
        try:
            candles = adapter.get_candles(args.symbol, args.count)
            written = append_candles(args.data_dir, args.symbol, args.timeframe, candles, expected_gap)
            if written:
                print(f"+{written} candle baru (terbaru: {candles[-1].time})")
        except BridgeError as e:
            print(f"bridge belum siap: {e}")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
