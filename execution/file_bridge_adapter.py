"""BrokerAdapter implementation that talks to a MetaTrader 5 terminal through plain files
instead of a native API — needed because the official `MetaTrader5` pip package only works
on Windows, and this runs on macOS for now (see docs/architecture.md). A companion MQL5 EA
(mql5/EADayenBridge.mq5) must be running in MT5, watching the same bridge folder. File
formats are documented in docs/bridge-protocol.md.

ponytail: file polling instead of a socket/pipe — fine while this is single-strategy and
not latency-sensitive. Upgrade to NativeMT5Adapter once this moves to Windows/VPS.
"""
import json
import os
import time
import uuid
from pathlib import Path

from .broker_base import BrokerAdapter, Candle


class BridgeTimeout(RuntimeError):
    """The MT5-side EA did not respond to a command within the timeout."""


class BridgeError(RuntimeError):
    """The MT5-side EA reported an error, or the bridge is in an unexpected state."""


class FileBridgeAdapter(BrokerAdapter):
    def __init__(self, bridge_dir: str, poll_interval: float = 0.5, timeout: float = 15.0):
        self.dir = Path(bridge_dir)
        self.poll_interval = poll_interval
        self.timeout = timeout

    def _snapshot(self, symbol: str) -> dict:
        path = self.dir / "snapshot.json"
        if not path.exists():
            raise BridgeError(f"no snapshot yet at {path} — is the MT5 EA running?")
        snap = json.loads(path.read_text())
        if snap["symbol"] != symbol:
            raise BridgeError(f"bridge is feeding {snap['symbol']}, not {symbol}")
        return snap

    def get_candles(self, symbol: str, count: int) -> list[Candle]:
        bars = self._snapshot(symbol)["candles"][-count:]
        return [Candle(b["time"], b["open"], b["high"], b["low"], b["close"], b["volume"]) for b in bars]

    def get_price(self, symbol: str) -> tuple[float, float]:
        snap = self._snapshot(symbol)
        return snap["bid"], snap["ask"]

    def place_order(self, symbol: str, side: str, lot: float, sl: float, tp: float) -> int:
        result = self._send_command(
            f"action=OPEN\nsymbol={symbol}\nside={side}\nlot={lot}\nsl={sl}\ntp={tp}\n"
        )
        return int(result["ticket"])

    def close_order(self, ticket: int) -> None:
        self._send_command(f"action=CLOSE\nticket={ticket}\n")

    def _send_command(self, body: str) -> dict:
        cmd_id = f"{int(time.time() * 1000)}-{uuid.uuid4().hex[:6]}"
        cmd_path = self.dir / f"cmd_{cmd_id}.cmd"
        tmp_path = cmd_path.with_suffix(".tmp")
        tmp_path.write_text(f"id={cmd_id}\n{body}")
        os.replace(tmp_path, cmd_path)  # atomic rename on the same filesystem

        done_path = self.dir / f"done_{cmd_id}.cmd"
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            if done_path.exists():
                result = _parse_kv(done_path.read_text())
                if result.get("status") != "ok":
                    raise BridgeError(result.get("message", "command failed"))
                return result
            time.sleep(self.poll_interval)
        raise BridgeTimeout(f"no response for command {cmd_id} within {self.timeout}s")


def _parse_kv(text: str) -> dict:
    return dict(line.split("=", 1) for line in text.splitlines() if "=" in line)
