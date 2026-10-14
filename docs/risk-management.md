# Manajemen Risiko

## Position Sizing

Lot size dihitung dari persentase equity/balance, bukan nilai fixed — menyesuaikan modal yang berubah dan volatilitas instrumen.

## Stop Loss / Take Profit

Setiap order wajib punya SL. TP opsional (bisa trailing stop sebagai alternatif).

## Limit

- Max drawdown harian/bulanan — EA berhenti trading otomatis kalau tersentuh (kill-switch).
- Max posisi terbuka bersamaan.
- Max risk per trade (persentase kecil dari equity, bukan nilai besar).

## Kill-Switch

Kondisi yang memaksa EA berhenti total (butuh intervensi manual untuk restart):
- Max drawdown tersentuh.
- Error beruntun dari broker API (koneksi putus, order gagal berulang).
- Model retrain gagal validasi (model baru tidak lebih baik dari model aktif — jangan promosikan).

## Gate SHADOW → LIVE

EA selalu mulai di mode **SHADOW** (`execution/shadow_guard.py`): setiap order dicatat ke decision log tapi **tidak pernah** dikirim ke broker asli — strategi/ML/risk code tidak bisa melewati gate ini karena semuanya cuma kenal `BrokerAdapter`, bukan koneksi broker mentah. Pindah ke `LIVE` wajib manual (ubah config), tidak pernah otomatis dari hasil retrain atau performa bagus di SHADOW.

## Catatan

Detail angka (persentase risk per trade, max drawdown threshold) menyusul setelah backtest awal.
