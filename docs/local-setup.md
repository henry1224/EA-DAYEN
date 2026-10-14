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

1. ~~Compile manual~~ — **sudah diotomasi**, lihat § Compile Otomatis di bawah. Jalankan ulang tiap habis edit `mql5/EADayenBridge.mq5`.
2. **Attach ke tiap chart** (8x, satu per simbol): buka chart simbolnya → drag EA dari Navigator ke chart → tab "Inputs" → isi `BridgeFolder` dan `TradeSymbol` sesuai tabel di atas → centang "Allow Algo Trading" → OK.

## Jalankan Data Poller (satu proses per simbol)

```bash
COMMON="$HOME/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/users/henrywilliam/AppData/Roaming/MetaQuotes/Terminal/Common/Files/EA-DAYEN"

for SYM in XAUUSD EURUSD GBPUSD USDJPY USDCHF AUDUSD USDCAD NZDUSD; do
  python3 -m data.poll_bridge --bridge-dir "$COMMON/$SYM" --symbol "$SYM" --timeframe M5 &
done
```

(`&` jalan di background; `jobs` buat lihat daftar proses, `kill %1` dst buat stop satu-satu, atau `kill $(jobs -p)` buat stop semua.)


## Compile Otomatis

MT5 Mac app membungkus Wine asli (`Contents/SharedSupport/wine`) — MetaEditor punya flag CLI `/compile`, jadi bisa dipanggil tanpa buka GUI:

```bash
export WINEPREFIX="$HOME/Library/Application Support/net.metaquotes.wine.metatrader5"
WINE="/Applications/MetaTrader 5.app/Contents/SharedSupport/wine/bin/wine"
cd "$WINEPREFIX/drive_c/Program Files/MetaTrader 5"

"$WINE" "MetaEditor64.exe" "/compile:MQL5\Experts\EA-DAYEN\EADayenBridge.mq5" &
PID=$!
for i in $(seq 1 15); do kill -0 "$PID" 2>/dev/null || break; sleep 1; done
kill -9 "$PID" 2>/dev/null  # jaga-jaga kalau nyangkut

ls "MQL5/Experts/EA-DAYEN/EADayenBridge.ex5"  # ada = sukses
```

Terverifikasi jalan di Mac ini (2026-10-14) — `.ex5` kebuat dalam ~3 detik, gak perlu buka GUI MetaEditor sama sekali.

## Kenapa "Attach ke Chart" Tetap Manual

MT5 punya fitur command-line `/config:file.ini` buat auto-attach **1 EA ke 1 chart** saat terminal baru nyala — tapi gak cocok buat 8 simbol sekaligus: tiap invocation `terminal64.exe` = 1 sesi login baru ke akun yang sama, dan Exness (seperti kebanyakan broker) **nolak/nendang sesi lama kalau akun yang sama login dobel**. Nyalain 8x berturut-turut bukan nambah 8 chart di 1 terminal — malah bikin terminal saling nendang satu sama lain.

Alternatif lain (manipulasi file "profile" MT5 buat simulasikan 8 chart+EA sekaligus) formatnya **sebagian biner, gak didokumentasikan resmi** — coba utak-atik itu berisiko bikin terminal gagal buka/corrupt profile, pada terminal yang sama sedang terhubung ke akun (walau demo). Risikonya lebih besar dari manfaatnya dibanding drag EA manual 8x (~2 menit kerja).

**Catatan baik:** log terminal konfirmasi akun yang terhubung sekarang server `Exness-MT5Trial8` — **demo**, bukan akun real. Aman buat eksperimen di tahap ini.
