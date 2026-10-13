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
