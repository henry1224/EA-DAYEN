"""Self-check for features/indicators.py. Run from repo root: python -m features.test_indicators"""
from .indicators import atr, ema, rsi, sma


def test_sma_basic():
    values = [1, 2, 3, 4, 5]
    out = sma(values, 3)
    assert out[:2] == [None, None]
    assert out[2] == 2.0   # (1+2+3)/3
    assert out[3] == 3.0   # (2+3+4)/3
    assert out[4] == 4.0   # (3+4+5)/3


def test_ema_converges_toward_constant_series():
    values = [10.0] * 30
    out = ema(values, 10)
    assert out[9] == 10.0
    assert out[-1] == 10.0  # flat input -> EMA settles exactly on the constant


def test_rsi_all_gains_is_100():
    closes = [float(i) for i in range(1, 20)]  # strictly increasing -> no losses
    out = rsi(closes, period=14)
    assert out[14] == 100.0


def test_rsi_all_losses_is_0():
    closes = [float(i) for i in range(20, 1, -1)]  # strictly decreasing -> no gains
    out = rsi(closes, period=14)
    assert out[14] == 0.0


def test_rsi_bounded_0_100_on_mixed_data():
    closes = [1, 2, 1.5, 3, 2.5, 4, 3.5, 5, 4.5, 6, 5.5, 7, 6.5, 8, 7.5, 9]
    out = rsi(closes, period=14)
    value = out[14]
    assert value is not None
    assert 0.0 <= value <= 100.0


def test_atr_zero_for_flat_candles():
    n = 20
    highs = [10.0] * n
    lows = [10.0] * n
    closes = [10.0] * n
    out = atr(highs, lows, closes, period=14)
    assert out[14] == 0.0  # no range, no gaps -> zero volatility


def test_atr_positive_for_moving_candles():
    highs = [10 + i for i in range(20)]
    lows = [9 + i for i in range(20)]
    closes = [9.5 + i for i in range(20)]
    out = atr(highs, lows, closes, period=14)
    assert out[14] > 0


if __name__ == "__main__":
    test_sma_basic()
    test_ema_converges_toward_constant_series()
    test_rsi_all_gains_is_100()
    test_rsi_all_losses_is_0()
    test_rsi_bounded_0_100_on_mixed_data()
    test_atr_zero_for_flat_candles()
    test_atr_positive_for_moving_candles()
    print("OK — indicators self-checks passed")
