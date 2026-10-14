"""Wraps a BrokerAdapter so every order first gets logged as an immutable decision, and in
SHADOW mode never reaches the real broker — only LIVE mode calls through. Strategy code only
ever sees a BrokerAdapter, never the raw broker connection, so this gate cannot be skipped
by accident. Mirrors plutoo's "SHADOW before real" rule (see docs/risk-management.md).
"""
import itertools

from .broker_base import BrokerAdapter
from core.decision_log import log_decision

_shadow_ticket_counter = itertools.count(1)


class ShadowGuard(BrokerAdapter):
    def __init__(self, inner: BrokerAdapter, decision_log_path: str, mode: str = "SHADOW"):
        if mode not in ("SHADOW", "LIVE"):
            raise ValueError(f"mode must be SHADOW or LIVE, got {mode!r}")
        self.inner = inner
        self.decision_log_path = decision_log_path
        self.mode = mode

    def get_candles(self, symbol, count):
        return self.inner.get_candles(symbol, count)

    def get_price(self, symbol):
        return self.inner.get_price(symbol)

    def place_order(self, symbol, side, lot, sl, tp) -> int:
        decision_id = log_decision(self.decision_log_path, {
            "mode": self.mode,
            "action": "place_order",
            "symbol": symbol,
            "side": side,
            "lot": lot,
            "sl": sl,
            "tp": tp,
        })
        if self.mode == "SHADOW":
            return -next(_shadow_ticket_counter)  # negative ticket = obviously fake
        return self.inner.place_order(symbol, side, lot, sl, tp)

    def close_order(self, ticket) -> None:
        log_decision(self.decision_log_path, {
            "mode": self.mode,
            "action": "close_order",
            "ticket": ticket,
        })
        if self.mode == "SHADOW":
            return
        self.inner.close_order(ticket)
