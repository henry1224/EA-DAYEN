"""Generate a local status dashboard (data_store/status.html) for the 8 data pollers.

Run once:
    python3 -m data.status

Run continuously (regenerates every --interval seconds, so an open browser tab with the
page's auto-refresh stays current):
    python3 -m data.status --loop

The page is a plain local file (file://) — never published, never leaves this machine.
Freshness is inferred from each raw CSV's mtime (same signal used manually all session):
a poller writing on --interval cadence should touch the file well under STALE_AFTER seconds.
"""
import argparse
import csv
import time
from datetime import datetime
from pathlib import Path

SYMBOLS = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD"]

# A raw CSV only gets a new row (and a new mtime) when a new candle actually closes -- NOT
# every poll cycle. For M5 that means the file can legitimately sit untouched for ~5 minutes
# between updates even while the poller is perfectly healthy. "Stale" has to be judged
# against the candle period, not the poll interval -- using a flat 60s here originally
# produced false STALE alarms every cycle (caught 2026-10-15). Same TIMEFRAME_SECONDS table
# poll_bridge.py uses for gap detection, so both stay consistent.
TIMEFRAME_SECONDS = {
    "M1": 60, "M5": 300, "M15": 900, "M30": 1800,
    "H1": 3600, "H4": 14400, "D1": 86400,
}


def _symbol_status(data_dir: str, symbol: str, timeframe: str) -> dict:
    stale_after = TIMEFRAME_SECONDS.get(timeframe, 300) * 1.5
    raw_path = Path(data_dir, "raw", f"{symbol}_{timeframe}.csv")
    gaps_path = Path(data_dir, "raw", f"{symbol}_{timeframe}.gaps.csv")

    if not raw_path.exists():
        return {"symbol": symbol, "state": "belum ada", "age": None, "rows": 0,
                "last_time": "-", "gaps": 0}

    age = time.time() - raw_path.stat().st_mtime
    with raw_path.open() as f:
        rows = list(csv.DictReader(f))
    last_time = rows[-1]["time"] if rows else "-"

    gaps = 0
    if gaps_path.exists():
        with gaps_path.open() as f:
            gaps = sum(1 for _ in csv.DictReader(f))

    state = "live" if age < stale_after else "stale"
    return {"symbol": symbol, "state": state, "age": age, "rows": len(rows),
            "last_time": last_time, "gaps": gaps}


def render_html(data_dir: str, timeframe: str = "M5") -> str:
    rows = [_symbol_status(data_dir, s, timeframe) for s in SYMBOLS]
    live_count = sum(1 for r in rows if r["state"] == "live")

    def fmt_age(age):
        if age is None:
            return "-"
        if age < 90:
            return f"{int(age)}s lalu"
        return f"{int(age / 60)}m lalu"

    body_rows = "\n".join(
        f'<tr class="{r["state"]}">'
        f'<td>{r["symbol"]}</td>'
        f'<td class="state">{"🟢 LIVE" if r["state"] == "live" else "🔴 STALE" if r["state"] == "stale" else "⚪ belum ada"}</td>'
        f'<td>{fmt_age(r["age"])}</td>'
        f'<td>{r["rows"]}</td>'
        f'<td>{r["last_time"]}</td>'
        f'<td>{r["gaps"]}</td>'
        f'</tr>'
        for r in rows
    )

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="10">
<title>EA-DAYEN — Status Data Poller</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{ background: #0d1117; color: #e6edf3; font-family: ui-monospace, Menlo, monospace;
         padding: 24px; max-width: 760px; margin: 0 auto; }}
  h1 {{ font-size: 18px; font-weight: 600; margin-bottom: 4px; }}
  .meta {{ color: #8b949e; font-size: 13px; margin-bottom: 20px; }}
  .summary {{ font-size: 14px; margin-bottom: 16px; padding: 10px 14px; border-radius: 8px;
             background: #161b22; border: 1px solid #30363d; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ text-align: left; color: #8b949e; font-weight: 500; padding: 8px 10px;
       border-bottom: 1px solid #30363d; }}
  td {{ padding: 8px 10px; border-bottom: 1px solid #21262d; }}
  tr.stale td.state {{ color: #f85149; }}
  tr.live td.state {{ color: #3fb950; }}
  .footer {{ margin-top: 20px; color: #6e7681; font-size: 12px; }}
</style>
</head>
<body>
  <h1>EA-DAYEN — Status Data Poller</h1>
  <div class="meta">Auto-refresh tiap 10 detik · dibuat {generated_at}</div>
  <div class="summary">{live_count}/8 simbol live</div>
  <table>
    <thead>
      <tr><th>Simbol</th><th>Status</th><th>Update terakhir</th><th>Baris</th><th>Candle terakhir</th><th>Gap</th></tr>
    </thead>
    <tbody>
      {body_rows}
    </tbody>
  </table>
  <div class="footer">File lokal — gak dipublish, gak ada data keluar dari Mac ini.</div>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data_store")
    parser.add_argument("--timeframe", default="M5")
    parser.add_argument("--loop", action="store_true", help="regenerate terus-menerus")
    parser.add_argument("--interval", type=float, default=15.0)
    args = parser.parse_args()

    out_path = Path(args.data_dir, "status.html")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not args.loop:
        out_path.write_text(render_html(args.data_dir, args.timeframe))
        print(f"ditulis ke {out_path}")
        return

    print(f"update {out_path} tiap {args.interval}s — Ctrl+C untuk stop")
    while True:
        out_path.write_text(render_html(args.data_dir, args.timeframe))
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
