"""Wires model -> rules -> risk -> execution into one call per candle (docs/architecture.md
§ Alur Sistem). Takes a direction string, not a model object -- works today with no trained
model (feed "UP"/"DOWN"/"SIDEWAYS" straight in) and doesn't care which model produced it
once model/baseline.py has real output. Always goes through `broker` as a BrokerAdapter --
pass a ShadowGuard-wrapped one so every order is logged and, in SHADOW mode, never actually
sent (see execution/shadow_guard.py).

ponytail: TP always 0.0 (MT5 convention for "no take profit") -- docs/risk-management.md
marks TP optional / trailing-stop-as-alternative, neither implemented yet. Add real TP or
a trailing-stop module before this needs one.
"""
from execution.broker_base import BrokerAdapter
from risk.position_sizing import calc_lot_size, stop_distance_from_atr
from rules.signal_filter import filter_signal

def run_signal(
    direction: str,
    candle_time: str,
    symbol: str,
    entry_price: float,
    atr: float,
    atr_mult: float,
    equity: float,
    risk_pct: float,
    pip_size: float,
    pip_value_per_lot: float,
    broker: BrokerAdapter,
    quiet_hours: tuple = (),
) -> dict:
    """Returns {"action": "WAIT"} if filtered out, else
    {"action": "BUY"/"SELL", "lot", "sl", "tp", "ticket"} after calling `broker.place_order`.
    """
    action = filter_signal(direction, candle_time, quiet_hours)
    if action == "WAIT":
        return {"action": "WAIT"}

    stop_distance = stop_distance_from_atr(atr, atr_mult)
    lot = calc_lot_size(equity, risk_pct, stop_distance, pip_size, pip_value_per_lot)
    sl = entry_price - stop_distance if action == "BUY" else entry_price + stop_distance
    tp = 0.0

    ticket = broker.place_order(symbol, action, lot, sl, tp)
    return {"action": action, "lot": lot, "sl": sl, "tp": tp, "ticket": ticket}
