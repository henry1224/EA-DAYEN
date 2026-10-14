# Arsitektur EA-DAYEN

## Alur Sistem

```text
Broker API (histori + live tick)
→ Data Pipeline (ingest, bersihkan, simpan)
→ Feature Engineering (indikator teknikal, volatilitas, dll)
→ Model ML (prediksi probabilitas arah/return)
→ Rule Layer (filter: trend, jam, news)
→ Risk & Position Sizing
→ Eksekusi Order (broker API)
→ Log Hasil Transaksi
→ Retrain Loop (berkala, pakai data performa terbaru)
```

## Komponen

| Komponen | Tanggung Jawab |
|---|---|
| `data/` | Ingest histori + live data dari broker API, simpan ke format konsisten (parquet/csv) |
| `features/` | Hitung fitur teknikal dari raw price data |
| `model/` | Training, validasi, serialisasi model ML |
| `rules/` | Filter sinyal ML dengan aturan teknikal/waktu |
| `risk/` | Hitung lot size, SL/TP, cek max drawdown |
| `execution/` | Kirim order ke broker API, pantau posisi terbuka |
| `retrain/` | Job berkala: ambil data baru, retrain, validasi, promosikan model baru |
| `core/` | Util lintas-modul: decision log immutable, dll |

## Keputusan Belum Final

- Broker API spesifik (ccxt/IB/OANDA) — menunggu keputusan user.
- Model ML spesifik — mulai dari baseline sederhana (gradient boosting), eksperimen lanjut setelah baseline jalan.

## Keputusan: Broker & Eksekusi (Exness via MT5)

Eksekusi real memakai akun **Exness** (MT5). Karena package Python resmi `MetaTrader5` cuma jalan di Windows, dan tahap ini develop/jalan di **MacBook native** (bukan VM/VPS dulu), dipakai pola **file-bridge**:

```text
MT5 app (Mac, native MetaQuotes) + 1 EA kecil (MQL5)
         │
         ├─ tulis snapshot data pasar → file JSON   (MT5 → Python baca)
         └─ poll file command → OrderSend() ke Exness (Python → MT5 eksekusi)
```

### Abstraksi Broker

Supaya migrasi ke VPS/Windows nanti tidak perlu rewrite logika strategi, dipakai 1 interface kecil:

```text
BrokerAdapter
├── get_candles(symbol, timeframe, count)
├── get_price(symbol)
├── place_order(symbol, side, lot, sl, tp)
└── close_order(order_id)

Implementasi:
├── FileBridgeAdapter   — dipakai sekarang (Mac, lewat EA MQL5 + file JSON)
└── NativeMT5Adapter    — dipakai setelah pindah ke Windows/VPS (pip MetaTrader5)
```

Kode strategi/ML/risk manggil `BrokerAdapter` saja — ganti implementasi = ganti config, bukan rewrite.

### Rencana Migrasi

1. Sekarang: develop & jalan di MacBook pakai `FileBridgeAdapter`.
2. Setelah terbukti jalan baik (hasil shadow/demo memuaskan): pindah ke VPS Windows, ganti ke `NativeMT5Adapter`.
3. Latency file-bridge (~1-5 detik polling) diterima di fase ini karena bukan strategi scalping ultra-cepat.

## Prinsip: Timeframe Otoritas Tunggal

Satu timeframe ditetapkan sebagai **satu-satunya otoritas entry** (contoh: M5). Timeframe lain boleh dipakai sebagai filter/konteks (trend H1/H4) atau penyempurnaan SL (M1), tapi **tidak boleh memicu entry sendiri**. Dipinjam dari plutoo — mencegah sinyal konflik antar timeframe yang bikin logika sulit di-debug. Timeframe final ditentukan saat rule layer mulai ditulis (lihat `docs/ml-strategy.md`).

## Decision Log (Immutable)

Setiap keputusan (`place_order`/`close_order`) wajib tercatat ke `core/decision_log.py` **sebelum** eksekusi — bukan cuma kalau sukses. Log append-only (JSONL, id dari hash konten), gak bisa diedit diam-diam. Tujuan: kalau EA ambil posisi aneh, bisa direkonstruksi alasannya dari log, bukan nebak dari memori.
