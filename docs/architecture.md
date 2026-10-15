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

## Status Modul

| Modul | Status | File |
|---|---|---|
| `data/` | ✅ Jalan | `data/store.py`, `data/poll_bridge.py` |
| `features/` | ✅ Baseline jalan | `features/indicators.py`, `features/build_features.py` |
| `execution/` (broker adapter) | ✅ Jalan | `execution/broker_base.py`, `execution/file_bridge_adapter.py` |
| `execution/` (shadow gate) | ✅ Jalan | `execution/shadow_guard.py` |
| `core/` (decision log) | ✅ Jalan | `core/decision_log.py` |
| `model/` | 🟡 Baseline jalan | `model/baseline.py` — GradientBoostingClassifier, belum pernah dilatih di data real (belum ada data terkumpul, lihat `status.md`) |
| `rules/` | ❌ Belum ada | — |
| `risk/` | ❌ Belum ada | — |
| `retrain/` | ❌ Belum ada | — |

"Jalan" berarti ada kode + self-check lolos, bukan berarti dipakai di alur trading nyata — belum ada `model/`/`rules/` yang memanggil `execution/`, jadi belum ada sinyal trading sungguhan yang dieksekusi (lihat `prd.md` § Posisi dalam Quant Trading).

## Keputusan Final

- **Broker**: Exness (MT5), eksekusi real (lihat § Keputusan: Broker & Eksekusi di bawah).
- **Simbol aktif**: XAUUSD + 7 major pairs (EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD, NZDUSD).
- **Timeframe data**: M5.
- **Format penyimpanan**: CSV (lihat `data-contracts.md`) — parquet dipertimbangkan nanti kalau volume data jadi masalah nyata, bukan sebelum itu.

## Keputusan Belum Final

- Broker API buat sumber data independen (kalau nanti perlu validasi silang) — belum perlu sekarang, satu sumber (Exness MT5) cukup untuk fase ini.

## Keputusan: Model ML Baseline

- **Library**: scikit-learn (`GradientBoostingClassifier`) — dipilih di atas XGBoost/LightGBM buat baseline karena install ringan (wheel murni, gak butuh compiler native) dan data saat ini masih kecil; upgrade ke XGBoost/LightGBM dipertimbangkan ulang kalau skala data beneran butuh (lihat `model/baseline.py` § ponytail).
- **Dependency management**: `.venv/` lokal (gitignored) + `requirements.txt` dicommit — repo ini zero-dependency sampai sekarang, jadi butuh pemisahan eksplisit dari Python sistem. Setup: `python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt`.
- **Target prediksi**: klasifikasi 3 kelas (UP/DOWN/SIDEWAYS), bukan regresi — lebih gampang map langsung ke keputusan BUY/SELL/WAIT di `rules/` nanti.

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
