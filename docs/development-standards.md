# Standar Pengembangan

## Git

- Branch dari `main` terbaru.
- Penamaan: `feature/`, `bug/`, `hotfix/`, `docs/`, `refactor/`, `test/`, `ci/`, `chore/`.
- Commit message jelas dan deskriptif.

## Testing

- Non-trivial logic (feature engineering, risk calculation, sizing) wajib punya minimal 1 test/assert-check yang bisa dijalankan.
- Backtest wajib reproducible — seed random di-fix saat development.
- Konvensi nyata yang sudah dipakai: tiap modul `foo.py` punya `test_foo.py` sejajar, assert-based (bukan framework), dijalankan `python3 -m <package>.test_<module>` dari root repo. Lihat `core/test_decision_log.py`, `execution/test_shadow_guard.py`, `features/test_indicators.py` sebagai contoh.
- **Python 3.9 compatibility**: Mac ini pakai Python 3.9 (`python3 --version` buat cek). Sintaks union modern (`str | None`) butuh `from __future__ import annotations` di baris atas file — tanpa itu `ImportError` saat runtime (pernah kejadian di `data/store.py`, lihat riwayat commit). Cek dulu sebelum pakai sintaks tipe baru.

## Dependency Python

- Default: **stdlib only** — baru tambah dependency kalau beneran gak bisa (contoh: gradient boosting beneran butuh library, bukan cuma "lebih enak pakai library").
- Kalau butuh dependency: `.venv/` lokal (gitignored, jangan install ke Python sistem — campur antar project) + `requirements.txt` dicommit (`pip freeze`, bukan nulis manual).
- Setup di mesin baru: `python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt`. Jalankan modul lewat `./.venv/bin/python3 -m <package>.<module>`, bukan `python3` sistem.

## MQL5 (EA-DAYEN bridge)

- Edit `mql5/EADayenBridge.mq5` di repo ini — jangan edit langsung file di folder Experts MT5 (gampang lupa sync balik ke git).
- Compile lewat Wine CLI (otomatis, gak perlu buka MetaEditor) — command lengkap di `local-setup.md` § Compile Otomatis.
- Setelah compile, EA yang nempel di chart **gak otomatis reload** — wajib "Remove" lalu drag ulang dari Navigator supaya pakai `.ex5` terbaru.
- Scan compiler log pakai `iconv -f UTF-16LE -t UTF-8` — log MT5/MQL5 di Wine ini UTF-16, `grep` biasa gak bakal nemu apapun walau teksnya ada.

## Prinsip Kode

- Stdlib/library yang sudah dipakai dulu sebelum nambah dependency baru.
- Jangan nulis abstraksi (interface, factory, config) untuk kebutuhan yang belum ada.
- Kode eksekusi order dan risk management harus mudah dibaca — ini bagian paling kritis, hindari clever code.
