# EA-DAYEN

Expert Advisor otomatis (ML + rule-based + auto-retrain) untuk forex major pairs. Eksekusi real lewat akun Exness (MT5), jalan native di Mac dulu lewat file-bridge, pindah ke Windows/VPS nanti dengan API native.

Dokumentasi lengkap: [`docs/README.md`](docs/README.md).

## Struktur

- `mql5/` — EA MQL5 (bridge eksekusi + data, jalan di MT5 app).
- `execution/` — `BrokerAdapter` + implementasi file-bridge (Python).

## Self-check

Tidak butuh dependency luar (stdlib saja). Jalankan dari root repo:

```bash
python3 -m execution.test_file_bridge_adapter
```
