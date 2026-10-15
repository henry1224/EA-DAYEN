# Dokumentasi EA-DAYEN

Index dokumen proyek. Baca sesuai urutan berikut saat onboarding.

0. [`status.md`](status.md) — dashboard: apa yang beneran jalan vs baru rencana, baca ini duluan.
1. [`prd.md`](prd.md) — tujuan, scope, bukan-tujuan, posisi dalam quant trading.
2. [`architecture.md`](architecture.md) — alur data → model → eksekusi → retrain, status tiap modul.
3. [`data-contracts.md`](data-contracts.md) — sumber data, format, skema raw & fitur.
4. [`ml-strategy.md`](ml-strategy.md) — fitur, model, validasi, kebijakan retrain.
5. [`risk-management.md`](risk-management.md) — sizing, SL/TP, drawdown limit, kill-switch.
6. [`development-standards.md`](development-standards.md) — branch, commit, testing.
7. [`bridge-protocol.md`](bridge-protocol.md) — format file MT5 ↔ Python.
8. [`local-setup.md`](local-setup.md) — setup spesifik Mac ini (path, cara compile, cara attach EA).

## Status

Lihat [`status.md`](status.md) untuk rincian. Ringkas: data pipeline & feature engineering baseline sudah jalan dan terverifikasi di akun demo real (Exness, 8 simbol); model/rule/risk/retrain belum ada.

## Catatan Independensi

EA-DAYEN **tidak berbagi kode maupun data** dengan proyek plutoo. Keputusan ini disengaja — lihat [`prd.md`](prd.md) § Mengapa Terpisah dari Plutoo.
