# Strategi ML

## Pendekatan

ML (supervised) + rule-based filter + auto-retrain — bukan reinforcement learning murni. Alasan: RL butuh environment simulasi sangat akurat, data/waktu training besar, dan rawan overfit ke simulator. ML+rule lebih robust dan debug-able untuk proyek individu (lihat `prd.md`).

## Model

- Baseline: gradient boosting (XGBoost/LightGBM) — prediksi probabilitas arah harga atau expected return jangka pendek.
- Fitur dari indikator teknikal (MA, RSI, MACD, volatilitas, dll) — daftar final menyusul setelah data pipeline jalan.

## Rule Layer

Filter sinyal ML sebelum eksekusi:
- Trend filter (hanya entry searah trend timeframe lebih tinggi).
- Jam trading (hindari sesi low-liquidity).
- News filter (hindari entry di sekitar rilis data besar).

## Validasi

- Walk-forward validation (bukan random split) — data time-series, split acak bikin data leakage dari masa depan.
- Metrik: bukan cuma akurasi — cek Sharpe ratio, max drawdown, win-rate vs risk-reward.

## Kebijakan Retrain (Self-Improvement Layer)

- Retrain berkala (frekuensi final menyusul — mulai dari mingguan).
- Model baru divalidasi di luar sample sebelum menggantikan model aktif.
- Catatan beda dengan plutoo: EA-DAYEN retrain otomatis tanpa approval manual per siklus — keputusan sadar, scope EA-DAYEN memang autonomous.

## Validasi & Backtest (disederhanakan dari pendekatan plutoo)

Dipinjam karena murah diterapkan dan langsung cegah bug backtest yang umum terjadi — bukan proses berat ala plutoo (tanpa ADR/traceability matrix, cukup dipegang lewat kode + file manifest).

### Manifest Run Deterministik

Setiap run backtest wajib simpan manifest (hash SHA-256 dari input: versi data, rentang tanggal, seed, versi fitur, parameter model) sebelum hasil dianggap valid. Tujuan: hasil backtest tidak boleh berubah diam-diam karena parameter kesenggol tanpa sadar — kalau input sama, manifest hash sama, hasil harus sama.

### Time-Split Ketat (bukan random split)

Data time-series dibagi berurutan, bukan diacak:

```text
TRAINING → gap purge → VALIDATION → gap embargo → WALK_FORWARD → OOS → HOLDOUT
```

- `purge`/`embargo` = jarak waktu kosong antar window, mencegah leakage dari fitur yang menyentuh masa depan (indikator dengan lookback/lookahead tumpang tindih).
- `HOLDOUT` cuma dipakai sekali di akhir, sebelum promosi model — bukan buat iterasi berulang.

### Modeling Cost Eksekusi

Backtest tidak boleh asumsi harga sempurna. Pisahkan komponen biaya:

- Spread (bid/ask real saat itu, bukan rata-rata).
- Slippage (asumsi realistis, bukan 0).
- Komisi broker (kalau ada).
- Swap/overnight fee (kalau posisi menahan lintas hari).

### Kebijakan Ambiguitas Intrabar

Kalau 1 candle M5/M1 menyentuh SL dan TP sekaligus (urutan harga di dalam candle gak diketahui dari data OHLC biasa), tentukan kebijakan eksplisit — jangan diam-diam asumsi salah satu:

- Default konservatif: anggap SL kena duluan (worst-case) kecuali ada data tick granular yang membuktikan sebaliknya.
- Dokumentasikan kebijakan ini di kode (bukan cuma komen), karena ini asumsi yang mengubah hasil backtest signifikan.
