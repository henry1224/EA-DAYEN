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

## Keputusan Belum Final

- Broker API spesifik (ccxt/IB/OANDA) — menunggu keputusan user.
- Model ML spesifik — mulai dari baseline sederhana (gradient boosting), eksperimen lanjut setelah baseline jalan.
