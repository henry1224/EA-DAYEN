"""Abstract broker interface so strategy/ML code never depends on a specific execution
backend. Two concrete backends are planned (see docs/architecture.md):

- FileBridgeAdapter  — now, MT5 on Mac via docs/bridge-protocol.md
- NativeMT5Adapter   — later, Windows/VPS via the official `MetaTrader5` pip package

Swapping backends should be a config change, not a strategy-code change.
"""
from abc import ABC, abstractmethod


class Candle:
    __slots__ = ("time", "open", "high", "low", "close", "volume")

    def __init__(self, time, open, high, low, close, volume):
        self.time = time
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume


class BrokerAdapter(ABC):
    @abstractmethod
    def get_candles(self, symbol: str, count: int) -> list[Candle]:
        ...

    @abstractmethod
    def get_price(self, symbol: str) -> tuple[float, float]:
        """Return (bid, ask)."""

    @abstractmethod
    def place_order(self, symbol: str, side: str, lot: float, sl: float, tp: float) -> int:
        """Place a market order. Returns the broker ticket id."""

    @abstractmethod
    def close_order(self, ticket: int) -> None:
        ...
