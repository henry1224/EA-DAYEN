# Protokol File-Bridge (MT5 ↔ Python)

Kontrak file antara `mql5/EADayenBridge.mq5` (jalan di MT5 app) dan `execution/file_bridge_adapter.py` (jalan di Python). Semua file ada di satu folder bersama: `Common\Files\EA-DAYEN\` (folder Common MT5, bukan folder data per-terminal — supaya tetap sama walau ganti/reinstall terminal).

## snapshot.json

Ditulis EA tiap `PollSeconds` detik (timpa file, bukan append). Dibaca Python kapan saja.

```json
{
  "symbol": "EURUSD",
  "time": "2026.10.14 08:00:00",
  "bid": 1.09501,
  "ask": 1.09515,
  "candles": [
    {"time": "2026.10.14 07:55:00", "open": 1.0950, "high": 1.0952, "low": 1.0948, "close": 1.0951, "volume": 120}
  ]
}
```

## cmd_<id>.cmd (ditulis Python, dibaca EA)

Key=value, satu baris per key. `<id>` unik per command (timestamp + random suffix).

OPEN:
```
id=1697000000123-ab12cd
action=OPEN
symbol=EURUSD
side=BUY
lot=0.10
sl=1.0950
tp=1.1050
```

CLOSE:
```
id=1697000000124-ef34gh
action=CLOSE
ticket=123456789
```

## done_<id>.cmd (ditulis EA, dibaca Python)

```
status=ok
ticket=123456789
```
atau
```
status=error
message=OrderSend failed, retcode=10016
```

## Aturan

- EA tidak pernah proses ulang `cmd_<id>.cmd` kalau `done_<id>.cmd` sudah ada — aman dari restart/race, mencegah order dobel.
- Python tunggu (`poll_interval`) sampai `done_<id>.cmd` muncul, timeout kalau EA tidak jalan/respon.
- File lama (`cmd_*`/`done_*`) tidak dihapus otomatis — bersihkan manual/berkala kalau folder makin penuh (volume rendah, belum jadi masalah di tahap ini).

## Catatan Waktu (Penting)

Format `time` persis output `TimeToString(TIME_DATE|TIME_SECONDS)` MQL5: `yyyy.mm.dd hh:mi:ss` (titik, bukan dash/ISO-8601). Ini **waktu server broker Exness, BELUM terverifikasi UTC** — offset server berbeda-beda per broker dan belum dicek. Simpan apa adanya dulu; jangan asumsikan UTC sampai offset server dikonfirmasi (lihat `docs/data-contracts.md` § Catatan Waktu).
