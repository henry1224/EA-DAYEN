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

- Semua timestamp disimpan UTC, konversi timezone di layer presentasi saja.
- Data mentah (raw) tidak boleh ditimpa — simpan immutable, hasil pembersihan di layer terpisah.
- Gap data (candle hilang) harus dicatat, bukan di-interpolasi diam-diam.
