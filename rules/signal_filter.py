"""Rule layer: turn a model direction into a trade action, filtered by rules that don't
need ML (docs/ml-strategy.md § Rule Layer). Sits between model/ and execution/ -- takes
a direction, not a model object, so it works today even with no trained model (feed it
"UP"/"DOWN"/"SIDEWAYS" directly) and doesn't care which model produced it later.

Implemented now:
- Jam trading (quiet hours) -- only needs the candle's own timestamp, already in every
  raw/feature row.

Not implemented (docs/ml-strategy.md lists these, prerequisites don't exist yet):
- Trend filter -- needs higher-timeframe (H1/H4) data; pipeline only has one timeframe
  (M5) so far (see docs/architecture.md § Prinsip: Timeframe Otoritas Tunggal).
- News filter -- needs an economic calendar feed; no such source wired into data/ yet.
Add them as extra parameters here when their inputs actually exist -- don't stub them
with fake logic now, that would be worse than just not having them.
"""
from datetime import datetime

_DIRECTION_TO_ACTION = {"UP": "BUY", "DOWN": "SELL", "SIDEWAYS": "WAIT"}

def filter_signal(direction: str, candle_time: str, quiet_hours: tuple = ()) -> str:
    """Returns "BUY"/"SELL"/"WAIT". `candle_time` is the raw MT5 timestamp string
    ("YYYY.MM.DD HH:MM:SS", broker/server time -- see docs/data-contracts.md; exact
    timezone not pinned down yet, same caveat applies to `quiet_hours`).

    `quiet_hours`: tuple of (start_hour, end_hour) ranges, each half-open [start, end) in
    24h server time, e.g. ((0, 7),) to force WAIT overnight. Empty by default -- no real
    hours are decided yet (ml-strategy.md marks this TBD pending backtest), so the only
    honest default is "don't filter" rather than guessing a cutoff with no evidence.
    """
    if direction not in _DIRECTION_TO_ACTION:
        raise ValueError(f"direction tidak dikenal: {direction!r}")

    hour = datetime.strptime(candle_time, "%Y.%m.%d %H:%M:%S").hour
    for start, end in quiet_hours:
        if start <= hour < end:
            return "WAIT"

    return _DIRECTION_TO_ACTION[direction]
