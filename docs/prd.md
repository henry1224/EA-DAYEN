# PRD — EA-DAYEN

## Ringkasan

EA-DAYEN adalah Expert Advisor otomatis untuk forex major pairs, dibangun dengan Python + broker API. Sistem mengeksekusi order sendiri berdasar sinyal ML yang difilter aturan teknikal, dan memperbaiki diri lewat retrain berkala.

## Tujuan

- Prediksi arah harga jangka pendek pakai ML (supervised, misal XGBoost/LightGBM) dari fitur teknikal.
- Filter sinyal ML dengan rule layer (trend filter, jam trading, news filter).
- Eksekusi order otomatis (entry, SL/TP, position sizing) tanpa approval manual per transaksi.
- Retrain model berkala memakai data performa terbaru (self-improvement layer).
- Risk management ketat: sizing berbasis equity/volatilitas, max drawdown limit, kill-switch.

## Bukan Tujuan

- Reinforcement learning murni (ditolak — risiko overfit ke simulator, butuh environment sangat akurat, effort tinggi untuk individu).
- Multi-instrumen di fase awal — fokus forex major pairs dulu.
- Multi-broker/agregasi akun.
- Menjamin profit atau winrate tertentu.

## Mengapa Terpisah dari Plutoo

Plutoo adalah terminal decision-support dengan prinsip inti: ML tidak boleh mengirim perintah sendiri, adaptasi model harus versioned dan lewat review promosi manual, mode live otonom eksplisit di luar scope. EA-DAYEN punya tujuan berlawanan — eksekusi dan retrain otomatis tanpa approval manual per siklus. Menggabungkan keduanya akan melanggar governance plutoo yang sudah disetujui. Keputusan: dua proyek berjalan independen, tanpa share kode atau data.

## Layer Sistem (target akhir)

1. Data pipeline (histori + live feed dari broker API).
2. Feature engineering.
3. Model ML (prediksi sinyal).
4. Rule layer (filter sinyal).
5. Eksekusi order otomatis.
6. Risk & position sizing.
7. Auto-retrain / self-improvement loop.

## Posisi dalam Quant Trading

Quant trading = keputusan trading dari model/aturan matematis yang dieksekusi sistematis, bukan penilaian manual trader. EA-DAYEN **menuju** quant trading penuh, tapi belum sampai di sana:

| Syarat | Status |
|---|---|
| Data sistematis (bukan baca chart manual) | Selesai |
| Fitur kuantitatif (indikator teknikal) | Selesai (baseline) |
| Model/aturan penghasil sinyal BUY/SELL/WAIT | Belum ada — "otak" sistem, prioritas berikutnya |
| Eksekusi otomatis dari sinyal | Infra siap (`BrokerAdapter`), belum ada pemanggil dari logika trading |
| Risk sizing dari rule matematis | Belum ada |

Sampai `model/` dan `rules/` menghasilkan sinyal nyata yang dipakai `execution/`, EA-DAYEN masih fase fondasi data — belum jadi sistem quant trading yang utuh.

## Kriteria Keluar Fase SHADOW (menuju LIVE)

Belum final, tapi arah kriterianya (detail angka menyusul setelah data & backtest cukup):

- Backtest out-of-sample (OOS) + holdout menunjukkan expectancy positif setelah biaya transaksi (spread/slippage/komisi) disertakan — bukan cuma gross profit.
- Shadow-trading (sinyal nyata, eksekusi bayangan) berjalan minimal beberapa minggu tanpa anomali (sinyal masuk akal, risk sizing benar, gak ada crash/silent failure).
- Max drawdown shadow dalam batas yang sudah ditetapkan `risk-management.md` sebelum shadow dimulai (bukan ditentukan setelah lihat hasil — mencegah bias "pindahin garis setelah tau skornya").
- Review manual sebelum switch `SHADOW` → `LIVE` (lihat `risk-management.md` § Gate SHADOW → LIVE) — tidak pernah otomatis.

## Status Implementasi

Lihat [`status.md`](status.md) untuk rincian per komponen — ringkasan per 2026-10-15:

- **Selesai**: data pipeline (bridge MT5↔Python, 8 simbol live), feature engineering baseline (SMA/EMA/RSI/ATR).
- **Belum ada**: model ML, rule layer, risk/position sizing, auto-retrain loop, pemanggil eksekusi dari logika trading nyata.
