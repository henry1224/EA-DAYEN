"""Position sizing: docs/risk-management.md § Position Sizing formula, as code.

ponytail: `pip_value_per_lot` is a required argument, not computed here -- it's
instrument-specific (differs for XAUUSD vs USD-quote vs JPY pairs vs USD-base pairs) and
depends on the live exchange rate for non-USD-quote pairs. Hardcoding a per-symbol table
here risks silently sizing a real order wrong; the correct source is the broker's own
symbol spec (MT5 `SymbolInfoDouble`), which isn't wired through `BrokerAdapter` yet. Add
a `get_pip_value(symbol)` to `BrokerAdapter` and look it up there before this feeds
execution/ for real.

`risk_pct` and the ATR multiplier below are also not final (docs/risk-management.md:
"angka final menyusul setelah backtest") -- callers must pass them explicitly, no default
pretending to be a validated number.
"""

def stop_distance_from_atr(atr: float, atr_mult: float) -> float:
    """SL distance (same price units as atr) -- volatility-based, not a fixed pip count
    (docs/risk-management.md: "atr_14 jadi kandidat dasar buat stop_distance otomatis").
    """
    if atr <= 0:
        raise ValueError(f"atr harus positif, dapat {atr}")
    if atr_mult <= 0:
        raise ValueError(f"atr_mult harus positif, dapat {atr_mult}")
    return atr * atr_mult

def calc_lot_size(
    equity: float,
    risk_pct: float,
    stop_distance: float,
    pip_size: float,
    pip_value_per_lot: float,
) -> float:
    """lot_size = (equity * risk_pct) / (stop_distance_pips * pip_value_per_lot).

    All five inputs are validated (this sizes a real order -- a silent garbage-in here
    becomes a silent wrong-size trade, not just a wrong number on screen). Result rounded
    to 2 decimals (common broker lot step); actual min/max/step per symbol isn't wired in
    from the broker yet, so this doesn't clamp to a tradeable size -- caller must still
    check against the broker's limits before sending an order.
    """
    if equity <= 0:
        raise ValueError(f"equity harus positif, dapat {equity}")
    if not (0 < risk_pct <= 1):
        raise ValueError(f"risk_pct harus di (0, 1], dapat {risk_pct}")
    if stop_distance <= 0:
        raise ValueError(f"stop_distance harus positif, dapat {stop_distance}")
    if pip_size <= 0:
        raise ValueError(f"pip_size harus positif, dapat {pip_size}")
    if pip_value_per_lot <= 0:
        raise ValueError(f"pip_value_per_lot harus positif, dapat {pip_value_per_lot}")

    risk_amount = equity * risk_pct
    stop_distance_pips = stop_distance / pip_size
    lot_size = risk_amount / (stop_distance_pips * pip_value_per_lot)
    return round(lot_size, 2)
