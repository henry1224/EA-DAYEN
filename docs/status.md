---
last_updated: 2026-10-15
---

# Status Implementasi

Dashboard ringkas — bukan proses approval berlapis kayak plutoo (proyek solo, gak perlu), cuma biar gampang lihat apa yang beneran jalan vs baru rencana. "Selesai" berarti ada kode + self-check lolos + (kalau relevan) terverifikasi jalan di data/akun real — bukan cuma "sudah ditulis".

## Ringkasan

| Layer | Status | Evidence |
|---|---|---|
| 1. Data pipeline | ✅ Selesai | `data/store.py`, `data/poll_bridge.py`, 8 simbol live sejak 2026-10-15 |
| 2. Feature engineering | 🟡 Baseline selesai | `features/indicators.py` (SMA/EMA/RSI/ATR), self-check lolos, jalan di data real XAUUSD |
| 3. Model ML | 🟡 Baseline kode siap, belum dilatih di data real | `model/baseline.py` (GradientBoostingClassifier, scikit-learn), self-check lolos — **belum pernah dilatih**, `data_store/` gak ada di mesin ini (lihat Insiden) |
| 4. Rule layer | ❌ Belum mulai | — |
| 5. Eksekusi order otomatis | 🟡 Infra siap, belum dipakai | `execution/broker_base.py`, `execution/file_bridge_adapter.py` — belum ada pemanggil dari logika trading nyata |
| 6. Risk & position sizing | ❌ Belum mulai (kerangka formula ada di `risk-management.md`) | — |
| 7. Auto-retrain loop | ❌ Belum mulai | — |

## Infrastruktur Pendukung

| Komponen | Status | Evidence |
|---|---|---|
| Bridge MT5 ↔ Python | ✅ Selesai | `mql5/EADayenBridge.mq5` v1.01, 8 simbol live, lihat `local-setup.md` |
| Decision log immutable | ✅ Selesai | `core/decision_log.py`, self-check lolos |
| Gate SHADOW → LIVE | ✅ Selesai | `execution/shadow_guard.py`, self-check lolos (belum pernah dites di alur trading nyata karena belum ada sinyal) |
| Repo + CI manual | ✅ Selesai | [github.com/henry1224/EA-DAYEN](https://github.com/henry1224/EA-DAYEN), self-check dijalankan manual tiap perubahan (belum ada CI otomatis — belum perlu di skala ini) |
| Dashboard status data (lokal) | ✅ Selesai | `data/status.py` → `data_store/status.html`, auto-refresh, file lokal murni |

## Insiden & Pelajaran (ringkas)

- **2026-10-14/15**: `OnTimer` MQL5 gak pernah terpanggil di build Wine MT5 Mac ini meski `EventSetTimer` klaim sukses. Fix: `OnTick` jadi pemicu utama. Detail: `bridge-protocol.md` § Perubahan v1.01.
- **2026-10-14/15**: Salah cek folder Wine user (`henrywilliam` vs `user` sebenarnya) — berjam-jam debug salah arah. Detail: `local-setup.md` § Koreksi Path.
- **2026-10-15**: `data_store/` sempat gak sengaja ke-commit ke git — sudah di-gitignore dan dikeluarkan dari tracking.
- **2026-10-15**: Poller crash kalau baca `snapshot.json` pas lagi ditimpa EA (race condition, `FileOpen(FILE_WRITE)` truncate dulu baru tulis) — fix: retry baca di `file_bridge_adapter.py`.
- **2026-10-15**: Threshold "stale" di dashboard (60 detik) salah — raw CSV cuma update pas candle beneran tutup (~5 menit buat M5), bukan tiap poll. Bikin alarm palsu. Fix: threshold berbasis timeframe.
- **2026-10-15**: Repo di-clone ulang di mesin ini (Mac lain/sesi baru) — `data_store/` **gak ada sama sekali** (gitignored, gak ikut clone, dan poller belum pernah dijalankan di mesin ini). Klaim "8 simbol live" di atas berlaku buat mesin yang jalanin poller, bukan otomatis berlaku di mesin lain manapun repo ini di-clone — cek `ps aux | grep poll_bridge` dan `ls data_store/` sebelum asumsi data ada.

## Berikutnya (urutan disarankan, bukan jadwal pasti)

1. **Jalankan `data/poll_bridge.py` di mesin yang ada MT5+EA attached** (lihat `local-setup.md`) — mesin ini belum punya `data_store/` sama sekali, jadi belum ada apapun buat dilatih.
2. Biarkan poller jalan beberapa hari — kumpulkan histori cukup buat training & backtest yang bermakna.
3. Latih `model/baseline.py` di data real (`python3 -m model.baseline --symbol <SIMBOL> --timeframe M5`) + protokol backtest (manifest hash, time-split — terdokumentasi di `ml-strategy.md`, belum diimplementasi).
5. Bangun `rules/` (filter sinyal ML).
6. Bangun `risk/` (position sizing dari formula di `risk-management.md`).
7. Sambungkan semuanya ke `execution/` lewat `ShadowGuard` — mulai SHADOW, bukan LIVE.
8. **Tambah panel posisi/order terbuka ke dashboard** — ditunda sampai poin 7 jalan (sebelum itu gak ada order dari sistem buat ditampilkan). Perlu perluas bridge (snapshot akun + posisi), bukan cuma data harga.
9. Evaluasi hasil SHADOW terhadap kriteria di `prd.md` § Kriteria Keluar Fase SHADOW sebelum pertimbangkan LIVE.
