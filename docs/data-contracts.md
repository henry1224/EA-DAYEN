# Kontrak Data

## Sumber Data

- **Broker**: Exness (MT5), lewat file-bridge lokal (lihat `bridge-protocol.md`) — bukan ccxt/IB/OANDA, itu opsi lama sebelum keputusan broker final (lihat `architecture.md` § Keputusan Final).
- **Instrumen** (8, semua live sejak 2026-10-15): XAUUSD, EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD, NZDUSD.
- **Timeframe**: M5.

## Format Penyimpanan

**CSV** — final untuk fase ini (bukan lagi kandidat). Alasan: data masih kecil (ribuan baris per simbol), CSV cukup cepat dan jauh lebih gampang di-debug (buka langsung, diff-able di git kalau perlu). Parquet dipertimbangkan ulang kalau volume data beneran jadi bottleneck nyata — belum terjadi.

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

## Skema Fitur (implementasi `features/build_features.py`)

```text
data_store/features/<SYMBOL>_<TIMEFRAME>.csv
header: time,open,high,low,close,volume,sma_20,ema_20,rsi_14,atr_14
```

- Satu baris output per baris input (`raw/`) — gak ada baris dibuang/ditambah.
- Kolom indikator kosong (bukan 0, bukan interpolasi) kalau histori belum cukup buat periode-nya (contoh: `sma_20` kosong di 19 baris pertama) — konsisten dengan aturan "jangan mengarang data" di atas.
- Daftar indikator akan nambah seiring `ml-strategy.md` berkembang (MACD, Bollinger Bands, sesi waktu, dll) — tambah kolom baru, jangan ubah makna kolom lama (breaking change ke konsumen yang sudah ada).
