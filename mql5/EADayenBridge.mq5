#property version   "1.00"

// EA-DAYEN execution bridge. Polls a folder (Common\Files\<BridgeFolder>) for plain-text
// command files written by the Python side, executes them against this MT5 account (real
// money if this account is live), and writes back a plain-text result file per command.
// Also writes a market-data snapshot on every timer tick so Python has price/candle data
// without any native MT5 API access (needed because the official Python `MetaTrader5`
// package only runs on Windows; this bridges MT5-on-Mac instead).
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
string SnapshotTmp()  { return NormalizedBridgeFolder() + "\\snapshot.tmp"; }

int OnInit()
{
   if(!EventSetTimer(MathMax(1, PollSeconds)))
   {
      Print("EADAYEN_TIMER_FAILED");
      return INIT_FAILED;
   }
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
}

void OnTimer()
{
   WriteSnapshot();
   ProcessPendingCommands();
}

//--- Market data snapshot ---------------------------------------------------

void WriteSnapshot()
{
   MqlRates rates[];
   int copied = CopyRates(TradeSymbol, Timeframe, 0, CandleCount, rates);
   if(copied <= 0)
   {
      Print("EADAYEN_SNAPSHOT_NO_RATES ", TradeSymbol);
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

   int handle = FileOpen(SnapshotTmp(), FILE_WRITE|FILE_TXT|FILE_COMMON|FILE_ANSI);
   if(handle == INVALID_HANDLE)
   {
      Print("EADAYEN_SNAPSHOT_WRITE_FAILED ", GetLastError());
      return;
   }
   FileWriteString(handle, json);
   FileClose(handle);

   // Atomic-ish swap so Python never reads a half-written file.
   FileDelete(SnapshotPath(), FILE_COMMON);
   FileMove(SnapshotTmp(), FILE_COMMON, SnapshotPath(), FILE_COMMON);
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
      Print("EADAYEN_WRITE_FAILED ", path, " ", GetLastError());
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
