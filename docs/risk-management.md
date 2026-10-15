# Manajemen Risiko

## Position Sizing

Lot size dihitung dari persentase equity/balance, bukan nilai fixed — menyesuaikan modal yang berubah dan volatilitas instrumen.

**Formula kerangka** (angka `risk_pct` final menyusul setelah backtest, strukturnya sudah pasti):

```text
risk_amount  = equity * risk_pct          # risk_pct: persentase kecil, misal 0.5-1% (TBD final)
stop_distance = |entry_price - stop_loss_price|
pip_value     = nilai 1 pip untuk simbol & lot tsb (beda-beda per instrumen)
lot_size      = risk_amount / (stop_distance_pips * pip_value)
```

`atr_14` (dari `features/`) jadi kandidat dasar buat `stop_distance` otomatis (stop berbasis volatilitas, bukan angka pip fixed) — konsisten dengan prinsip sizing adaptif.

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

### Tingkatan Status Modal (rencana, belum diimplementasi)

Daripada biner "jalan/berhenti", status modal bertingkat — supaya respons terhadap kerugian proporsional, bukan lompat langsung ke halt total:

```text
NORMAL → CAUTION → REDUCED_RISK → HALT
```

- **NORMAL**: sizing & trading normal.
- **CAUTION**: drawdown mendekati batas (threshold final menyusul) — log peringatan, sizing tetap normal.
- **REDUCED_RISK**: drawdown lebih dalam — sizing dikecilkan otomatis (bukan berhenti total).
- **HALT**: max drawdown tersentuh — EA berhenti total, butuh intervensi manual (sesuai § Kill-Switch di atas).

Naik tingkat (ke arah lebih ketat) otomatis; turun tingkat (pulih ke NORMAL) butuh review manual — supaya gak langsung balik agresif begitu angka kebetulan membaik sebentar.

## Gate SHADOW → LIVE

EA selalu mulai di mode **SHADOW** (`execution/shadow_guard.py`): setiap order dicatat ke decision log tapi **tidak pernah** dikirim ke broker asli — strategi/ML/risk code tidak bisa melewati gate ini karena semuanya cuma kenal `BrokerAdapter`, bukan koneksi broker mentah. Pindah ke `LIVE` wajib manual (ubah config), tidak pernah otomatis dari hasil retrain atau performa bagus di SHADOW.

## Catatan

Detail angka (persentase risk per trade, max drawdown threshold) menyusul setelah backtest awal.
