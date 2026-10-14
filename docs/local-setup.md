# Setup Lokal (Mac Ini)

Catatan operasional — path spesifik ke instalasi MT5 di Mac ini (beda dari dokumen lain yang generik).

## Lokasi MT5

MT5 di Mac ini terpasang sebagai app Wine-wrapped (`/Applications/MetaTrader 5.app`), portable mode:

```text
Experts    : ~/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5/MQL5/Experts/EA-DAYEN/
Common Files: ~/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/users/henrywilliam/AppData/Roaming/MetaQuotes/Terminal/Common/Files/EA-DAYEN/
```

`EADayenBridge.mq5` sudah disalin ke folder Experts di atas. Folder bridge per simbol di Common Files sudah dibuat.

## Konvensi Multi-Simbol

Satu file EA (`EADayenBridge.mq5`), di-attach berkali-kali — satu kali per chart/simbol — dengan input `BridgeFolder` berbeda per simbol supaya snapshot/command gak tabrakan:

| Simbol | Input `BridgeFolder` | Input `TradeSymbol` |
|---|---|---|
| XAUUSD | `EA-DAYEN/XAUUSD` | `XAUUSD` |
| EURUSD | `EA-DAYEN/EURUSD` | `EURUSD` |
| GBPUSD | `EA-DAYEN/GBPUSD` | `GBPUSD` |
| USDJPY | `EA-DAYEN/USDJPY` | `USDJPY` |
| USDCHF | `EA-DAYEN/USDCHF` | `USDCHF` |
| AUDUSD | `EA-DAYEN/AUDUSD` | `AUDUSD` |
| USDCAD | `EA-DAYEN/USDCAD` | `USDCAD` |
| NZDUSD | `EA-DAYEN/NZDUSD` | `NZDUSD` |

`Timeframe` dan `MagicNumber` boleh sama di semua instance (default EA: M5, 20261014) — isolasi sudah terjamin lewat `BridgeFolder` yang berbeda, bukan lewat magic number.

## Langkah Manual (Tidak Bisa Diotomasi)

Dua langkah ini wajib manual di GUI MT5 — bukan keterbatasan skrip, tapi memang disengaja oleh MT5 sendiri (konfirmasi algo-trading tidak bisa dilewati lewat script, demi keamanan akun real):

1. **Compile sekali**: buka MetaEditor (Tools → MetaQuotes Language Editor, atau `F4` dari terminal), buka `EADayenBridge.mq5`, tekan `F7` (Compile). Cukup sekali — berlaku buat semua 8 instance.
2. **Attach ke tiap chart** (8x, satu per simbol): buka chart simbolnya → drag EA dari Navigator ke chart → tab "Inputs" → isi `BridgeFolder` dan `TradeSymbol` sesuai tabel di atas → centang "Allow Algo Trading" → OK.

## Jalankan Data Poller (satu proses per simbol)

```bash
COMMON="$HOME/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/users/henrywilliam/AppData/Roaming/MetaQuotes/Terminal/Common/Files/EA-DAYEN"

for SYM in XAUUSD EURUSD GBPUSD USDJPY USDCHF AUDUSD USDCAD NZDUSD; do
  python3 -m data.poll_bridge --bridge-dir "$COMMON/$SYM" --symbol "$SYM" --timeframe M5 &
done
```

(`&` jalan di background; `jobs` buat lihat daftar proses, `kill %1` dst buat stop satu-satu, atau `kill $(jobs -p)` buat stop semua.)
