"""Self-check for risk/position_sizing.py. Run from repo root: python3 -m risk.test_position_sizing"""
from .position_sizing import calc_lot_size, stop_distance_from_atr

def test_stop_distance_from_atr():
    assert stop_distance_from_atr(atr=0.0020, atr_mult=1.5) == 0.0030

def test_stop_distance_rejects_non_positive():
    for bad in (0, -0.001):
        try:
            stop_distance_from_atr(atr=bad, atr_mult=1.5)
            raise AssertionError("should reject non-positive atr")
        except ValueError:
            pass

def test_calc_lot_size_matches_hand_computed_example():
    # EUR/USD-style: equity 10,000, risk 1%, 30-pip stop, $10/pip per standard lot.
    # risk_amount=100, stop_distance_pips=30 -> lot = 100 / (30*10) = 0.333... -> 0.33
    lot = calc_lot_size(
        equity=10_000, risk_pct=0.01, stop_distance=0.0030,
        pip_size=0.0001, pip_value_per_lot=10.0,
    )
    assert lot == 0.33

def test_calc_lot_size_scales_with_equity():
    # 10x equity, same risk_pct/stop/pip values -> 10x risk_amount -> 10x lot (before
    # each is independently rounded to 2dp, so compare pre-rounding via equity ratio).
    lot_1k = calc_lot_size(equity=1_000, risk_pct=0.01, stop_distance=0.0030, pip_size=0.0001, pip_value_per_lot=10.0)
    lot_100k = calc_lot_size(equity=100_000, risk_pct=0.01, stop_distance=0.0030, pip_size=0.0001, pip_value_per_lot=10.0)
    assert lot_1k == 0.03   # 10 / 300 = 0.0333 -> 0.03
    assert lot_100k == 3.33  # 1000 / 300 = 3.333 -> 3.33

def test_calc_lot_size_rejects_bad_inputs():
    base = dict(equity=10_000, risk_pct=0.01, stop_distance=0.0030, pip_size=0.0001, pip_value_per_lot=10.0)
    for field, bad in [("equity", 0), ("risk_pct", 0), ("risk_pct", 1.5), ("stop_distance", -1), ("pip_size", 0), ("pip_value_per_lot", 0)]:
        kwargs = dict(base)
        kwargs[field] = bad
        try:
            calc_lot_size(**kwargs)
            raise AssertionError(f"should reject {field}={bad}")
        except ValueError:
            pass

if __name__ == "__main__":
    test_stop_distance_from_atr()
    test_stop_distance_rejects_non_positive()
    test_calc_lot_size_matches_hand_computed_example()
    test_calc_lot_size_scales_with_equity()
    test_calc_lot_size_rejects_bad_inputs()
    print("OK — risk/position_sizing.py self-checks passed")
