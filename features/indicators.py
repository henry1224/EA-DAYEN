"""Technical indicators, pure stdlib (no numpy/pandas -- not installed, and data volume here
doesn't need them yet; add a dependency only if/when this becomes a real bottleneck).

Every function takes a list of floats and returns a same-length list, with `None` for
indices where there isn't enough history yet (so callers can align indicator output
directly against the original candle rows by index, no off-by-one bookkeeping).
"""


def sma(values: list, period: int) -> list:
    out = [None] * len(values)
    for i in range(period - 1, len(values)):
        window = values[i - period + 1:i + 1]
        out[i] = sum(window) / period
    return out


def ema(values: list, period: int) -> list:
    out = [None] * len(values)
    if len(values) < period:
        return out
    k = 2 / (period + 1)
    seed = sum(values[:period]) / period
    out[period - 1] = seed
    prev = seed
    for i in range(period, len(values)):
        prev = values[i] * k + prev * (1 - k)
        out[i] = prev
    return out


def rsi(closes: list, period: int = 14) -> list:
    """Wilder's RSI. First value lands at index `period` (needs `period` deltas, i.e.
    `period + 1` closes)."""
    out = [None] * len(closes)
    if len(closes) < period + 1:
        return out

    gains = [0.0] * len(closes)
    losses = [0.0] * len(closes)
    for i in range(1, len(closes)):
        delta = closes[i] - closes[i - 1]
        gains[i] = max(delta, 0.0)
        losses[i] = max(-delta, 0.0)

    avg_gain = sum(gains[1:period + 1]) / period
    avg_loss = sum(losses[1:period + 1]) / period
    out[period] = _rsi_from_averages(avg_gain, avg_loss)

    for i in range(period + 1, len(closes)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        out[i] = _rsi_from_averages(avg_gain, avg_loss)

    return out


def _rsi_from_averages(avg_gain: float, avg_loss: float) -> float:
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - 100.0 / (1.0 + rs)


def atr(highs: list, lows: list, closes: list, period: int = 14) -> list:
    """Wilder's ATR (volatility). First value lands at index `period`."""
    n = len(highs)
    out = [None] * n
    if n < period + 1:
        return out

    tr = [0.0] * n
    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        tr[i] = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )

    avg_tr = sum(tr[1:period + 1]) / period
    out[period] = avg_tr
    for i in range(period + 1, n):
        avg_tr = (avg_tr * (period - 1) + tr[i]) / period
        out[i] = avg_tr

    return out
