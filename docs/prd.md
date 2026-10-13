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

## Status

Layer 1-7 belum ada — proyek baru di tahap dokumentasi dan scaffold.
