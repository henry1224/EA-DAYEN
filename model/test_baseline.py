"""Self-check for model/baseline.py. Run from repo root: python3 -m model.test_baseline"""
from .baseline import label_direction, load_model, save_model, train_baseline

def test_label_direction_up_down_sideways():
    closes = [100.0, 102.0, 101.9, 100.0]  # +2 (UP), -0.1 (SIDEWAYS), -1.9 (DOWN)
    atr = [1.0, 1.0, 1.0, 1.0]
    out = label_direction(closes, atr, threshold_atr_mult=0.25)
    assert out == ["UP", "SIDEWAYS", "DOWN", None]  # last index always None (no next candle)

def test_label_direction_skips_missing_atr():
    closes = [100.0, 105.0, 101.0]
    atr = [None, 1.0, None]
    out = label_direction(closes, atr, threshold_atr_mult=0.25)
    assert out == [None, "DOWN", None]  # index 0 skipped (atr not warmed up yet)

def test_train_baseline_learns_separable_pattern():
    # feature[0] > 0.5 -> UP, else DOWN. Trivially separable, so holdout accuracy
    # should be high if the chronological split + fit/score wiring is correct.
    X, y = [], []
    for i in range(200):
        if i % 2 == 0:
            X.append([1.0, 0.0, 0.0, 0.0])
            y.append("UP")
        else:
            X.append([0.0, 1.0, 0.0, 0.0])
            y.append("DOWN")

    model, train_acc, test_acc = train_baseline(X, y, test_fraction=0.2)
    assert train_acc > 0.95
    assert test_acc > 0.95

def test_train_baseline_empty_holdout_reports_none():
    X = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0]] * 5
    y = ["UP", "DOWN"] * 5
    _, _, test_acc = train_baseline(X, y, test_fraction=0.0)
    assert test_acc is None

def test_save_and_load_model_roundtrip(tmp_path="data_store/_tmp_test_model.pkl"):
    X = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0]] * 10
    y = ["UP", "DOWN"] * 10
    model, _, _ = train_baseline(X, y, test_fraction=0.0)

    save_model(model, tmp_path)
    loaded = load_model(tmp_path)
    assert list(loaded.predict([[1.0, 0.0, 0.0, 0.0]])) == list(model.predict([[1.0, 0.0, 0.0, 0.0]]))

    import os
    os.remove(tmp_path)

if __name__ == "__main__":
    test_label_direction_up_down_sideways()
    test_label_direction_skips_missing_atr()
    test_train_baseline_learns_separable_pattern()
    test_train_baseline_empty_holdout_reports_none()
    test_save_and_load_model_roundtrip()
    print("OK — model/baseline.py self-checks passed")
