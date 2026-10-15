"""Baseline model: predict next-candle direction (UP/DOWN/SIDEWAYS) from
features/build_features.py output. First real "signal" in the pipeline -- see
docs/prd.md § Posisi dalam Quant Trading. Run from repo root:

    python3 -m model.baseline --symbol XAUUSD --timeframe M5

ponytail: scikit-learn GradientBoostingClassifier + one chronological holdout split,
no walk-forward/multi-window validation (docs/ml-strategy.md § Validasi) and no
promotion gate (§ Gate Promosi) yet. Add those before this feeds execution/ for real --
this module alone is not a go-live signal, just a trained model + a holdout score.
"""
import argparse
import csv
import pickle
from pathlib import Path

from sklearn.ensemble import GradientBoostingClassifier

_FEATURE_COLUMNS = ["sma_20", "ema_20", "rsi_14", "atr_14"]

def label_direction(closes: list, atr: list, threshold_atr_mult: float = 0.25) -> list:
    """UP/DOWN/SIDEWAYS label for the move from candle i to i+1, sized against that
    candle's own ATR -- a fixed-pip threshold would mean something different on XAUUSD
    vs a tight forex pair, ATR doesn't. `threshold_atr_mult` is a guess (ml-strategy.md
    marks the real threshold as TBD pending backtest); last index is always None (no
    next candle yet), as are indices where ATR hasn't warmed up.
    """
    out = [None] * len(closes)
    for i in range(len(closes) - 1):
        if atr[i] is None:
            continue
        delta = closes[i + 1] - closes[i]
        threshold = atr[i] * threshold_atr_mult
        if delta > threshold:
            out[i] = "UP"
        elif delta < -threshold:
            out[i] = "DOWN"
        else:
            out[i] = "SIDEWAYS"
    return out

def load_dataset(data_dir: str, symbol: str, timeframe: str, threshold_atr_mult: float = 0.25):
    """Returns (X, y): feature rows (order: _FEATURE_COLUMNS) and string labels, both
    chronological -- rows with a missing feature or no label dropped. Caller must not
    shuffle before splitting (this is a time series, not i.i.d. samples).
    """
    path = Path(data_dir, "features", f"{symbol}_{timeframe}.csv")
    if not path.exists():
        raise FileNotFoundError(f"no feature data at {path} -- run features/build_features.py first")

    with path.open() as f:
        rows = list(csv.DictReader(f))

    closes = [float(r["close"]) for r in rows]
    atr_14 = [None if r["atr_14"] == "" else float(r["atr_14"]) for r in rows]
    labels = label_direction(closes, atr_14, threshold_atr_mult)

    X, y = [], []
    for i, r in enumerate(rows):
        if labels[i] is None:
            continue
        values = [r[c] for c in _FEATURE_COLUMNS]
        if "" in values:
            continue
        X.append([float(v) for v in values])
        y.append(labels[i])
    return X, y

def train_baseline(X: list, y: list, test_fraction: float = 0.2):
    """Chronological holdout, not a random shuffle-split -- shuffling a time series
    leaks future rows into training. Returns (model, train_accuracy, test_accuracy);
    test_accuracy is None if the holdout slice ends up empty.
    """
    split = int(len(X) * (1 - test_fraction))
    X_train, y_train = X[:split], y[:split]
    X_test, y_test = X[split:], y[split:]

    model = GradientBoostingClassifier(random_state=0)
    model.fit(X_train, y_train)
    train_acc = model.score(X_train, y_train)
    test_acc = model.score(X_test, y_test) if X_test else None
    return model, train_acc, test_acc

def save_model(model, path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(model, f)

def load_model(path: str):
    with open(path, "rb") as f:
        return pickle.load(f)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--timeframe", required=True)
    parser.add_argument("--data-dir", default="data_store")
    parser.add_argument("--threshold-atr-mult", type=float, default=0.25)
    args = parser.parse_args()

    X, y = load_dataset(args.data_dir, args.symbol, args.timeframe, args.threshold_atr_mult)
    if len(X) < 50:
        raise SystemExit(
            f"cuma {len(X)} baris data berlabel -- terlalu sedikit buat training "
            f"(butuh histori lebih lama, lihat docs/status.md)"
        )

    model, train_acc, test_acc = train_baseline(X, y)
    out_path = f"{args.data_dir}/models/{args.symbol}_{args.timeframe}.pkl"
    save_model(model, out_path)

    test_acc_str = f"{test_acc:.3f}" if test_acc is not None else "N/A"
    print(f"model disimpan ke {out_path}")
    print(f"akurasi train={train_acc:.3f} test={test_acc_str}")

if __name__ == "__main__":
    main()
