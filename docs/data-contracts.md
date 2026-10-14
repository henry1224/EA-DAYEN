# Kontrak Data

## Sumber Data

- Broker API (TBD: ccxt / Interactive Brokers / OANDA) — histori candle + live tick.
- Instrumen: forex major pairs (EUR/USD, GBP/USD, USD/JPY, dll — daftar final menyusul).

## Format Penyimpanan

Belum final. Kandidat: parquet (efisien untuk time-series besar) atau CSV (debug-friendly, mulai dari ini dulu karena lebih simpel).

## Skema Minimal (candle)

```text
timestamp (UTC, ISO 8601)
symbol
open, high, low, close
volume (jika tersedia dari broker)
timeframe
```

## Aturan

- Timestamp disimpan apa adanya dari waktu server broker (format MT5: `yyyy.mm.dd hh:mi:ss`, lihat `docs/bridge-protocol.md`). **Belum dikonversi ke UTC** — offset server Exness belum diverifikasi. Jangan asumsikan UTC sampai ini dicek (known gap, bukan keputusan final).
- Data mentah (raw) tidak boleh ditimpa — simpan immutable, hasil pembersihan di layer terpisah.
- Gap data (candle hilang) harus dicatat, bukan di-interpolasi diam-diam.


## Skema Penyimpanan Lokal (implementasi `data/store.py`)

```text
data_store/raw/<SYMBOL>_<TIMEFRAME>.csv        # candle, append-only, header: time,open,high,low,close,volume
data_store/raw/<SYMBOL>_<TIMEFRAME>.gaps.csv   # gap tercatat, header: from_time,to_time,missing_bars_estimate
```

Append idempotent terhadap window yang tumpang tindih (polling ulang candle yang sama tidak bikin duplikat). Gap dicatat ke file terpisah, bukan diinterpolasi diam-diam ke file raw.
