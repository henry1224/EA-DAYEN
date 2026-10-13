# Standar Pengembangan

## Git

- Branch dari `main` terbaru.
- Penamaan: `feature/`, `bug/`, `hotfix/`, `docs/`, `refactor/`, `test/`, `ci/`, `chore/`.
- Commit message jelas dan deskriptif.

## Testing

- Non-trivial logic (feature engineering, risk calculation, sizing) wajib punya minimal 1 test/assert-check yang bisa dijalankan.
- Backtest wajib reproducible — seed random di-fix saat development.

## Prinsip Kode

- Stdlib/library yang sudah dipakai dulu sebelum nambah dependency baru.
- Jangan nulis abstraksi (interface, factory, config) untuk kebutuhan yang belum ada.
- Kode eksekusi order dan risk management harus mudah dibaca — ini bagian paling kritis, hindari clever code.
