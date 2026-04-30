"""
Beta local — Trading cockpit completo.
python beta_local.py → http://localhost:8000/dashboard
"""
import json, os, sys, webbrowser, threading, time, random
from pathlib import Path
from datetime import datetime, timezone
from collections import deque

def install_if_missing():
    import importlib.util
    needed = {"fastapi":"fastapi","uvicorn":"uvicorn[standard]",
              "pydantic":"pydantic","requests":"requests","pytz":"pytz",
              "yfinance":"yfinance"}
    missing=[pkg for mod,pkg in needed.items() if importlib.util.find_spec(mod) is None]
    if missing:
        print(f"Installing: {', '.join(missing)}")
        import subprocess
        subprocess.check_call([sys.executable,"-m","pip","install",*missing,"-q"])
        os.execv(sys.executable,[sys.executable]+sys.argv)

install_if_missing()

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn, pytz

# ── State ─────────────────────────────────────────────────────────────────────
SIGNALS_QUEUE: deque = deque(maxlen=100)
TRADES_LOG: list     = []
EQUITY_CURVE: list   = []
LOG_FILE = Path("trades.jsonl")

ACCOUNT = {"balance":50_000.0,"start":50_000.0,"peak":50_000.0}

ACTIVE_POSITION: dict = {}   # {} = flat; else {symbol,action,qty,entry,sl,tp,open_pnl}

DAILY_BIAS = {"value": "NEUTRAL"}  # BULLISH | NEUTRAL | BEARISH — set from UI

CONFIG = {
    "MAX_RISK_PCT":          0.01,
    "MIN_RR":                2.0,
    "STOP_TICKS":            10,
    "STOP_PCT":              0.5,
    "MAX_TRADES_SESSION":    2,
    "MAX_DAILY_LOSS_PCT":    0.03,
    "WIN_PROB":              0.60,   # simulation win probability
}

# Upcoming high-impact news (static schedule — real app uses ForexFactory)
NEWS_SCHEDULE = [
    {"name":"NFP",  "day":"first_friday", "hour":8,"min":30,"impact":"HIGH"},
    {"name":"CPI",  "day":"variable",     "hour":8,"min":30,"impact":"HIGH"},
    {"name":"FOMC", "day":"variable",     "hour":14,"min":0, "impact":"HIGH"},
]

def _ts():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]+"Z"

def log_event(event:str, data:dict):
    rec={"ts":_ts(),"event":event,**data}
    TRADES_LOG.append(rec)
    with open(LOG_FILE,"a",encoding="utf-8") as f:
        f.write(json.dumps(rec)+"\n")
    return rec

def push_equity():
    ACCOUNT["peak"]=max(ACCOUNT["peak"],ACCOUNT["balance"])
    dd=(ACCOUNT["peak"]-ACCOUNT["balance"])/ACCOUNT["peak"]*100
    EQUITY_CURVE.append({"ts":_ts(),"balance":round(ACCOUNT["balance"],2),"dd":round(dd,2)})

# ── Kill zone ─────────────────────────────────────────────────────────────────
NY=pytz.timezone("America/New_York")

def _now_ny(): return datetime.now(NY)

def kz_status()->dict:
    """
    Kill zones (TJR/ICT NY session):
      Window A — NY Open:      8:30–9:00 ET  (máxima liquidez, movimientos explosivos)
      Window B — Mid-morning: 9:30–10:30 ET  (NYSE open, continuación de sesión)
      Silver Bullet:          10:00–11:00 ET  (setup específico TJR Day-34)
    El scanner solo opera dentro de estas ventanas.
    """
    import datetime as dt
    ny=_now_ny()
    t=ny.time()
    wd=ny.weekday()

    win_a = dt.time(8,30)<=t<=dt.time(9,0)
    win_b = dt.time(9,30)<=t<=dt.time(10,30)
    sb    = dt.time(10,0)<=t<=dt.time(11,0)
    active= wd<5 and (win_a or win_b or sb)

    if active:
        if win_a: zone_name="NY Open (A)"
        elif sb:  zone_name="Silver Bullet"
        else:     zone_name="Mid-Morning (B)"
        # Next close
        if t<dt.time(9,0):   next_event=f"Ventana A cierra en {int((dt.time(9,0).hour*60+dt.time(9,0).minute)-(t.hour*60+t.minute))}m"
        elif t<dt.time(10,30): next_event=f"Ventana B cierra en {int((dt.time(10,30).hour*60+dt.time(10,30).minute)-(t.hour*60+t.minute))}m"
        else:                next_event=f"Silver Bullet cierra en {int((11*60)-(t.hour*60+t.minute))}m"
        nxt=next_event
    elif wd>=5:
        nxt="Abre el lunes 8:30 ET"; zone_name="Weekend"
    elif t<dt.time(8,30):
        mins=int((8*60+30)-(t.hour*60+t.minute))
        nxt=f"Ventana A abre en {mins}m (8:30 ET)"; zone_name="Pre-KZ"
    elif dt.time(9,0)<t<dt.time(9,30):
        nxt="Ventana B abre en {}m (9:30 ET)".format(int((9*60+30)-(t.hour*60+t.minute))); zone_name="Gap A→B"
    else:
        nxt="Abre mañana 8:30 ET"; zone_name="Post-KZ"

    return {
        "active":active,"silver_bullet":sb,
        "window_a":win_a,"window_b":win_b,
        "zone_name":zone_name if active else zone_name,
        "et":ny.strftime("%H:%M:%S"),"day":ny.strftime("%A"),"next":nxt
    }

def next_news()->dict|None:
    ny=_now_ny()
    # NFP: first Friday
    if ny.weekday()==4 and ny.day<=7:
        event_t=ny.replace(hour=8,minute=30,second=0,microsecond=0)
        delta=(event_t-ny).total_seconds()/60
        if -15<=delta<=240:
            return {"name":"NFP","mins":int(delta),"blackout":abs(delta)<=15}
    return None

# ── Simulated executor ────────────────────────────────────────────────────────
def simulated_executor():
    session_count=0
    session_date=None

    while True:
        time.sleep(0.3)
        if not SIGNALS_QUEUE: continue
        signal=SIGNALS_QUEUE.popleft()

        ny=_now_ny(); today=ny.date()
        if session_date!=today:
            session_date=today; session_count=0

        kz=kz_status()
        if not kz["active"]:
            log_event("skip",{"reason":f"Fuera de kill zone — {kz['next']}","signal":signal}); continue

        if DAILY_BIAS["value"]=="NEUTRAL":
            log_event("skip",{"reason":"Daily Bias NEUTRAL — no operar hoy","signal":signal}); continue

        bias=DAILY_BIAS["value"]
        action=signal["action"]
        if (action=="BUY" and bias=="BEARISH") or (action=="SELL" and bias=="BULLISH"):
            log_event("skip",{"reason":f"Señal {action} contra bias {bias}","signal":signal}); continue

        if session_count>=CONFIG["MAX_TRADES_SESSION"]:
            log_event("skip",{"reason":f"Max {CONFIG['MAX_TRADES_SESSION']} trades/sesión alcanzado","signal":signal}); continue

        news=next_news()
        if news and news["blackout"]:
            log_event("skip",{"reason":f"Blackout noticias: {news['name']} en {news['mins']}m","signal":signal}); continue

        # Sizing
        entry=signal["close"]; act=signal["action"]
        sd=entry*CONFIG["STOP_PCT"]/100
        rr=CONFIG["MIN_RR"]
        sl=round(entry-sd,4) if act=="BUY" else round(entry+sd,4)
        tp=round(entry+sd*rr,4) if act=="BUY" else round(entry-sd*rr,4)
        qty=max(1,int(ACCOUNT["balance"]*CONFIG["MAX_RISK_PCT"]/(sd or 1)))

        ACTIVE_POSITION.update({"symbol":signal["symbol"],"action":act,"qty":qty,
                                 "entry":entry,"sl":sl,"tp":tp,"open_pnl":0.0,
                                 "ts":_ts()})
        session_count+=1
        log_event("order_placed",{"symbol":signal["symbol"],"action":act,"qty":qty,
            "entry":entry,"sl":sl,"tp":tp,"rr":rr,
            "risk_usd":round(ACCOUNT["balance"]*CONFIG["MAX_RISK_PCT"],2),
            "reason":signal.get("reason",""),"bias":bias,"kz_silver":kz["silver_bullet"]})
        print(f"  [ORDER] {act} {qty}x {signal['symbol']} @ {entry} SL {sl} TP {tp}")

        # Simulate fill
        hold=random.uniform(2,8)
        for _ in range(int(hold*2)):
            time.sleep(0.5)
            drift=random.uniform(-sd*0.5,sd*0.5)
            cur=entry+(drift if act=="BUY" else -drift)
            ACTIVE_POSITION["open_pnl"]=round((cur-entry)*qty if act=="BUY" else (entry-cur)*qty,2)

        ACTIVE_POSITION.clear()
        win=random.random()<CONFIG["WIN_PROB"]
        pnl=round(sd*qty*rr if win else -sd*qty,2)
        ACCOUNT["balance"]+=pnl
        push_equity()
        rr_got=rr if win else round(random.uniform(0.2,0.9),1)
        log_event("trade_closed",{"symbol":signal["symbol"],"pnl":pnl,"rr_achieved":rr_got,
            "result":"WIN" if win else "LOSS","balance_after":round(ACCOUNT["balance"],2)})
        print(f"  [{'WIN ' if win else 'LOSS'}] {signal['symbol']} ${pnl:+.2f} bal ${ACCOUNT['balance']:,.0f}")

# ── IFVG Detector (autonomous signal generation) ─────────────────────────────
# Runs every ~60s in background. Downloads 5m bars from Yahoo Finance,
# detects IFVGs in Python (same logic as Pine Script), auto-queues signals.
# User only needs to set Daily Bias once in the morning.

DETECTOR_STATE = {
    "last_run": None,       # datetime of last scan
    "last_candle": None,    # last bar timestamp processed (avoid duplicates)
    "signals_today": 0,
    "status": "idle",       # idle | scanning | paused
    "last_signal": None,
    "enabled": True,
}

YF_SYMBOLS_DETECT = {"NQ1!":"^NDX","ES1!":"^GSPC","AAPL":"AAPL","MSFT":"MSFT"}
WATCH_SYMBOLS = ["NQ1!"]   # symbols to watch (configurable from UI)

def detect_ifvg(candles: list) -> list:
    """
    True 3-stage IFVG detection (ICT/TJR methodology):

    Stage 1 — FVG creation: 3-candle imbalance (gap between c[i-2].high and c[i].low)
    Stage 2 — Violation/Inversion: price CLOSES completely through the FVG
               Bull FVG violated → close < fvg.bot → zone becomes RESISTANCE (IFVG bearish)
               Bear FVG violated → close > fvg.top → zone becomes SUPPORT (IFVG bullish)
    Stage 3 — Retest: price pulls back INTO the inverted zone → SIGNAL

    This is what separates a real IFVG from a simple FVG that price touched.
    """
    signals = []
    if len(candles) < 10:
        return signals

    ZONE_LOOKBACK = 40   # bars before a zone expires

    # Active FVGs (not yet violated)
    bull_fvgs = []   # [{top, bot, bar}]  → candidate for bearish IFVG
    bear_fvgs = []   # [{top, bot, bar}]  → candidate for bullish IFVG

    # Inverted zones (IFVGs) waiting for retest
    ifvg_zones = []  # [{top, bot, type:'sell'/'buy', bar_inv}]

    for i in range(2, len(candles)):
        c0 = candles[i]
        c2 = candles[i-2]

        # ── Stage 1: detect new FVGs ──────────────────────────────────────
        if c2["high"] < c0["low"]:          # Bullish FVG
            bull_fvgs.append({"top": c0["low"], "bot": c2["high"], "bar": i})

        if c2["low"] > c0["high"]:          # Bearish FVG
            bear_fvgs.append({"top": c2["low"], "bot": c0["high"], "bar": i})

        # Expire old zones
        bull_fvgs  = [f for f in bull_fvgs  if i - f["bar"] <= ZONE_LOOKBACK]
        bear_fvgs  = [f for f in bear_fvgs  if i - f["bar"] <= ZONE_LOOKBACK]
        ifvg_zones = [z for z in ifvg_zones if i - z["bar_inv"] <= ZONE_LOOKBACK]

        # ── Stage 2: detect violations → create IFVG zones ────────────────
        for fvg in bull_fvgs[:]:
            if i - fvg["bar"] < 1:  # need at least 1 bar after creation
                continue
            # Violation: close BELOW bottom of bullish FVG
            if c0["close"] < fvg["bot"]:
                ifvg_zones.append({
                    "top": fvg["top"], "bot": fvg["bot"],
                    "type": "sell",   # inverted bull FVG → resistance → SELL on retest
                    "bar_inv": i,
                    "desc": f"bull FVG [{fvg['bot']:.0f}-{fvg['top']:.0f}] invertido"
                })
                bull_fvgs.remove(fvg)

        for fvg in bear_fvgs[:]:
            if i - fvg["bar"] < 1:
                continue
            # Violation: close ABOVE top of bearish FVG
            if c0["close"] > fvg["top"]:
                ifvg_zones.append({
                    "top": fvg["top"], "bot": fvg["bot"],
                    "type": "buy",    # inverted bear FVG → support → BUY on retest
                    "bar_inv": i,
                    "desc": f"bear FVG [{fvg['bot']:.0f}-{fvg['top']:.0f}] invertido"
                })
                bear_fvgs.remove(fvg)

        # ── Stage 3: retest → signal ───────────────────────────────────────
        for zone in ifvg_zones[:]:
            if i - zone["bar_inv"] < 1:   # at least 1 bar after inversion
                continue

            if zone["type"] == "sell":
                # Bearish IFVG: price retests zone → SELL
                # Price must have come from BELOW and entered the zone
                if zone["bot"] <= c0["close"] <= zone["top"]:
                    signals.append({
                        "action": "SELL",
                        "close":  c0["close"],
                        "reason": f"IFVG SELL — {zone['desc']} → resistencia confirmada",
                        "bar_index": i,
                        "fvg_bot": zone["bot"], "fvg_top": zone["top"],
                    })
                    ifvg_zones.remove(zone)

            elif zone["type"] == "buy":
                # Bullish IFVG: price retests zone → BUY
                if zone["bot"] <= c0["close"] <= zone["top"]:
                    signals.append({
                        "action": "BUY",
                        "close":  c0["close"],
                        "reason": f"IFVG BUY — {zone['desc']} → soporte confirmado",
                        "bar_index": i,
                        "fvg_bot": zone["bot"], "fvg_top": zone["top"],
                    })
                    ifvg_zones.remove(zone)

    return signals


# ── Weekly/Daily/4H Bias Analyzer ─────────────────────────────────────────────
BIAS_CACHE = {"result": None, "ts": None}  # cache for 30 min

def analyze_bias(yf_sym: str = "^NDX") -> dict:
    """
    Top-down structural analysis: Weekly → Daily → 4H.
    Returns suggested bias (BULLISH/BEARISH/NEUTRAL) with score + reasoning.
    Score: +N = bullish evidence, -N = bearish evidence, threshold ±3 for bias.
    """
    import yfinance as yf
    score = 0
    signals = []

    try:
        # ── Weekly: is price expanding in bullish or bearish direction? ──
        wk = yf.Ticker(yf_sym).history(period="3mo", interval="1wk", auto_adjust=True)
        if len(wk) >= 3:
            pw  = wk.iloc[-2]   # previous week (fully closed)
            cw  = wk.iloc[-1]   # current week
            ppw = wk.iloc[-3]   # 2 weeks ago
            pdh, pdl = float(pw["High"]), float(pw["Low"])
            pdc = float(pw["Close"])
            cp  = float(cw["Close"])

            if cp > pdh:
                score += 2; signals.append(f"W: precio sobre máx semana previa ({pdh:.0f}) +2")
            elif cp < pdl:
                score -= 2; signals.append(f"W: precio bajo mín semana previa ({pdl:.0f}) -2")
            elif cp > pdc:
                score += 1; signals.append(f"W: cierre semanal por encima PDC ({pdc:.0f}) +1")
            else:
                score -= 1; signals.append(f"W: cierre semanal bajo PDC ({pdc:.0f}) -1")

            # Weekly HH/HL or LH/LL
            if float(pw["High"]) > float(ppw["High"]) and float(pw["Low"]) > float(ppw["Low"]):
                score += 1; signals.append("W: HH+HL semanal (tendencia alcista) +1")
            elif float(pw["High"]) < float(ppw["High"]) and float(pw["Low"]) < float(ppw["Low"]):
                score -= 1; signals.append("W: LH+LL semanal (tendencia bajista) -1")

    except Exception as e:
        signals.append(f"W: error ({e})")

    try:
        # ── Daily: PDH, PDL, premium/discount ──
        dy = yf.Ticker(yf_sym).history(period="10d", interval="1d", auto_adjust=True)
        if len(dy) >= 3:
            yd   = dy.iloc[-2]   # yesterday (fully closed)
            td   = dy.iloc[-1]   # today so far
            pdh  = float(yd["High"])
            pdl  = float(yd["Low"])
            pdc  = float(yd["Close"])
            cp   = float(td["Close"])
            mid  = (pdh + pdl) / 2  # equilibrium

            if cp > pdh:
                score += 2; signals.append(f"D: precio sobre PDH ({pdh:.0f}) — expansión alcista +2")
            elif cp < pdl:
                score -= 2; signals.append(f"D: precio bajo PDL ({pdl:.0f}) — expansión bajista -2")
            elif cp > mid:
                score += 1; signals.append(f"D: precio en zona premium ({mid:.0f}-{pdh:.0f}) +1")
            else:
                score -= 1; signals.append(f"D: precio en zona descuento ({pdl:.0f}-{mid:.0f}) -1")

            # Daily trend: 3 days
            if len(dy) >= 4:
                d2, d3 = dy.iloc[-3], dy.iloc[-4]
                dh = [float(d3["High"]), float(d2["High"]), float(yd["High"])]
                dl = [float(d3["Low"]),  float(d2["Low"]),  float(yd["Low"])]
                if dh[2]>dh[1]>dh[0] and dl[2]>dl[1]>dl[0]:
                    score += 1; signals.append("D: HH+HL diario (tendencia alcista) +1")
                elif dh[2]<dh[1]<dh[0] and dl[2]<dl[1]<dl[0]:
                    score -= 1; signals.append("D: LH+LL diario (tendencia bajista) -1")

    except Exception as e:
        signals.append(f"D: error ({e})")

    try:
        # ── 4H: estructura reciente ──
        h1 = yf.Ticker(yf_sym).history(period="10d", interval="1h", auto_adjust=True)
        if len(h1) >= 12:
            import pandas as pd
            h4 = h1.resample("4h", origin="start").agg(
                Open=("Open","first"), High=("High","max"),
                Low=("Low","min"),   Close=("Close","last")
            ).dropna()

            if len(h4) >= 4:
                bars = h4.iloc[-4:]
                highs = [float(b["High"])  for _, b in bars.iterrows()]
                lows  = [float(b["Low"])   for _, b in bars.iterrows()]
                closes= [float(b["Close"]) for _, b in bars.iterrows()]

                # Higher highs + higher lows
                if highs[-1]>highs[-2] and lows[-1]>lows[-2]:
                    score += 2; signals.append("4H: HH+HL → estructura alcista +2")
                elif highs[-1]<highs[-2] and lows[-1]<lows[-2]:
                    score -= 2; signals.append("4H: LH+LL → estructura bajista -2")
                elif highs[-1]>highs[-2]:
                    score += 1; signals.append("4H: higher high (momentum alcista) +1")
                elif lows[-1]<lows[-2]:
                    score -= 1; signals.append("4H: lower low (momentum bajista) -1")

                # Price vs 4H midpoint of last completed bar
                last_h4 = h4.iloc[-2]
                h4_mid = (float(last_h4["High"]) + float(last_h4["Low"])) / 2
                if closes[-1] > h4_mid:
                    score += 1; signals.append(f"4H: cierre sobre midpoint ({h4_mid:.0f}) +1")
                else:
                    score -= 1; signals.append(f"4H: cierre bajo midpoint ({h4_mid:.0f}) -1")

    except Exception as e:
        signals.append(f"4H: error ({e})")

    # ── Conclusion ──
    if score >= 4:
        suggested = "BULLISH"
    elif score <= -4:
        suggested = "BEARISH"
    else:
        suggested = "NEUTRAL"

    confidence = min(abs(score) / 8 * 100, 100)

    return {
        "suggested": suggested,
        "score": score,
        "max_score": 10,
        "confidence": round(confidence, 0),
        "signals": signals,
        "symbol": yf_sym,
        "ts": _ts(),
        "note": "Sugerencia automatizada — confirmar con análisis propio de Weekly+Daily+4H",
    }


def ifvg_scanner():
    """Background thread: scans for IFVGs every ~60s on bar close."""
    import yfinance as yf

    print("[SCANNER] IFVG detector started — watching:", WATCH_SYMBOLS)

    last_processed = {}  # sym → last bar unix timestamp processed

    while True:
        time.sleep(55)   # ~1 min loop

        if not DETECTOR_STATE["enabled"]:
            DETECTOR_STATE["status"] = "paused"
            continue

        kz = kz_status()
        if not kz["active"]:
            DETECTOR_STATE["status"] = "idle"
            DETECTOR_STATE["last_run"] = _ts()
            continue

        if DAILY_BIAS["value"] == "NEUTRAL":
            DETECTOR_STATE["status"] = "idle"
            continue

        DETECTOR_STATE["status"] = "scanning"
        DETECTOR_STATE["last_run"] = _ts()

        for sym in WATCH_SYMBOLS:
            yf_sym = YF_SYMBOLS_DETECT.get(sym, sym)
            try:
                df = yf.Ticker(yf_sym).history(period="5d", interval="5m", auto_adjust=True)
                if df.empty or len(df) < 5:
                    continue

                candles = []
                for ts, row in df.iterrows():
                    candles.append({
                        "time":  int(ts.timestamp()),
                        "open":  float(row["Open"]),
                        "high":  float(row["High"]),
                        "low":   float(row["Low"]),
                        "close": float(row["Close"]),
                    })

                # Only process if we have a NEW closed bar
                last_bar_ts = candles[-1]["time"]
                if last_processed.get(sym) == last_bar_ts:
                    continue  # same bar, skip
                last_processed[sym] = last_bar_ts

                # Run detector on last 50 bars
                detected = detect_ifvg(candles[-50:])
                if not detected:
                    continue

                # Take the LAST signal (most recent bar)
                sig = detected[-1]
                action = sig["action"]
                close  = sig["close"]
                reason = sig["reason"]

                # Bias filter
                bias = DAILY_BIAS["value"]
                if (action == "BUY" and bias == "BEARISH") or \
                   (action == "SELL" and bias == "BULLISH"):
                    print(f"[SCANNER] IFVG {action} on {sym} — filtered (contra bias {bias})")
                    continue

                # Skip if already have active position
                if ACTIVE_POSITION:
                    print(f"[SCANNER] IFVG {action} on {sym} — filtered (position open)")
                    continue

                payload = {
                    "action": action, "symbol": sym,
                    "close": close, "timeframe": "5",
                    "time": _ts(), "reason": reason,
                }
                SIGNALS_QUEUE.append(payload)
                DETECTOR_STATE["last_signal"] = f"{action} {sym} @ {close:.0f} — {reason}"
                DETECTOR_STATE["signals_today"] += 1
                print(f"[SCANNER] >>> {action} {sym} @ {close:.0f} | {reason}")

            except Exception as e:
                print(f"[SCANNER] Error {sym}: {e}")

        DETECTOR_STATE["status"] = "idle"


# ── FastAPI ───────────────────────────────────────────────────────────────────
app=FastAPI(title="IFVG Trading Bot",version="2.0.0-beta")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"])

TV_SYMBOLS={"NQ1!":"NASDAQ:NDX","ES1!":"SP:SPX","MNQ1!":"NASDAQ:NDX","MES1!":"SP:SPX",
            "AAPL":"NASDAQ:AAPL","MSFT":"NASDAQ:MSFT","NVDA":"NASDAQ:NVDA",
            "TSLA":"NASDAQ:TSLA","META":"NASDAQ:META","AMZN":"NASDAQ:AMZN",
            "EURUSD":"FX:EURUSD","GBPUSD":"FX:GBPUSD"}

class Signal(BaseModel):
    action:str; symbol:str; timeframe:str="1"
    close:float; time:str=""; reason:str="IFVG_manual"

    # TradingView envía timenow como unix ms (ej. "1746000000000")
    # Normalizar a ISO string al recibir
    def iso_time(self) -> str:
        if not self.time:
            return _ts()
        try:
            ms = int(self.time)
            from datetime import timezone as tz
            return datetime.fromtimestamp(ms/1000, tz=tz.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        except (ValueError, TypeError):
            return self.time or _ts()

class BiasUpdate(BaseModel):
    value:str  # BULLISH | NEUTRAL | BEARISH

class ConfigUpdate(BaseModel):
    key:str; value:float

@app.post("/webhook")
async def webhook(signal:Signal, x_api_key:str=Header(None)):
    key=os.getenv("WEBHOOK_API_KEY","")
    if key and x_api_key!=key: raise HTTPException(403,"Unauthorized")
    SIGNALS_QUEUE.append(signal.model_dump())
    return {"status":"queued","action":signal.action,"symbol":signal.symbol}

@app.get("/status")
async def status():
    return {"status":"online","mode":"LOCAL BETA","kill_zone":kz_status(),
            "daily_bias":DAILY_BIAS["value"],"news":next_news(),"version":"2.0.0-beta"}

@app.get("/api/trades")
async def trades_api(limit:int=60):
    return {"trades":TRADES_LOG[-limit:],"total":len(TRADES_LOG)}

@app.get("/api/equity")
async def equity_api():
    p=ACCOUNT["peak"]; dd=(p-ACCOUNT["balance"])/p*100 if p else 0
    return {"curve":EQUITY_CURVE[-120:],"balance":round(ACCOUNT["balance"],2),
            "start":ACCOUNT["start"],"peak":round(p,2),"max_drawdown_pct":round(dd,2)}

@app.get("/api/analytics")
async def analytics_api():
    closed=[t for t in TRADES_LOG if t.get("event")=="trade_closed"]
    orders=[t for t in TRADES_LOG if t.get("event")=="order_placed"]
    skips =[t for t in TRADES_LOG if t.get("event")=="skip"]
    wins  =[t for t in closed if t.get("pnl",0)>0]
    losses=[t for t in closed if t.get("pnl",0)<=0]
    tw=sum(t.get("pnl",0) for t in wins)
    tl=abs(sum(t.get("pnl",0) for t in losses))
    aw=tw/len(wins) if wins else 0
    al=tl/len(losses) if losses else 0
    p=ACCOUNT["peak"]; dd=(p-ACCOUNT["balance"])/p*100 if p else 0
    sr:dict[str,int]={}
    for s in skips:
        r=s.get("reason","?").split("—")[0].strip()[:40]
        sr[r]=sr.get(r,0)+1
    return {"orders_placed":len(orders),"trades_closed":len(closed),
            "signals_skipped":len(skips),"wins":len(wins),"losses":len(losses),
            "win_rate":round(len(wins)/len(closed),3) if closed else None,
            "profit_factor":round(tw/tl,2) if tl>0 else None,
            "avg_rr":round(aw/al,2) if al>0 else None,
            "total_pnl":round(tw-tl,2),"balance":round(ACCOUNT["balance"],2),
            "max_drawdown_pct":round(dd,2),"skip_reasons":sr}

@app.get("/api/position")
async def position_api():
    return {"position":ACTIVE_POSITION or None}

@app.get("/api/config")
async def config_get():
    return CONFIG

@app.post("/api/config")
async def config_set(u:ConfigUpdate):
    BOUNDS={"MAX_RISK_PCT":(0.003,0.015),"MIN_RR":(1.5,4.0),"STOP_TICKS":(3,30),
            "STOP_PCT":(0.2,2.0),"MAX_TRADES_SESSION":(1,4),
            "MAX_DAILY_LOSS_PCT":(0.01,0.06),"WIN_PROB":(0.1,0.9)}
    if u.key not in CONFIG: raise HTTPException(400,f"Unknown key: {u.key}")
    lo,hi=BOUNDS.get(u.key,(0,1e9))
    if not (lo<=u.value<=hi): raise HTTPException(400,f"{u.key} must be {lo}–{hi}")
    CONFIG[u.key]=u.value
    return {"key":u.key,"value":u.value,"status":"applied"}

@app.post("/api/bias")
async def bias_set(b:BiasUpdate):
    if b.value not in ("BULLISH","NEUTRAL","BEARISH"):
        raise HTTPException(400,"value must be BULLISH|NEUTRAL|BEARISH")
    DAILY_BIAS["value"]=b.value
    return {"bias":b.value}

@app.post("/api/test-signal")
async def test_signal(symbol:str="NQ1!",action:str="BUY",price:float=19250.0):
    sig={"action":action,"symbol":symbol,"close":price,"timeframe":"1","time":"","reason":"IFVG_test"}
    SIGNALS_QUEUE.append(sig)
    return {"status":"queued","signal":sig}

@app.get("/api/scanner")
async def scanner_status():
    return {**DETECTOR_STATE, "watching": WATCH_SYMBOLS}

@app.get("/api/bias-suggestion")
async def bias_suggestion(symbol:str="NQ1!"):
    """
    Automated top-down analysis W/D/4H → suggests bias.
    Cached 30 min (Yahoo Finance rate limit).
    """
    import time as _time
    cached = BIAS_CACHE.get("result")
    cached_ts = BIAS_CACHE.get("ts")
    # Cache valid for 30 min
    if cached and cached_ts and (_time.time() - cached_ts < 1800):
        return cached
    yf_sym = YF_SYMBOLS.get(symbol, "^NDX")
    result = analyze_bias(yf_sym)
    BIAS_CACHE["result"] = result
    BIAS_CACHE["ts"] = _time.time()
    return result

@app.post("/api/scanner/toggle")
async def scanner_toggle():
    DETECTOR_STATE["enabled"] = not DETECTOR_STATE["enabled"]
    return {"enabled": DETECTOR_STATE["enabled"]}

@app.post("/api/reset")
async def reset():
    TRADES_LOG.clear(); EQUITY_CURVE.clear(); SIGNALS_QUEUE.clear(); ACTIVE_POSITION.clear()
    ACCOUNT.update({"balance":ACCOUNT["start"],"peak":ACCOUNT["start"]})
    DAILY_BIAS["value"]="NEUTRAL"
    DETECTOR_STATE.update({"signals_today":0,"last_signal":None})
    if LOG_FILE.exists(): LOG_FILE.unlink()
    return {"status":"reset"}

@app.get("/api/tv-symbol")
async def tv_symbol(symbol:str="NQ1!"):
    return {"tv":TV_SYMBOLS.get(symbol,symbol)}

# Mapping: bot symbol → Yahoo Finance ticker
YF_SYMBOLS = {
    "NQ1!":"^NDX","ES1!":"^GSPC","MNQ1!":"^NDX","MES1!":"^GSPC",
    "AAPL":"AAPL","MSFT":"MSFT","NVDA":"NVDA","TSLA":"TSLA",
    "META":"META","AMZN":"AMZN","EURUSD":"EURUSD=X","GBPUSD":"GBPUSD=X",
}
YF_INTERVAL = {"1":"1m","5":"5m","15":"15m","60":"1h","1H":"1h","4H":"1h","1D":"1d","D":"1d"}
YF_PERIOD   = {"1m":"7d","5m":"60d","15m":"60d","1h":"730d","1d":"5y"}

@app.get("/api/chart-data")
async def chart_data(symbol:str="NQ1!", interval:str="5"):
    try:
        import yfinance as yf
        yf_sym  = YF_SYMBOLS.get(symbol, symbol)
        yf_iv   = YF_INTERVAL.get(interval, "5m")
        period  = YF_PERIOD.get(yf_iv, "60d")
        df = yf.Ticker(yf_sym).history(period=period, interval=yf_iv, auto_adjust=True)
        candles = []
        for ts, row in df.iterrows():
            candles.append({
                "time":  int(ts.timestamp()),
                "open":  round(float(row["Open"]),  2),
                "high":  round(float(row["High"]),  2),
                "low":   round(float(row["Low"]),   2),
                "close": round(float(row["Close"]), 2),
                "volume":int(row.get("Volume", 0)),
            })
        return {"symbol":symbol,"interval":interval,"candles":candles[-600:]}
    except Exception as e:
        return {"symbol":symbol,"interval":interval,"candles":[],"error":str(e)}

# ── Dashboard ─────────────────────────────────────────────────────────────────
DASHBOARD = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>IFVG Bot</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#0d1117;--bg2:#161b22;--bg3:#1c2128;--border:#30363d;--border2:#21262d;
  --text:#c9d1d9;--text2:#8b949e;--text3:#e6edf3;--green:#3fb950;--yellow:#d29922;
  --red:#f85149;--blue:#58a6ff;--purple:#bc8cff}
body{background:var(--bg);color:var(--text);font-family:'SF Mono','Consolas',monospace;
  font-size:13px;height:100vh;display:flex;flex-direction:column;overflow:hidden}

/* Header */
.hdr{background:var(--bg2);border-bottom:1px solid var(--border);padding:10px 16px;
  display:flex;align-items:center;gap:10px;flex-shrink:0;min-height:44px}
.hdr h1{font-size:15px;color:var(--text3);font-weight:600}
.dot{width:8px;height:8px;border-radius:50%;background:var(--green);animation:pulse 2s infinite;flex-shrink:0}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.badge{padding:2px 9px;border-radius:10px;font-size:10px;font-weight:700;letter-spacing:.4px;border:1px solid}
.b-paper{background:#1a2e1a;color:var(--green);border-color:#2ea043}
.b-kz-on{background:#1a2a3a;color:var(--blue);border-color:#388bfd}
.b-kz-off{background:#222;color:var(--text2);border-color:var(--border)}
.b-sb{background:#2a1a3a;color:var(--purple);border-color:#7c4dff}
.b-bias-bull{background:#1a3a1a;color:var(--green);border-color:#2ea043}
.b-bias-bear{background:#3a1a1a;color:var(--red);border-color:#da3633}
.b-bias-neut{background:#222;color:var(--text2);border-color:var(--border)}
.et{font-size:12px;color:var(--text2);margin-left:4px}
.hdr-right{margin-left:auto;display:flex;align-items:center;gap:8px}
.news-pill{background:#3a2a1a;color:var(--yellow);border:1px solid #bb8009;
  padding:2px 9px;border-radius:10px;font-size:10px;font-weight:700;animation:blink 1s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.5}}

/* Symbol bar */
.symbar{background:var(--bg2);border-bottom:1px solid var(--border);padding:7px 16px;
  display:flex;align-items:center;gap:8px;flex-shrink:0}
.symbar select,.symbar button{background:var(--bg3);border:1px solid var(--border);
  color:var(--text);border-radius:5px;font-family:inherit;font-size:12px;cursor:pointer;padding:4px 10px}
.symbar button:hover,.symbar button.act{background:#388bfd;border-color:#58a6ff;color:#fff}
.symbar button.act{font-weight:700}
.sep{width:1px;height:20px;background:var(--border);margin:0 4px}

/* Main layout */
.main{display:flex;flex:1;min-height:0}
.chart-col{flex:1;min-width:0;display:flex;flex-direction:column;border-right:1px solid var(--border)}

/* TradingView chart */
#tv-container{flex:1;min-height:0}
#tv-container iframe{width:100%;height:100%;border:none}

/* Equity mini chart */
.equity-bar{height:90px;background:var(--bg2);border-top:1px solid var(--border);padding:8px 12px;flex-shrink:0}
.equity-label{font-size:10px;color:var(--text2);text-transform:uppercase;letter-spacing:.4px;margin-bottom:4px}
#eq-canvas{width:100%;height:52px;display:block}

/* Sidebar */
.sidebar{width:300px;flex-shrink:0;overflow-y:auto;display:flex;flex-direction:column;gap:0}

/* Sidebar panels */
.panel{border-bottom:1px solid var(--border);padding:12px 14px}
.panel-title{font-size:10px;color:var(--text2);text-transform:uppercase;letter-spacing:.5px;
  margin-bottom:10px;display:flex;justify-content:space-between;align-items:center}

/* Bias */
.bias-btns{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px}
.bias-btn{padding:8px 4px;border-radius:6px;border:1px solid var(--border);background:var(--bg3);
  color:var(--text2);cursor:pointer;font-size:11px;font-weight:600;font-family:inherit;
  text-align:center;transition:all .15s}
.bias-btn.sel-bull{background:#1a3a1a;border-color:var(--green);color:var(--green)}
.bias-btn.sel-neut{background:#2a2a2a;border-color:#555;color:#aaa}
.bias-btn.sel-bear{background:#3a1a1a;border-color:var(--red);color:var(--red)}
.bias-btn:hover{border-color:var(--text2)}

/* Risk calc */
.rc-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:8px}
.rc-label{font-size:10px;color:var(--text2);margin-bottom:3px}
.rc-input{width:100%;background:var(--bg3);border:1px solid var(--border);border-radius:5px;
  color:var(--text3);font-family:inherit;font-size:12px;padding:5px 8px}
.rc-input:focus{outline:none;border-color:var(--blue)}
.rc-result{background:var(--bg3);border:1px solid var(--border2);border-radius:6px;
  padding:8px 10px;display:grid;grid-template-columns:1fr 1fr;gap:4px}
.rc-r-label{font-size:10px;color:var(--text2)}
.rc-r-val{font-size:14px;font-weight:700;color:var(--text3)}

/* Signal */
.sig-btns{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:6px}
.btn-long{padding:10px;border-radius:6px;border:1px solid #2ea043;background:#1a3a1a;
  color:var(--green);cursor:pointer;font-size:13px;font-weight:700;font-family:inherit;transition:all .15s}
.btn-long:hover{background:#2ea043;color:#fff}
.btn-short{padding:10px;border-radius:6px;border:1px solid #da3633;background:#3a1a1a;
  color:var(--red);cursor:pointer;font-size:13px;font-weight:700;font-family:inherit;transition:all .15s}
.btn-short:hover{background:#da3633;color:#fff}
.sig-sel{width:100%;background:var(--bg3);border:1px solid var(--border);border-radius:5px;
  color:var(--text);font-family:inherit;font-size:12px;padding:5px 8px;margin-bottom:6px}
.sig-fb{font-size:11px;min-height:16px;text-align:center}

/* Position */
.pos-empty{color:var(--text2);font-size:12px;text-align:center;padding:8px 0}
.pos-card{background:var(--bg3);border-radius:6px;border:1px solid var(--border2);padding:10px}
.pos-sym{font-size:14px;font-weight:700;color:var(--text3)}
.pos-dir{font-size:11px;font-weight:600;padding:1px 7px;border-radius:4px;display:inline-block}
.pos-dir-long{background:#1a3a1a;color:var(--green)}
.pos-dir-short{background:#3a1a1a;color:var(--red)}
.pos-row{display:flex;justify-content:space-between;font-size:11px;color:var(--text2);margin-top:4px}
.pos-pnl{font-size:18px;font-weight:700;margin-top:6px}

/* Metrics */
.metrics-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.m-card{background:var(--bg3);border-radius:6px;border:1px solid var(--border2);padding:8px 10px}
.m-label{font-size:9px;color:var(--text2);text-transform:uppercase;letter-spacing:.4px;margin-bottom:2px}
.m-val{font-size:16px;font-weight:700;color:var(--text3)}
.m-val.g{color:var(--green)}.m-val.y{color:var(--yellow)}.m-val.r{color:var(--red)}
.m-sub{font-size:9px;color:#444;margin-top:2px}

/* Config */
.cfg-row{display:flex;align-items:center;gap:8px;margin-bottom:6px}
.cfg-label{flex:1;font-size:11px;color:var(--text2)}
.cfg-input{width:70px;background:var(--bg3);border:1px solid var(--border);border-radius:5px;
  color:var(--text3);font-family:inherit;font-size:12px;padding:3px 6px;text-align:right}
.cfg-input:focus{outline:none;border-color:var(--blue)}
.cfg-apply{padding:2px 8px;border-radius:4px;border:1px solid var(--border);background:var(--bg3);
  color:var(--text2);cursor:pointer;font-size:11px;font-family:inherit}
.cfg-apply:hover{border-color:var(--blue);color:var(--blue)}

/* Trade log */
.log-wrap{border-top:1px solid var(--border)}
.log-hdr{background:var(--bg2);padding:7px 16px;font-size:10px;color:var(--text2);
  text-transform:uppercase;letter-spacing:.4px;border-bottom:1px solid var(--border);
  display:flex;justify-content:space-between}
.log-table{width:100%;border-collapse:collapse;font-size:11px}
.log-table td{padding:5px 16px;border-top:1px solid var(--border2)}
.log-table tr:hover td{background:var(--bg3)}
.b{display:inline-block;padding:1px 7px;border-radius:3px;font-size:10px;font-weight:600}
.b-ord{background:#1f3a5f;color:var(--blue)}.b-sk{background:#222;color:var(--text2)}
.b-win{background:#1a3a1a;color:var(--green)}.b-ls{background:#3a1a1a;color:var(--red)}
.b-buy{background:#1a3a1a;color:var(--green)}.b-sell{background:#3a1a1a;color:var(--red)}

/* Reset btn */
.btn-reset{padding:4px 10px;border-radius:5px;border:1px solid var(--border);background:var(--bg3);
  color:var(--text2);cursor:pointer;font-size:11px;font-family:inherit}
.btn-reset:hover{border-color:var(--red);color:var(--red)}

/* Scrollbar */
.sidebar::-webkit-scrollbar{width:4px}
.sidebar::-webkit-scrollbar-track{background:var(--bg)}
.sidebar::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
</style>
</head>
<body>

<!-- Header -->
<div class="hdr">
  <div class="dot" id="dot"></div>
  <h1>IFVG Bot</h1>
  <span class="badge b-paper">PAPER BETA</span>
  <span class="badge b-kz-off" id="kz-badge">KZ OFF</span>
  <span class="badge b-bias-neut" id="bias-badge">NEUTRAL</span>
  <span id="news-pill" style="display:none" class="news-pill">⚠ NFP</span>
  <span class="et" id="et-clock">--:-- ET</span>
  <div class="hdr-right">
    <button class="btn-reset" onclick="doReset()">↺ Reset</button>
  </div>
</div>

<!-- Symbol / TF bar -->
<div class="symbar">
  <select id="sym-sel" onchange="changeSymbol()">
    <option value="NQ1!">NQ (Nasdaq Fut.)</option>
    <option value="ES1!">ES (S&P500 Fut.)</option>
    <option value="AAPL">AAPL</option>
    <option value="MSFT">MSFT</option>
    <option value="NVDA">NVDA</option>
    <option value="TSLA">TSLA</option>
    <option value="EURUSD">EURUSD</option>
  </select>
  <div class="sep"></div>
  <button onclick="setTF('1')"  id="tf-1"  class="act">1m</button>
  <button onclick="setTF('5')"  id="tf-5" >5m</button>
  <button onclick="setTF('15')" id="tf-15">15m</button>
  <button onclick="setTF('60')" id="tf-60">1H</button>
  <button onclick="setTF('240')"id="tf-240">4H</button>
  <button onclick="setTF('D')"  id="tf-D" >1D</button>
  <div class="sep"></div>
  <span style="font-size:11px;color:var(--text2)">Kill zone: 8:30-11:00 ET &nbsp;|&nbsp; Silver Bullet: 10:00-11:00 ET</span>
</div>

<!-- Main -->
<div class="main">

  <!-- Left: Chart + Equity -->
  <div class="chart-col">
    <div id="tv-container"></div>
    <div class="equity-bar">
      <div class="equity-label">Equity curve &nbsp;<span id="eq-stats" style="color:var(--text2)"></span></div>
      <canvas id="eq-canvas"></canvas>
    </div>
  </div>

  <!-- Right: Sidebar -->
  <div class="sidebar">

    <!-- Bias Sugerido W/D/4H -->
    <div class="panel">
      <div class="panel-title">
        <span>Bias Sugerido</span>
        <span style="color:var(--text2);font-size:10px">W+D+4H auto</span>
        <button onclick="loadBiasSuggestion()" id="bias-refresh-btn"
          style="margin-left:auto;background:var(--bg3);border:1px solid var(--border);color:var(--text2);
                 padding:3px 8px;border-radius:4px;cursor:pointer;font-size:10px;font-family:inherit">
          ↻
        </button>
      </div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
        <span id="bs-badge" style="font-size:16px;font-weight:700;color:var(--text2)">—</span>
        <div>
          <div style="font-size:10px;color:var(--text2)">Score: <span id="bs-score">—</span> · Confianza: <span id="bs-conf">—</span></div>
          <div style="font-size:9px;color:var(--text2)" id="bs-loading">Cargando análisis...</div>
        </div>
      </div>
      <div id="bs-signals" style="font-size:9px;color:var(--text2);line-height:1.7;max-height:80px;overflow-y:auto"></div>
      <div style="font-size:9px;color:#555;margin-top:4px">⚠ Confirma con tu propio análisis antes de operar</div>
    </div>

    <!-- Daily Bias (confirmación manual) -->
    <div class="panel">
      <div class="panel-title"><span>Daily Bias</span><span style="color:var(--text2);font-size:10px">TJR Day-34 · confirmar</span></div>
      <div class="bias-btns">
        <button class="bias-btn" id="bb-bull" onclick="setBias('BULLISH')">▲ BULLISH</button>
        <button class="bias-btn sel-neut" id="bb-neut" onclick="setBias('NEUTRAL')">— NEUTRAL</button>
        <button class="bias-btn" id="bb-bear" onclick="setBias('BEARISH')">▼ BEARISH</button>
      </div>
      <div style="font-size:10px;color:var(--text2);margin-top:8px">
        Sin bias claro → no operar (Fede Day-22)
      </div>
    </div>

    <!-- IFVG Scanner status -->
    <div class="panel" id="scanner-panel">
      <div class="panel-title">
        <span>Auto Scanner</span>
        <span id="scanner-dot" style="width:8px;height:8px;border-radius:50%;background:#555;display:inline-block;margin-left:6px"></span>
        <button onclick="toggleScanner()" id="scanner-btn"
          style="margin-left:auto;background:var(--bg3);border:1px solid var(--border);color:var(--text2);
                 padding:3px 10px;border-radius:4px;cursor:pointer;font-size:10px;font-family:inherit">
          PAUSE
        </button>
      </div>
      <div style="font-size:10px;color:var(--text2);line-height:1.6" id="scanner-info">
        Esperando kill zone...
      </div>
      <div style="font-size:10px;color:var(--text2);margin-top:2px" id="scanner-windows">
        Ventanas: A 8:30-9:00 · B 9:30-10:30 · SB 10:00-11:00
      </div>
      <div style="font-size:10px;color:var(--green);margin-top:4px;min-height:14px" id="scanner-last"></div>
    </div>

    <!-- Risk Calculator -->
    <div class="panel">
      <div class="panel-title"><span>Risk Calculator</span><span style="color:var(--text2);font-size:10px">1% rule</span></div>
      <div class="rc-grid">
        <div>
          <div class="rc-label">Entry price</div>
          <input class="rc-input" id="rc-entry" type="number" value="19250" oninput="calcRisk()">
        </div>
        <div>
          <div class="rc-label">SL ticks</div>
          <input class="rc-input" id="rc-sl" type="number" value="10" oninput="calcRisk()">
        </div>
        <div>
          <div class="rc-label">Account $</div>
          <input class="rc-input" id="rc-acc" type="number" value="50000" oninput="calcRisk()">
        </div>
        <div>
          <div class="rc-label">Risk %</div>
          <input class="rc-input" id="rc-risk" type="number" value="1" step="0.1" oninput="calcRisk()">
        </div>
      </div>
      <div class="rc-result" id="rc-result">
        <div><div class="rc-r-label">Position size</div><div class="rc-r-val" id="rc-size">—</div></div>
        <div><div class="rc-r-label">Risk $</div><div class="rc-r-val" id="rc-riskusd">—</div></div>
        <div><div class="rc-r-label">SL</div><div class="rc-r-val" id="rc-slpx">—</div></div>
        <div><div class="rc-r-label">TP (2:1)</div><div class="rc-r-val" id="rc-tppx">—</div></div>
      </div>
    </div>

    <!-- Send signal -->
    <div class="panel">
      <div class="panel-title"><span>Enviar señal</span></div>
      <select class="sig-sel" id="sig-sym">
        <option value="NQ1!">NQ1! — Nasdaq</option>
        <option value="ES1!">ES1! — S&P500</option>
        <option value="AAPL">AAPL</option>
        <option value="MSFT">MSFT</option>
        <option value="NVDA">NVDA</option>
        <option value="TSLA">TSLA</option>
        <option value="EURUSD">EURUSD</option>
      </select>
      <div class="sig-btns">
        <button class="btn-long"  onclick="fire('BUY')">▲ LONG</button>
        <button class="btn-short" onclick="fire('SELL')">▼ SHORT</button>
      </div>
      <div class="sig-fb" id="sig-fb"></div>
    </div>

    <!-- Active position -->
    <div class="panel">
      <div class="panel-title"><span>Posición activa</span><span id="pos-badge"></span></div>
      <div id="pos-body"><div class="pos-empty">Flat — sin posición abierta</div></div>
    </div>

    <!-- Metrics -->
    <div class="panel">
      <div class="panel-title"><span>Métricas</span></div>
      <div class="metrics-grid">
        <div class="m-card"><div class="m-label">Win Rate</div><div class="m-val" id="m-wr">—</div><div class="m-sub">target ≥50%</div></div>
        <div class="m-card"><div class="m-label">Profit Factor</div><div class="m-val" id="m-pf">—</div><div class="m-sub">target ≥1.5</div></div>
        <div class="m-card"><div class="m-label">Avg RR</div><div class="m-val" id="m-rr">—</div><div class="m-sub">target ≥2:1</div></div>
        <div class="m-card"><div class="m-label">Max DD</div><div class="m-val" id="m-dd">0%</div><div class="m-sub">límite 20%</div></div>
        <div class="m-card"><div class="m-label">Balance</div><div class="m-val" id="m-bal">$50k</div><div class="m-sub" id="m-pnl">PnL: —</div></div>
        <div class="m-card"><div class="m-label">W / L</div><div class="m-val" id="m-wl">—</div><div class="m-sub" id="m-skip">Filtradas: 0</div></div>
      </div>
    </div>

    <!-- Bot Config -->
    <div class="panel">
      <div class="panel-title"><span>Parámetros</span><span style="color:var(--text2);font-size:10px">editable</span></div>
      <div id="cfg-rows"></div>
    </div>

  </div><!-- /sidebar -->
</div><!-- /main -->

<!-- Trade log -->
<div class="log-wrap">
  <div class="log-hdr">
    <span>Eventos recientes</span>
    <span id="log-ts" style="font-size:10px;color:#444"></span>
  </div>
  <table class="log-table">
    <tbody id="log-body">
      <tr><td colspan="5" style="color:var(--text2);padding:14px;text-align:center">
        Configura el Daily Bias y pulsa ▲ LONG o ▼ SHORT
      </td></tr>
    </tbody>
  </table>
</div>

<!-- Lightweight Charts — open source, sin restricciones, MIT license -->
<script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
<script>

// ── Lightweight Charts (Yahoo Finance data) ───────────────────────────────────
let lwChart=null, candleSeries=null, volSeries=null, markerList=[];
let currentSym="NQ1!", currentTF="5";

function buildTV(sym,tf){
  currentSym=sym; currentTF=tf;
  const wrap=document.getElementById("tv-container");
  wrap.innerHTML='<div id="lw_chart" style="width:100%;height:100%"></div>';
  const el=document.getElementById("lw_chart");

  if(typeof LightweightCharts==="undefined"){
    wrap.innerHTML='<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text2)">Cargando librería de charts...</div>';
    return;
  }

  if(lwChart){ lwChart.remove(); lwChart=null; }

  lwChart=LightweightCharts.createChart(el,{
    width:el.clientWidth, height:el.clientHeight,
    layout:{background:{color:"#0d1117"},textColor:"#c9d1d9"},
    grid:{vertLines:{color:"#21262d"},horzLines:{color:"#21262d"}},
    crosshair:{mode:1},
    rightPriceScale:{borderColor:"#30363d"},
    timeScale:{borderColor:"#30363d",timeVisible:true,secondsVisible:false},
    handleScroll:true, handleScale:true,
  });

  candleSeries=lwChart.addCandlestickSeries({
    upColor:"#3fb950",downColor:"#f85149",
    borderVisible:false,
    wickUpColor:"#3fb950",wickDownColor:"#f85149",
  });

  volSeries=lwChart.addHistogramSeries({
    priceFormat:{type:"volume"},
    priceScaleId:"vol",
    scaleMargins:{top:0.82,bottom:0},
  });
  lwChart.priceScale("vol").applyOptions({scaleMargins:{top:0.82,bottom:0}});

  // Resize observer
  new ResizeObserver(()=>{
    if(lwChart) lwChart.resize(el.clientWidth,el.clientHeight);
  }).observe(el);

  loadChartData(sym,tf);
}

async function loadChartData(sym,tf){
  const wrap=document.getElementById("tv-container");
  try {
    const data=await fetch(`/api/chart-data?symbol=${sym}&interval=${tf}`).then(r=>r.json());
    if(!data.candles||data.candles.length===0){
      if(data.error) console.warn("Chart error:",data.error);
      wrap.innerHTML+=`<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);color:var(--text2);font-size:12px">Sin datos — ${data.error||"intenta otro símbolo"}</div>`;
      return;
    }
    candleSeries.setData(data.candles);
    volSeries.setData(data.candles.map(c=>({
      time:c.time, value:c.volume,
      color:c.close>=c.open?"#3fb95033":"#f8514933"
    })));
    addTradeMarkers(data.candles);
    lwChart.timeScale().fitContent();
  } catch(e){ console.error("loadChartData",e); }
}

function addTradeMarkers(candles){
  if(!candleSeries||!markerList.length) return;
  // Poner marcadores de nuestros trades en el chart
  const minT=candles[0]?.time||0;
  const markers=markerList
    .filter(m=>m.time>=minT)
    .sort((a,b)=>a.time-b.time);
  candleSeries.setMarkers(markers);
}

function pushMarker(ts,action,price){
  const t=Math.floor(new Date(ts).getTime()/1000);
  markerList.push({
    time:t, position:action==="BUY"?"belowBar":"aboveBar",
    color:action==="BUY"?"#3fb950":"#f85149",
    shape:action==="BUY"?"arrowUp":"arrowDown",
    text:`${action} ${price}`
  });
}

function changeSymbol(){
  currentSym=document.getElementById("sym-sel").value;
  buildTV(currentSym,currentTF);
  document.getElementById("sig-sym").value=currentSym;
  calcRisk();
}

function setTF(tf){
  currentTF=tf;
  ["1","5","15","60","240","D"].forEach(t=>{
    const el=document.getElementById("tf-"+t);
    if(el) el.classList.toggle("act",t===tf);
  });
  buildTV(currentSym,tf);
}

// Recargar datos cada 60s sin perder la vista
setInterval(()=>{
  if(candleSeries) loadChartData(currentSym,currentTF);
}, 60000);

// Init chart — 5m por defecto (datos más estables)
window.addEventListener("load",()=>{
  setTimeout(()=>buildTV("NQ1!","5"),400);
  setTimeout(()=>loadBiasSuggestion(),1500);  // load bias suggestion after chart
});

// ── Equity chart ─────────────────────────────────────────────────────────────
const eqCanvas=document.getElementById("eq-canvas");
const eqCtx=eqCanvas.getContext("2d");
let eqData=[],eqStart=50000;

function drawEq(pts,start){
  const W=eqCanvas.parentElement.offsetWidth-24, H=52;
  eqCanvas.width=W; eqCanvas.height=H;
  eqCtx.fillStyle="#161b22"; eqCtx.fillRect(0,0,W,H);
  if(pts.length<2){
    eqCtx.fillStyle="#30363d"; eqCtx.font="10px Consolas"; eqCtx.textAlign="center";
    eqCtx.fillText("Curva de equity — realiza trades para verla",W/2,H/2+4); return;
  }
  const vals=pts.map(p=>p.balance);
  const mn=Math.min(...vals,start*.97), mx=Math.max(...vals,start*1.03);
  const px=i=>Math.round((i/(pts.length-1))*W);
  const py=v=>Math.round(H-((v-mn)/(mx-mn))*H);
  const last=vals[vals.length-1], isUp=last>=start;
  const col=isUp?"#3fb950":"#f85149";
  // zero line
  const y0=py(start);
  eqCtx.strokeStyle="#30363d"; eqCtx.lineWidth=1; eqCtx.setLineDash([3,3]);
  eqCtx.beginPath(); eqCtx.moveTo(0,y0); eqCtx.lineTo(W,y0); eqCtx.stroke();
  eqCtx.setLineDash([]);
  // fill
  const grad=eqCtx.createLinearGradient(0,0,0,H);
  grad.addColorStop(0,isUp?"rgba(63,185,80,.3)":"rgba(248,81,73,.3)");
  grad.addColorStop(1,"rgba(13,17,23,0)");
  eqCtx.beginPath();
  pts.forEach((p,i)=>i===0?eqCtx.moveTo(px(i),py(p.balance)):eqCtx.lineTo(px(i),py(p.balance)));
  eqCtx.lineTo(W,H); eqCtx.lineTo(0,H); eqCtx.closePath();
  eqCtx.fillStyle=grad; eqCtx.fill();
  // line
  eqCtx.beginPath(); eqCtx.strokeStyle=col; eqCtx.lineWidth=2;
  pts.forEach((p,i)=>i===0?eqCtx.moveTo(px(i),py(p.balance)):eqCtx.lineTo(px(i),py(p.balance)));
  eqCtx.stroke();
}

// ── Risk calculator ───────────────────────────────────────────────────────────
function calcRisk(){
  const entry=parseFloat(document.getElementById("rc-entry").value)||0;
  const slTicks=parseFloat(document.getElementById("rc-sl").value)||10;
  const acc=parseFloat(document.getElementById("rc-acc").value)||50000;
  const riskPct=parseFloat(document.getElementById("rc-risk").value)||1;
  // Use 0.25pt tick for NQ/ES, 0.5% for stocks
  const isFut=["NQ1!","ES1!","MNQ1!","MES1!"].includes(currentSym);
  const tickSz=isFut?0.25:0.01;
  const tickVal=currentSym.startsWith("NQ")?5:currentSym.startsWith("ES")?12.5:1;
  const riskUsd=acc*riskPct/100;
  const riskPerCont=slTicks*tickVal;
  const size=Math.max(1,Math.floor(riskUsd/riskPerCont));
  const slDist=slTicks*tickSz;
  const sl=isFut?(entry-slDist).toFixed(2):(entry*(1-riskPct/100)).toFixed(2);
  const tp=isFut?(entry+slDist*2).toFixed(2):(entry*(1+riskPct/100*2)).toFixed(2);
  document.getElementById("rc-size").textContent=isFut?size+"x":"—";
  document.getElementById("rc-riskusd").textContent="$"+riskUsd.toFixed(0);
  document.getElementById("rc-slpx").textContent=sl;
  document.getElementById("rc-tppx").textContent=tp;
}
calcRisk();

// ── Config panel ──────────────────────────────────────────────────────────────
const CFG_LABELS={
  "MAX_RISK_PCT":["Riesgo/trade","0.01 = 1%"],
  "MIN_RR":["Min RR","≥1.5"],
  "STOP_PCT":["Stop % (stocks)","0.5%"],
  "MAX_TRADES_SESSION":["Max trades/sesión","1-4"],
  "MAX_DAILY_LOSS_PCT":["Daily loss limit","0.03 = 3%"],
  "WIN_PROB":["Win prob (sim)","0.6 = 60%"],
};

async function loadConfig(){
  const cfg=await fetch("/api/config").then(r=>r.json());
  const rows=document.getElementById("cfg-rows");
  rows.innerHTML="";
  for(const [k,v] of Object.entries(cfg)){
    const [label,hint]=CFG_LABELS[k]||[k,""];
    rows.innerHTML+=`<div class="cfg-row">
      <div class="cfg-label">${label}<br><span style="font-size:9px;color:#444">${hint}</span></div>
      <input class="cfg-input" id="cfg-${k}" type="number" step="0.001" value="${v}">
      <button class="cfg-apply" onclick="applyConfig('${k}')">✓</button>
    </div>`;
  }
}

async function applyConfig(key){
  const val=parseFloat(document.getElementById("cfg-"+key).value);
  const r=await fetch("/api/config",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({key,value:val})});
  const d=await r.json();
  const el=document.getElementById("cfg-"+key);
  if(r.ok){ el.style.borderColor="var(--green)"; setTimeout(()=>el.style.borderColor="",1500); }
  else{ el.style.borderColor="var(--red)"; alert(d.detail||"Error"); }
}

loadConfig();

// ── Daily Bias ────────────────────────────────────────────────────────────────
async function setBias(val){
  await fetch("/api/bias",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({value:val})});
  updateBiasUI(val);
}

function updateBiasUI(val){
  ["bull","neut","bear"].forEach(b=>{
    document.getElementById("bb-"+b).className="bias-btn";
  });
  const map={"BULLISH":"bb-bull sel-bull","NEUTRAL":"bb-neut sel-neut","BEARISH":"bb-bear sel-bear"};
  const bid={"BULLISH":"bb-bull","NEUTRAL":"bb-neut","BEARISH":"bb-bear"};
  if(bid[val]) document.getElementById(bid[val]).className="bias-btn "+map[val];
  const badge=document.getElementById("bias-badge");
  badge.textContent=val;
  badge.className="badge "+{"BULLISH":"b-bias-bull","NEUTRAL":"b-bias-neut","BEARISH":"b-bias-bear"}[val];
}

// ── Actions ───────────────────────────────────────────────────────────────────
async function fire(action){
  const sym=document.getElementById("sig-sym").value;
  const PRICES={"NQ1!":19250,"ES1!":5300,"AAPL":172.5,"MSFT":415,"NVDA":875,"TSLA":180,"EURUSD":1.085};
  const price=PRICES[sym]||100;
  const fb=document.getElementById("sig-fb");
  fb.style.color="var(--yellow)"; fb.textContent=`Enviando ${action} ${sym}...`;
  const r=await fetch(`/api/test-signal?symbol=${sym}&action=${action}&price=${price}`,{method:"POST"});
  const d=await r.json();
  fb.style.color="var(--green)"; fb.textContent="✓ En cola — procesando...";
  setTimeout(()=>{fb.textContent="";},4000);
  setTimeout(refresh,600);
}

async function doReset(){
  if(!confirm("¿Resetear todas las trades y el balance?")) return;
  await fetch("/api/reset",{method:"POST"});
  await refresh();
}

// ── Metric helpers ────────────────────────────────────────────────────────────
function setM(id,v,fmt,good,warn){
  const el=document.getElementById(id);
  el.textContent=v==null?"—":fmt(v);
  el.className="m-val "+(v==null?"":v>=good?"g":v>=warn?"y":"r");
}

// ── Main refresh ──────────────────────────────────────────────────────────────
let lastLogCount=0;

async function loadBiasSuggestion(){
  const btn=document.getElementById("bias-refresh-btn");
  btn.textContent="..."; btn.disabled=true;
  document.getElementById("bs-loading").textContent="Analizando W+D+4H (Yahoo Finance)...";
  try{
    const sym=(document.getElementById("sym-sel")||{}).value||"NQ1!";
    const d=await fetch(`/api/bias-suggestion?symbol=${encodeURIComponent(sym)}`).then(r=>r.json());
    const badge=document.getElementById("bs-badge");
    badge.textContent=d.suggested;
    badge.style.color=d.suggested==="BULLISH"?"var(--green)":d.suggested==="BEARISH"?"var(--red)":"#aaa";
    document.getElementById("bs-score").textContent=(d.score>0?"+":"")+d.score+"/"+d.max_score;
    document.getElementById("bs-conf").textContent=d.confidence+"%";
    document.getElementById("bs-loading").textContent=d.ts?("actualizado "+new Date(d.ts).toLocaleTimeString("es")):"";
    document.getElementById("bs-signals").innerHTML=
      (d.signals||[]).map(s=>`<div style="color:${s.includes("+")?"var(--green)":s.includes("-")?"var(--red)":"var(--text2)"}">· ${s}</div>`).join("")||"<div>Sin datos suficientes</div>";
  }catch(e){
    document.getElementById("bs-loading").textContent="Error cargando análisis";
  }
  btn.textContent="↻"; btn.disabled=false;
}

async function toggleScanner(){
  const d=await fetch("/api/scanner/toggle",{method:"POST"}).then(r=>r.json());
  document.getElementById("scanner-btn").textContent=d.enabled?"PAUSE":"RESUME";
}

async function refresh(){
  try{
    const [s,a,eq,t,pos,sc]=await Promise.all([
      fetch("/status").then(r=>r.json()),
      fetch("/api/analytics").then(r=>r.json()),
      fetch("/api/equity").then(r=>r.json()),
      fetch("/api/trades?limit=30").then(r=>r.json()),
      fetch("/api/position").then(r=>r.json()),
      fetch("/api/scanner").then(r=>r.json()),
    ]);

    // Scanner widget
    const dot=document.getElementById("scanner-dot");
    const info=document.getElementById("scanner-info");
    const last=document.getElementById("scanner-last");
    const btn=document.getElementById("scanner-btn");
    if(!sc.enabled){
      dot.style.background="#555"; info.textContent="Scanner pausado";
      btn.textContent="RESUME";
    } else if(sc.status==="scanning"){
      dot.style.background="#d29922"; info.textContent="Escaneando IFVGs...";
    } else if(sc.status==="idle"){
      const kz=s.kill_zone||{};
      dot.style.background=kz.active?"#3fb950":"#555";
      info.textContent=kz.active
        ? `Activo · NQ/ES 5m · próximo scan ~1m`
        : `En espera — ${kz.next||"fuera de KZ"}`;
      btn.textContent="PAUSE";
    }
    if(sc.last_signal) last.textContent="Última señal: "+sc.last_signal;

    // Header
    const kz=s.kill_zone||{};
    document.getElementById("et-clock").textContent=kz.et||"--:--";
    const kzBadge=document.getElementById("kz-badge");
    if(kz.active){
      kzBadge.className=kz.silver_bullet?"badge b-sb":"badge b-kz-on";
      kzBadge.textContent=kz.silver_bullet?"SILVER BULLET":"KZ ACTIVA";
    } else {
      kzBadge.className="badge b-kz-off";
      kzBadge.textContent="KZ OFF";
    }
    updateBiasUI(s.daily_bias||"NEUTRAL");

    // News
    const news=s.news;
    const np=document.getElementById("news-pill");
    if(news){ np.style.display="inline-block"; np.textContent=`⚠ ${news.name} ${news.mins>0?`en ${news.mins}m`:"AHORA"}`; }
    else { np.style.display="none"; }

    // Metrics
    setM("m-wr",a.win_rate,v=>(v*100).toFixed(0)+"%",0.5,0.4);
    setM("m-pf",a.profit_factor,v=>v.toFixed(2),2.0,1.5);
    setM("m-rr",a.avg_rr,v=>v.toFixed(1)+":1",2.0,1.5);
    const dd=a.max_drawdown_pct||0;
    const ddEl=document.getElementById("m-dd");
    ddEl.textContent=dd.toFixed(1)+"%"; ddEl.className="m-val "+(dd<10?"g":dd<20?"y":"r");
    const bal=eq.balance,start=eq.start,pnl=a.total_pnl;
    const balEl=document.getElementById("m-bal");
    balEl.textContent="$"+(bal/1000).toFixed(1)+"k";
    balEl.className="m-val "+(bal>=start?"g":bal>=start*.95?"y":"r");
    document.getElementById("m-pnl").textContent="PnL: "+(pnl>0?"+":"")+"$"+(pnl||0).toFixed(0);
    document.getElementById("m-wl").textContent=(a.wins||0)+" / "+(a.losses||0);
    document.getElementById("m-skip").textContent="Filtradas: "+(a.signals_skipped||0);

    // Equity
    eqData=eq.curve||[]; eqStart=eq.start;
    drawEq(eqData,eqStart);
    const eqStats=`$${bal.toLocaleString("es",{maximumFractionDigits:0})} · DD ${dd.toFixed(1)}%`;
    document.getElementById("eq-stats").textContent=eqStats;

    // Position
    const pb=document.getElementById("pos-body");
    if(pos.position){
      const p=pos.position, pnlc=p.open_pnl>=0?"var(--green)":"var(--red)";
      pb.innerHTML=`<div class="pos-card">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
          <span class="pos-sym">${p.symbol}</span>
          <span class="pos-dir pos-dir-${p.action==='BUY'?'long':'short'}">${p.action==='BUY'?'LONG':'SHORT'}</span>
        </div>
        <div class="pos-row"><span>Qty</span><span>${p.qty}x</span></div>
        <div class="pos-row"><span>Entry</span><span>${p.entry}</span></div>
        <div class="pos-row"><span>SL</span><span style="color:var(--red)">${p.sl}</span></div>
        <div class="pos-row"><span>TP</span><span style="color:var(--green)">${p.tp}</span></div>
        <div class="pos-pnl" style="color:${pnlc}">${p.open_pnl>=0?"+":""}$${(p.open_pnl||0).toFixed(2)}</div>
      </div>`;
    } else {
      pb.innerHTML='<div class="pos-empty">Flat — sin posición abierta</div>';
    }

    // Trade log
    if(t.total!==lastLogCount){
      lastLogCount=t.total;
      const rows=t.trades.slice().reverse().map(ev=>{
        let tsStr="—";
        try{
          const d=new Date(ev.ts);
          tsStr=d.toLocaleTimeString("es",{timeZone:"America/New_York",hour:"2-digit",minute:"2-digit",second:"2-digit"})+" ET";
        }catch(_){}
        let badge="",sym=ev.symbol||"—",side="—",detail="";
        if(ev.event==="order_placed"){
          badge=`<span class="b b-ord">ORDEN</span>`;
          side=`<span class="b b-${(ev.action||"").toLowerCase()}">${ev.action||""}</span>`;
          const biasTag=ev.bias?` bias:${ev.bias}`:"";
          const sbTag=ev.kz_silver?" 🎯SB":"";
          detail=`Entry ${ev.entry} · SL ${ev.sl} · TP ${ev.tp} · x${ev.qty}${biasTag}${sbTag}`;
          // Pintar marcador en el chart
          if(ev.ts && ev.action && ev.entry) pushMarker(ev.ts, ev.action, ev.entry);
        } else if(ev.event==="trade_closed"){
          const w=ev.pnl>0;
          badge=`<span class="b ${w?"b-win":"b-ls"}">${w?"WIN":"LOSS"}</span>`;
          const c=w?"var(--green)":"var(--red)";
          detail=`<span style="color:${c}">${ev.pnl>0?"+":""}$${(ev.pnl||0).toFixed(2)}</span> · RR ${ev.rr_achieved} · Bal $${(ev.balance_after||0).toLocaleString("es",{maximumFractionDigits:0})}`;
        } else if(ev.event==="skip"){
          badge=`<span class="b b-sk">SKIP</span>`; sym=ev.signal?.symbol||"—"; detail=ev.reason||"";
        }
        return `<tr><td style="color:var(--text2);white-space:nowrap">${tsStr}</td><td>${badge}</td><td>${sym}</td><td>${side}</td><td style="color:var(--text2);max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${detail}</td></tr>`;
      }).join("");
      document.getElementById("log-body").innerHTML=rows||
        '<tr><td colspan="5" style="color:var(--text2);padding:14px;text-align:center">Configura el Daily Bias y pulsa ▲ LONG o ▼ SHORT</td></tr>';
    }
    document.getElementById("log-ts").textContent="Auto-refresh · "+new Date().toLocaleTimeString("es");
    document.getElementById("dot").style.background="var(--green)";
  }catch(e){ document.getElementById("dot").style.background="var(--red)"; console.error(e); }
}

refresh();
setInterval(refresh,3000);
window.addEventListener("resize",()=>drawEq(eqData,eqStart));
</script>
</body>
</html>"""

@app.get("/dashboard",response_class=HTMLResponse)
async def dashboard(): return DASHBOARD

@app.get("/",response_class=HTMLResponse)
async def root(): return HTMLResponse('<meta http-equiv="refresh" content="0;url=/dashboard">',302)

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__=="__main__":
    print("\n"+"="*55)
    print("  IFVG Trading Cockpit — v2")
    print("  Dashboard: http://localhost:8000/dashboard")
    print("  Ctrl+C para parar")
    print("="*55+"\n")
    threading.Thread(target=simulated_executor,daemon=True).start()
    threading.Thread(target=ifvg_scanner,daemon=True).start()
    threading.Thread(target=lambda:(time.sleep(1.5),webbrowser.open("http://localhost:8000/dashboard")),daemon=True).start()
    uvicorn.run(app,host="0.0.0.0",port=8000,log_level="warning")
