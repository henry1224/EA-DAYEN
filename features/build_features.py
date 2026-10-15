"""Read raw candles from data_store/raw/, compute indicators, write data_store/features/.
Run from repo root:

    python3 -m features.build_features --symbol XAUUSD --timeframe M5

Output has one row per input candle, with indicator columns added (None where there isn't
enough history yet -- callers decide how to handle that, this module never invents values).
"""
import argparse
import csv
from pathlib import Path

from .indicators import atr, ema, rsi, sma

_FEATURE_FIELDS = [
    "time", "open", "high", "low", "close", "volume",
    "sma_20", "ema_20", "rsi_14", "atr_14",
]


def build_features(data_dir: str, symbol: str, timeframe: str) -> int:
    raw_path = Path(data_dir, "raw", f"{symbol}_{timeframe}.csv")
    if not raw_path.exists():
        raise FileNotFoundError(f"no raw data at {raw_path} -- run data/poll_bridge.py first")

    with raw_path.open() as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return 0

    closes = [float(r["close"]) for r in rows]
    highs = [float(r["high"]) for r in rows]
    lows = [float(r["low"]) for r in rows]

    sma_20 = sma(closes, 20)
    ema_20 = ema(closes, 20)
    rsi_14 = rsi(closes, 14)
    atr_14 = atr(highs, lows, closes, 14)

    out_path = Path(data_dir, "features", f"{symbol}_{timeframe}.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_FEATURE_FIELDS)
        writer.writeheader()
        for i, r in enumerate(rows):
            writer.writerow({
                "time": r["time"], "open": r["open"], "high": r["high"],
                "low": r["low"], "close": r["close"], "volume": r["volume"],
                "sma_20": sma_20[i], "ema_20": ema_20[i],
                "rsi_14": rsi_14[i], "atr_14": atr_14[i],
            })
    return len(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--timeframe", required=True)
    parser.add_argument("--data-dir", default="data_store")
    args = parser.parse_args()

    n = build_features(args.data_dir, args.symbol, args.timeframe)
    print(f"{n} baris fitur ditulis ke {args.data_dir}/features/{args.symbol}_{args.timeframe}.csv")


if __name__ == "__main__":
    main()
