#property version   "1.01"

// EA-DAYEN execution bridge. Polls a folder (Common\Files\<BridgeFolder>) for plain-text
// command files written by the Python side, executes them against this MT5 account (real
// money if this account is live), and writes back a plain-text result file per command.
// Also writes a market-data snapshot so Python has price/candle data without any native
// MT5 API access (needed because the official Python `MetaTrader5` package only runs on
// Windows; this bridges MT5-on-Mac instead).
//
// File formats are documented in docs/bridge-protocol.md.
// Independent project from plutoo — do not reuse this EA's bridge folder for plutoo.

input string          BridgeFolder = "EA-DAYEN";
input string          TradeSymbol  = "EURUSD";
input ENUM_TIMEFRAMES Timeframe    = PERIOD_M5;
input int             CandleCount  = 50;
input int             PollSeconds  = 2;
input ulong           MagicNumber  = 20261014;

// Normalisasi supaya BridgeFolder boleh diisi pakai "/" atau "\\" -- keduanya jadi "\\".
string NormalizedBridgeFolder()
{
   string f = BridgeFolder;
   StringReplace(f, "/", "\\");
   return f;
}

string SnapshotPath() { return NormalizedBridgeFolder() + "\\snapshot.json"; }

int      effectivePollSeconds = 2;
datetime lastPoll             = 0;
bool     everWroteSnapshot    = false;
int      pollCount            = 0;

int OnInit()
{
   effectivePollSeconds = (int)MathMax(1, PollSeconds);

   if(!FolderCreate(NormalizedBridgeFolder(), FILE_COMMON))
   {
      int err = GetLastError();
      if(err != 4301) // ERR_DIRECTORY_NOT_EMPTY-ish "already exists" -- harmless, folder is there
         Print("EADAYEN_FOLDER_CREATE_WARN ", NormalizedBridgeFolder(), " err=", err);
   }

   if(!SymbolSelect(TradeSymbol, true))
      Print("EADAYEN_SYMBOL_SELECT_FAILED ", TradeSymbol, " err=", GetLastError());

   // EventSetTimer tetap dipasang (hemat CPU saat market sepi tick), tapi OnTick jadi
   // pemicu utama -- beberapa build Wine MT5 mengaku sukses EventSetTimer tanpa OnTimer
   // pernah benar-benar terpanggil (diverifikasi langsung 2026-10-14). OnTick dipicu tick
   // harga asli, bukan API timer Windows, jadi tetap jalan walau EventSetTimer cacat.
   EventSetTimer(effectivePollSeconds);

   Print("EADAYEN_INIT_OK symbol=", TradeSymbol, " folder=", NormalizedBridgeFolder(),
         " timeframe=", EnumToString(Timeframe), " pollSeconds=", effectivePollSeconds);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   Print("EADAYEN_DEINIT reason=", reason);
}

void OnTimer() { MaybePoll(); }
void OnTick()  { MaybePoll(); }

void MaybePoll()
{
   datetime now = TimeLocal();
   if(now - lastPoll < effectivePollSeconds) return;
   lastPoll = now;
   pollCount++;

   WriteSnapshot();
   ProcessPendingCommands();

   // Heartbeat ringan tiap ~30 detik, bukan tiap poll -- biar kelihatan hidup di panel
   // Experts tanpa membanjiri log. Dicetak terlepas dari sukses/gagal write.
   if(pollCount % MathMax(1, 30 / effectivePollSeconds) == 0)
      Print("EADAYEN_ALIVE poll#", pollCount, " everWrote=", everWroteSnapshot);
}

//--- Market data snapshot ---------------------------------------------------

void WriteSnapshot()
{
   MqlRates rates[];
   int copied = CopyRates(TradeSymbol, Timeframe, 0, CandleCount, rates);
   if(copied <= 0)
   {
      Print("EADAYEN_SNAPSHOT_NO_RATES ", TradeSymbol, " err=", GetLastError());
      return;
   }

   double bid = SymbolInfoDouble(TradeSymbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(TradeSymbol, SYMBOL_ASK);

   string json = "{";
   json += "\"symbol\":\"" + TradeSymbol + "\",";
   json += "\"time\":\"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\",";
   json += "\"bid\":" + DoubleToString(bid, 5) + ",";
   json += "\"ask\":" + DoubleToString(ask, 5) + ",";
   json += "\"candles\":[";
   for(int i = 0; i < copied; i++)
   {
      if(i > 0) json += ",";
      json += "{";
      json += "\"time\":\"" + TimeToString(rates[i].time, TIME_DATE|TIME_SECONDS) + "\",";
      json += "\"open\":" + DoubleToString(rates[i].open, 5) + ",";
      json += "\"high\":" + DoubleToString(rates[i].high, 5) + ",";
      json += "\"low\":" + DoubleToString(rates[i].low, 5) + ",";
      json += "\"close\":" + DoubleToString(rates[i].close, 5) + ",";
      json += "\"volume\":" + IntegerToString((long)rates[i].tick_volume);
      json += "}";
   }
   json += "]}";

   // Tulis langsung ke file final (FILE_WRITE menimpa isi lama) -- bukan tulis-ke-tmp-lalu-
   // FileMove seperti versi awal. FileMove di build Wine ini perilakunya gak pernah
   // terverifikasi benar (dicurigai salah satu sumber bug "EA gak pernah nulis apa-apa"
   // 2026-10-14), dan skenario pembaca baca file "robek" di tengah tulis itu risiko kecil
   // untuk use case ini (Python cuma baca snapshot harga terbaru, bukan data finansial
   // kritikal) -- lebih baik andal daripada atomic-tapi-gak-pernah-jalan.
   int handle = FileOpen(SnapshotPath(), FILE_WRITE|FILE_TXT|FILE_COMMON|FILE_ANSI);
   if(handle == INVALID_HANDLE)
   {
      Print("EADAYEN_SNAPSHOT_WRITE_FAILED ", SnapshotPath(), " err=", GetLastError());
      return;
   }
   FileWriteString(handle, json);
   FileClose(handle);

   if(!everWroteSnapshot)
   {
      everWroteSnapshot = true;
      Print("EADAYEN_READY first snapshot written -> ", SnapshotPath());
   }
}

//--- Command processing ------------------------------------------------------

void ProcessPendingCommands()
{
   string filename;
   string mask = NormalizedBridgeFolder() + "\\cmd_*.cmd";
   long handle = FileFindFirst(mask, filename, FILE_COMMON);
   if(handle == INVALID_HANDLE)
      return; // nothing pending

   do
   {
      ProcessOneCommand(filename);
   }
   while(FileFindNext(handle, filename));
   FileFindClose(handle);
}

void ProcessOneCommand(const string filename)
{
   string cmdId = filename;
   StringReplace(cmdId, "cmd_", "");
   StringReplace(cmdId, ".cmd", "");

   string donePath = NormalizedBridgeFolder() + "\\done_" + cmdId + ".cmd";
   if(FileIsExist(donePath, FILE_COMMON))
      return; // already processed — never redo a trade on a restart/race

   string body = ReadFile(NormalizedBridgeFolder() + "\\" + filename);
   string action = KvGet(body, "action");

   string result;
   if(action == "OPEN")
      result = ExecuteOpen(body);
   else if(action == "CLOSE")
      result = ExecuteClose(body);
   else
      result = "status=error\nmessage=unknown action '" + action + "'\n";

   Print("EADAYEN_COMMAND id=", cmdId, " action=", action, " result_first_line=", StringSubstr(result, 0, 40));
   WriteFile(donePath, result);
}

string ExecuteOpen(const string body)
{
   string symbol = KvGet(body, "symbol");
   string side   = KvGet(body, "side");
   double lot    = StringToDouble(KvGet(body, "lot"));
   double sl     = StringToDouble(KvGet(body, "sl"));
   double tp     = StringToDouble(KvGet(body, "tp"));

   if(symbol != TradeSymbol)
      return "status=error\nmessage=EA only trades " + TradeSymbol + "\n";
   if(side != "BUY" && side != "SELL")
      return "status=error\nmessage=side must be BUY or SELL, got '" + side + "'\n";
   if(lot <= 0.0)
      return "status=error\nmessage=lot must be > 0, got " + DoubleToString(lot, 2) + "\n";

   MqlTradeRequest request;
   MqlTradeResult  response;
   ZeroMemory(request);
   ZeroMemory(response);
   request.action       = TRADE_ACTION_DEAL;
   request.symbol       = symbol;
   request.volume       = lot;
   request.type         = (side == "BUY") ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   request.price        = (side == "BUY") ? SymbolInfoDouble(symbol, SYMBOL_ASK)
                                           : SymbolInfoDouble(symbol, SYMBOL_BID);
   request.sl           = sl;
   request.tp           = tp;
   request.magic        = MagicNumber;
   request.type_filling = ORDER_FILLING_IOC;

   if(!OrderSend(request, response) || response.retcode != TRADE_RETCODE_DONE)
      return "status=error\nmessage=OrderSend failed, retcode=" + IntegerToString(response.retcode) + "\n";

   return "status=ok\nticket=" + IntegerToString((long)response.order) + "\n";
}

string ExecuteClose(const string body)
{
   ulong ticket = (ulong)StringToInteger(KvGet(body, "ticket"));
   if(ticket == 0)
      return "status=error\nmessage=missing or invalid ticket\n";
   if(!PositionSelectByTicket(ticket))
      return "status=error\nmessage=position " + IntegerToString((long)ticket) + " not found\n";

   string symbol = PositionGetString(POSITION_SYMBOL);
   double volume = PositionGetDouble(POSITION_VOLUME);
   long   type   = PositionGetInteger(POSITION_TYPE);

   MqlTradeRequest request;
   MqlTradeResult  response;
   ZeroMemory(request);
   ZeroMemory(response);
   request.action       = TRADE_ACTION_DEAL;
   request.symbol       = symbol;
   request.volume       = volume;
   request.position     = ticket;
   request.type         = (type == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
   request.price        = (type == POSITION_TYPE_BUY) ? SymbolInfoDouble(symbol, SYMBOL_BID)
                                                       : SymbolInfoDouble(symbol, SYMBOL_ASK);
   request.magic        = MagicNumber;
   request.type_filling = ORDER_FILLING_IOC;

   if(!OrderSend(request, response) || response.retcode != TRADE_RETCODE_DONE)
      return "status=error\nmessage=close failed, retcode=" + IntegerToString(response.retcode) + "\n";

   return "status=ok\nticket=" + IntegerToString((long)ticket) + "\n";
}

//--- small file/kv helpers ---------------------------------------------------

string ReadFile(const string path)
{
   int handle = FileOpen(path, FILE_READ|FILE_TXT|FILE_COMMON|FILE_ANSI);
   if(handle == INVALID_HANDLE)
      return "";
   string content = "";
   while(!FileIsEnding(handle))
      content += FileReadString(handle) + "\n";
   FileClose(handle);
   return content;
}

void WriteFile(const string path, const string content)
{
   int handle = FileOpen(path, FILE_WRITE|FILE_TXT|FILE_COMMON|FILE_ANSI);
   if(handle == INVALID_HANDLE)
   {
      Print("EADAYEN_WRITE_FAILED ", path, " err=", GetLastError());
      return;
   }
   FileWriteString(handle, content);
   FileClose(handle);
}

string KvGet(const string body, const string key)
{
   string lines[];
   int n = StringSplit(body, '\n', lines);
   for(int i = 0; i < n; i++)
   {
      int pos = StringFind(lines[i], "=");
      if(pos <= 0) continue;
      string k = StringSubstr(lines[i], 0, pos);
      if(k == key)
         return StringSubstr(lines[i], pos + 1);
   }
   return "";
}
