"""Self-check for features/build_features.py. Run from repo root: python -m features.test_build_features"""
import csv
import tempfile
from pathlib import Path

from .build_features import build_features


def test_builds_feature_file_with_expected_columns():
    with tempfile.TemporaryDirectory() as d:
        raw_dir = Path(d, "raw")
        raw_dir.mkdir()
        raw_path = raw_dir / "EURUSD_M5.csv"
        with raw_path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["time", "open", "high", "low", "close", "volume"])
            for i in range(25):
                price = 1.1000 + i * 0.0001
                writer.writerow([f"2026.10.15 0{i}:00:00", price, price + 0.0002, price - 0.0002, price, 100])

        n = build_features(d, "EURUSD", "M5")
        assert n == 25

        out_path = Path(d, "features", "EURUSD_M5.csv")
        assert out_path.exists()
        rows = list(csv.DictReader(out_path.open()))
        assert len(rows) == 25
        assert rows[0]["sma_20"] == ""  # not enough history yet -> None -> empty in CSV
        assert rows[19]["sma_20"] != ""  # 20th row (index 19) has enough history


def test_missing_raw_file_raises_clear_error():
    with tempfile.TemporaryDirectory() as d:
        try:
            build_features(d, "NOPE", "M5")
            raise AssertionError("should have raised")
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    test_builds_feature_file_with_expected_columns()
    test_missing_raw_file_raises_clear_error()
    print("OK — build_features self-checks passed")
