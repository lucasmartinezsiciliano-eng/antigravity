"""
Beta local — Trading cockpit completo.
python beta_local.py → http://localhost:8000/dashboard
"""
import json, os, sys, webbrowser, threading, time
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
LOG_FILE      = Path("trades.jsonl")
PAPER_LOG     = Path("paper_trading.jsonl")

ACCOUNT = {"balance":50_000.0,"start":50_000.0,"peak":50_000.0}

ACTIVE_POSITION: dict  = {}   # {} = flat; else {symbol,action,qty,entry,sl,tp,open_pnl}
PAPER_POSITIONS: dict  = {}   # symbol -> open paper trade tracking real outcome

# ── Circuit breaker / Daily state ─────────────────────────────────────────────
CIRCUIT_BREAKER_LIMIT = -800.0   # halt trading if daily PnL drops below this ($)
DAILY_STATE = {
    "date":            "",
    "pnl":             0.0,
    "trades":          0,
    "circuit_breaker": False,
}

# ── Multi-account prop firm tracker ───────────────────────────────────────────
# Cada cuenta tiene balance, DD, profit target y estado de evaluación propios.
# Todas reciben las mismas señales (misma estrategia, misma ejecución).
# Cuentas en modo SIMULACIÓN — mismas reglas reales, sin dinero real todavía.
# Cuando vayamos live: cambiar "sim": True → False y conectar broker.
PROP_ACCOUNTS = [
    {
        "id":           1,
        "name":         "Apex #1",
        "firm":         "Apex Trader Funding",
        "balance":      50_000.0,
        "start":        50_000.0,
        "peak":         50_000.0,
        "profit_target":5_000.0,    # 10% de $50k
        "max_dd_pct":   10.0,       # trailing DD máximo
        "daily_dd_pct": 5.0,        # DD diario máximo
        "daily_pnl":    0.0,
        "daily_date":   "",
        "trades":       0,
        "wins":         0,
        "losses":       0,
        "status":       "EVAL",     # EVAL | PASSED | FAILED | FUNDED
        "start_date":   "",
        "sim":          True,       # True = simulación, False = real
        "payout_pct":   90,         # % de profits para el trader
    },
    {
        "id":           2,
        "name":         "Topstep #1",
        "firm":         "Topstep",
        "balance":      50_000.0,
        "start":        50_000.0,
        "peak":         50_000.0,
        "profit_target":3_000.0,    # 6% de $50k (Topstep es más bajo)
        "max_dd_pct":   8.0,        # Topstep: 8% max trailing DD
        "daily_dd_pct": 4.0,
        "daily_pnl":    0.0,
        "daily_date":   "",
        "trades":       0,
        "wins":         0,
        "losses":       0,
        "status":       "EVAL",
        "start_date":   "",
        "sim":          True,
        "payout_pct":   90,
    },
    {
        "id":           3,
        "name":         "Apex #2",
        "firm":         "Apex Trader Funding",
        "balance":      50_000.0,
        "start":        50_000.0,
        "peak":         50_000.0,
        "profit_target":5_000.0,
        "max_dd_pct":   10.0,
        "daily_dd_pct": 5.0,
        "daily_pnl":    0.0,
        "daily_date":   "",
        "trades":       0,
        "wins":         0,
        "losses":       0,
        "status":       "EVAL",
        "start_date":   "",
        "sim":          True,
        "payout_pct":   90,
    },
    {
        "id":           4,
        "name":         "FTMO #1",
        "firm":         "FTMO",
        "balance":      50_000.0,
        "start":        50_000.0,
        "peak":         50_000.0,
        "profit_target":5_000.0,    # 10% FTMO fase 1
        "max_dd_pct":   10.0,       # 10% max DD relativo
        "daily_dd_pct": 5.0,
        "daily_pnl":    0.0,
        "daily_date":   "",
        "trades":       0,
        "wins":         0,
        "losses":       0,
        "status":       "EVAL",
        "start_date":   "",
        "sim":          True,
        "payout_pct":   80,         # FTMO da 80% (vs 90% Apex)
    },
]

# Inicializa start_date con hoy si está vacío
def _init_accounts():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for acc in PROP_ACCOUNTS:
        if not acc["start_date"]:
            acc["start_date"] = today
_init_accounts()

PROP_ACCOUNTS_LOG = Path("prop_accounts.jsonl")

def _mirror_trade_to_accounts(pnl: float, result: str):
    """Aplica el resultado de un trade a todas las cuentas de fondeo.
    Todas reciben la misma señal → mismo PnL proporcional (mismo % del balance).
    Actualiza balance, DD, wins/losses y estado de evaluación.
    """
    today = _now_ny().strftime("%Y-%m-%d")
    for acc in PROP_ACCOUNTS:
        if acc["status"] in ("FAILED",):
            continue  # cuentas eliminadas no reciben más trades

        # Reset daily PnL on new day
        if acc["daily_date"] != today:
            acc["daily_pnl"]  = 0.0
            acc["daily_date"] = today

        # Apply PnL (same dollar amount — accounts have same size)
        acc["balance"]   = round(acc["balance"] + pnl, 2)
        acc["peak"]      = max(acc["peak"], acc["balance"])
        acc["daily_pnl"] = round(acc["daily_pnl"] + pnl, 2)
        acc["trades"]   += 1
        if result == "WIN":
            acc["wins"]  += 1
        else:
            acc["losses"] += 1

        # Check prop firm rules
        # Trailing DD: desde el pico histórico (Apex/Topstep usan este cálculo)
        # FTMO usa DD relativo al balance inicial, pero usamos trailing para ser conservadores
        drawdown_pct = (acc["peak"] - acc["balance"]) / acc["peak"] * 100 if acc["peak"] > 0 else 0
        daily_dd_pct = abs(acc["daily_pnl"]) / acc["start"] * 100 if acc["daily_pnl"] < 0 else 0
        profit_pct   = (acc["balance"] - acc["start"]) / acc["start"] * 100

        if drawdown_pct >= acc["max_dd_pct"]:
            acc["status"] = "FAILED"
            print(f"[PROP] ⚠️  Cuenta {acc['id']} ELIMINADA — DD {drawdown_pct:.1f}% >= {acc['max_dd_pct']}%")
        elif daily_dd_pct >= acc["daily_dd_pct"]:
            acc["status"] = "FAILED"
            print(f"[PROP] ⚠️  Cuenta {acc['id']} ELIMINADA — DD diario {daily_dd_pct:.1f}%")
        elif profit_pct >= acc["profit_target"] / acc["start"] * 100 and acc["status"] == "EVAL":
            acc["status"] = "PASSED"
            print(f"[PROP] 🎉 Cuenta {acc['id']} APROBADA — profit {profit_pct:.1f}% >= target!")
        else:
            if acc["status"] != "PASSED":
                acc["status"] = "EVAL"

        print(f"  [ACC{acc['id']}] ${acc['balance']:,.0f} | PnL hoy ${acc['daily_pnl']:+.0f} | "
              f"DD {drawdown_pct:.1f}% | {acc['status']}")

    # Persist snapshot
    snap = {"ts": _ts(), "accounts": [
        {"id": a["id"], "balance": a["balance"], "status": a["status"],
         "trades": a["trades"], "wins": a["wins"]}
        for a in PROP_ACCOUNTS
    ]}
    with open(PROP_ACCOUNTS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(snap) + "\n")


def _reset_daily_if_needed():
    """Reset daily counters on new NY trading day."""
    today = _now_ny().strftime("%Y-%m-%d")
    if DAILY_STATE["date"] != today:
        DAILY_STATE.update({"date": today, "pnl": 0.0, "trades": 0, "circuit_breaker": False})
        print(f"[DAILY] Nuevo día {today} — contadores reseteados")

def _build_trade_explanation(symbol, act, entry, sl, tp, sd, rr, qty, risk_usd, bias, kz, news, reason):
    """Genera explicación legible del setup en el momento de la entrada."""
    now_ny   = _now_ny()
    time_str = now_ny.strftime("%H:%M ET")
    dir_str  = "LARGO (BUY)" if act == "BUY" else "CORTO (SELL)"
    dir_why  = "esperando subida" if act == "BUY" else "esperando bajada"

    # Zona de kill zone
    if kz.get("silver_bullet"):
        kz_name = "Silver Bullet (10:00-11:00 ET) — ventana de máxima precisión ICT"
    elif kz.get("window_a"):
        kz_name = "Ventana A (8:30-9:00 ET) — apertura de mercado NY"
    elif kz.get("window_b"):
        kz_name = "Ventana B (9:30-10:30 ET) — segunda oportunidad de sesión"
    else:
        kz_name = "Kill Zone activa"

    # Noticias
    news_str = "Sin noticias de alto impacto próximas." if not news else \
               f"Próxima noticia: {news.get('name','?')} en {news.get('mins','?')} min."

    # Bias
    bias_map = {"BULLISH": "alcista (favorece LONG)", "BEARISH": "bajista (favorece SHORT)", "NEUTRAL": "neutral"}
    bias_str = bias_map.get(bias, bias)

    # Niveles en puntos NQ (1 punto = $20 NQ)
    stop_pts   = round(sd, 1)
    target_pts = round(sd * rr, 1)

    lines = [
        f"📍 SETUP — {time_str} · {symbol}",
        f"",
        f"Dirección: {dir_str}",
        f"  El detector IFVG encontró un Fair Value Gap violado y retestado {dir_why}.",
        f"  Señal técnica: {reason}",
        f"",
        f"Contexto de mercado:",
        f"  • Kill Zone: {kz_name}",
        f"  • Bias del día: {bias_str}",
        f"  • {news_str}",
        f"",
        f"Niveles de la operación:",
        f"  • Entrada:  {entry:.2f}",
        f"  • Stop:     {sl:.2f}  ({stop_pts:.1f} pts de riesgo, ${risk_usd:.0f})",
        f"  • Target:   {tp:.2f}  ({target_pts:.1f} pts, RR {rr}:1)",
        f"  • Tamaño:   {qty} contrato{'s' if qty>1 else ''}",
        f"",
        f"Reglas aplicadas: kill zone ✓ · bias confirmado ✓ · sin blackout noticias ✓ · 1ª operación del día ✓",
    ]
    return "\n".join(lines)


def _build_outcome_explanation(setup_explanation, exit_price,
                                pnl, result, rr_got, be_triggered, bars_seen):
    """Añade el resultado al final de la explicación del setup."""
    mins_in_trade = bars_seen * 5
    hours = mins_in_trade // 60
    mins  = mins_in_trade % 60
    time_str = f"{hours}h {mins}m" if hours else f"{mins}m"

    if result == "WIN":
        if rr_got >= 1.4:
            outcome_detail = f"✅ TARGET alcanzado a {rr_got:.1f}R. El precio se movió directamente hacia el objetivo sin rebotar."
        else:
            outcome_detail = f"✅ WIN con RR {rr_got:.1f}R."
    else:
        if be_triggered:
            outcome_detail = (f"🔶 BREAKEVEN — El precio llegó a 1R favorable (trigger BE), "
                              f"el stop se movió a entrada+buffer. Luego el mercado revirtió y "
                              f"cerró en pequeña ganancia/pérdida mínima.")
        else:
            outcome_detail = (f"❌ STOP LOSS — El precio no llegó a 1R antes de revertir. "
                              f"Pérdida completa de {rr_got:.1f}R.")

    result_lines = [
        f"",
        f"─" * 40,
        f"📊 RESULTADO — {result}",
        f"",
        f"  Salida: {exit_price:.2f}  |  PnL: {'+'if pnl>=0 else ''}{pnl:.0f}$  |  RR: {rr_got:.2f}",
        f"  Tiempo en trade: {time_str}",
        f"  BE activado: {'Sí' if be_triggered else 'No'}",
        f"",
        f"  {outcome_detail}",
    ]
    return setup_explanation + "\n".join(result_lines)


def _record_paper_outcome(symbol, action, entry, sl, tp, pnl, result, exit_price, rr_got, explanation=""):
    """Persist paper trade result to disk and update daily state."""
    _reset_daily_if_needed()
    DAILY_STATE["pnl"]    = round(DAILY_STATE["pnl"] + pnl, 2)
    DAILY_STATE["trades"] += 1
    if DAILY_STATE["pnl"] <= CIRCUIT_BREAKER_LIMIT and not DAILY_STATE["circuit_breaker"]:
        DAILY_STATE["circuit_breaker"] = True
        print(f"[CIRCUIT BREAKER] PnL diario ${DAILY_STATE['pnl']:.0f} < ${CIRCUIT_BREAKER_LIMIT:.0f} — scanner detenido hoy")

    ACCOUNT["balance"] += pnl
    push_equity()

    # Mirror trade to all prop firm accounts
    _mirror_trade_to_accounts(pnl, result)

    log_event("trade_closed", {
        "symbol": symbol, "pnl": pnl, "rr_achieved": round(rr_got, 2),
        "result": result, "exit": exit_price,
        "balance_after": round(ACCOUNT["balance"], 2),
        "daily_pnl": DAILY_STATE["pnl"],
        "explanation": explanation,
    })

    rec = {
        "date":        DAILY_STATE["date"],
        "ts":          _ts(),
        "symbol":      symbol,
        "action":      action,
        "entry":       entry,
        "sl":          sl,
        "tp":          tp,
        "exit":        exit_price,
        "pnl":         pnl,
        "result":      result,
        "rr":          round(rr_got, 2),
        "daily_pnl":   DAILY_STATE["pnl"],
        "balance":     round(ACCOUNT["balance"], 2),
        "explanation": explanation,
    }
    with open(PAPER_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")

    # Also write human-readable log
    readable_log = Path("paper_trading_readable.txt")
    with open(readable_log, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*60}\n")
        f.write(explanation + "\n")

    print(f"  [PAPER {'WIN ' if pnl>0 else 'LOSS'}] {symbol} ${pnl:+.2f} | día ${DAILY_STATE['pnl']:+.0f} | bal ${ACCOUNT['balance']:,.0f}")
    if explanation:
        print(explanation)

DAILY_BIAS = {"value": "NEUTRAL"}  # BULLISH | NEUTRAL | BEARISH — set from UI

CONFIG = {
    "MAX_RISK_PCT":          0.013,   # 1.3% — optimal: MaxDD=8.48%, +41.8%/2yr, Sharpe=4.17
    "MIN_RR":                2.5,     # RR 2.5 sin BE — OOS best config (PF=1.79)
    "STOP_TICKS":            10,
    "STOP_PCT":              0.4,     # 0.4% stop
    "MAX_TRADES_SESSION":    2,       # max 2 trades/day — OOS+bias validated
    "MAX_DAILY_LOSS_PCT":    0.03,
    "WIN_PROB":              0.60,    # simulation win probability
}

# ── OOS-validated filter config (2yr QQQ 5m, 65 trades, PF=1.79, +41.8%, MaxDD=8.48%) ──
# Cambios finales vs config anterior:
#   skip_weekdays: (0,1) → () — Lun+Mar incluidos, auto-bias controla dirección
#   MIN_RR: 2.0 → 2.5  (sin BE, targets más lejanos)
#   be_trigger_r: 1.5 → 99  (sin BE — BE@cualquierR reduce retorno y Sharpe)
#   MAX_RISK_PCT: 1.5% → 1.3%  (sweet spot: +41.8% retorno, MaxDD 8.48% < 10%)
LIVE_FILTERS = {
    "skip_weekdays":    (),       # sin filtro días — auto-bias controla dirección
    "no_window_b":      False,    # incluir Window B — beneficia en 2yr OOS
    "min_displacement": 21.0,     # FVG creation candle body ≥ 21pts NQ (≡ 0.5 QQQ pts)
    "be_trigger_r":     99,       # sin BE — dejar correr hasta TP (mejor PF y Sharpe)
}

# News calendar loaded lazily from ForexFactory (via news_calendar.py)
_TODAY_EVENTS: list = []   # cached today's events
_TODAY_DATE: str   = ""    # date string of last fetch

def _get_today_events() -> list:
    """Returns today's HIGH-impact USD events, refreshed once per day."""
    global _TODAY_EVENTS, _TODAY_DATE
    today = _now_ny().strftime("%Y-%m-%d")
    if _TODAY_DATE == today:
        return _TODAY_EVENTS
    try:
        from news_calendar import get_today_events
        _TODAY_EVENTS = get_today_events("HIGH")
        _TODAY_DATE   = today
        print(f"[NEWS] {len(_TODAY_EVENTS)} eventos HIGH hoy: {[e['short'] for e in _TODAY_EVENTS]}")
    except Exception as e:
        print(f"[NEWS] Error cargando calendario: {e}")
        _TODAY_EVENTS = []
    return _TODAY_EVENTS



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
    if LIVE_FILTERS.get("no_window_b"):
        win_b = False   # 9:30-10:00 excluido — peor sub-ventana por datos
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
    """Próximo evento HIGH-impact del día. Usa ForexFactory via news_calendar.py."""
    try:
        from news_calendar import next_event_status
        events = _get_today_events()
        status = next_event_status(events)
        if status:
            return {
                "name":    status["name"],
                "mins":    int(status["delta_min"]),
                "blackout":status["blackout"],
                "time_et": status["time_et"],
                "forecast":status.get("forecast",""),
                "previous":status.get("previous",""),
            }
    except Exception:
        pass
    return None

# ── Paper executor — real price outcome tracking ───────────────────────────────
def simulated_executor():
    """Processes signals queue. Registers real paper positions — outcome determined by price."""
    session_count=0
    session_date=None

    while True:
        time.sleep(0.3)
        if not SIGNALS_QUEUE: continue
        signal=SIGNALS_QUEUE.popleft()

        ny=_now_ny(); today=ny.date()
        if session_date!=today:
            session_date=today; session_count=0

        # Circuit breaker check
        _reset_daily_if_needed()
        if DAILY_STATE["circuit_breaker"]:
            log_event("skip",{"reason":f"Circuit breaker activo — PnL día ${DAILY_STATE['pnl']:.0f}","signal":signal}); continue

        # Day-of-week filter: usa LIVE_FILTERS (vacío = opera todos los días, bias controla)
        _wd = ny.weekday()
        _skip_days = LIVE_FILTERS.get("skip_weekdays", ())
        if _skip_days and _wd in _skip_days:
            log_event("skip",{"reason":f"Día filtrado ({ny.strftime('%A')})","signal":signal}); continue

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
            log_event("skip",{"reason":f"Max trades/sesión alcanzado","signal":signal}); continue

        news=next_news()
        if news and news["blackout"]:
            log_event("skip",{"reason":f"Blackout noticias: {news['name']} en {news['mins']}m","signal":signal}); continue

        if ACTIVE_POSITION:
            log_event("skip",{"reason":"Posición ya abierta","signal":signal}); continue

        # Sizing
        entry=signal["close"]; act=signal["action"]
        sd=entry*CONFIG["STOP_PCT"]/100
        rr=CONFIG["MIN_RR"]
        sl=round(entry-sd,4) if act=="BUY" else round(entry+sd,4)
        tp=round(entry+sd*rr,4) if act=="BUY" else round(entry-sd*rr,4)
        qty=max(1,int(ACCOUNT["balance"]*CONFIG["MAX_RISK_PCT"]/(sd or 1)))
        risk_usd=round(sd*qty,2)

        # Build setup explanation
        explanation = _build_trade_explanation(
            signal["symbol"], act, entry, sl, tp, sd, rr, qty, risk_usd,
            bias, kz, news, signal.get("reason", "IFVG retest detectado")
        )
        print(f"\n{explanation}\n")

        ACTIVE_POSITION.update({"symbol":signal["symbol"],"action":act,"qty":qty,
                                 "entry":entry,"sl":sl,"tp":tp,"open_pnl":0.0,"ts":_ts()})
        # Register for real-price outcome tracking
        PAPER_POSITIONS[signal["symbol"]] = {
            "action":act,"entry":entry,"sl":sl,"tp":tp,"qty":qty,
            "sd":sd,"rr":rr,"risk_usd":risk_usd,
            "entry_ts":    int(datetime.now(timezone.utc).timestamp()),
            "be_triggered": False,
            "explanation":  explanation,
        }
        session_count+=1
        log_event("order_placed",{"symbol":signal["symbol"],"action":act,"qty":qty,
            "entry":entry,"sl":sl,"tp":tp,"rr":rr,"risk_usd":risk_usd,
            "reason":signal.get("reason",""),"bias":bias,"kz_silver":kz["silver_bullet"],
            "explanation": explanation})
        print(f"  [ORDER] {act} {qty}x {signal['symbol']} @ {entry:.2f} SL {sl:.2f} TP {tp:.2f} | risk ${risk_usd:.0f}")


def paper_position_tracker():
    """
    Background thread: checks open paper positions against real 5m bars.
    Determines SL/TP hit using same BE-at-1R logic as backtest.
    Runs every 60s. Max tracking: 200 bars (~16h) then closes at market.
    """
    import yfinance as yf
    BE_TRIGGER = LIVE_FILTERS.get("be_trigger_r", 0.5)  # matches backtest config
    BE_BUFFER  = 0.08  # SL → entry + 8% of stop

    while True:
        time.sleep(60)
        if not PAPER_POSITIONS:
            continue

        for sym, pos in list(PAPER_POSITIONS.items()):
            yf_sym = YF_SYMBOLS_DETECT.get(sym, sym)
            try:
                df = yf.Ticker(yf_sym).history(period="2d", interval="5m", auto_adjust=True)
                if df.empty:
                    continue

                entry     = pos["entry"]
                act       = pos["action"]
                qty       = pos["qty"]
                sd        = pos["sd"]
                entry_ts  = pos["entry_ts"]
                sl        = pos["sl"]
                tp        = pos["tp"]
                be_done   = pos["be_triggered"]

                outcome   = None
                bars_seen = 0

                for ts, row in df.iterrows():
                    bar_unix = int(ts.timestamp())
                    if bar_unix <= entry_ts:
                        continue
                    bars_seen += 1
                    h, l = float(row["High"]), float(row["Low"])

                    # Update open_pnl for dashboard
                    mid = (h + l) / 2
                    opnl = round((mid - entry)*qty if act=="BUY" else (entry - mid)*qty, 2)
                    if sym in PAPER_POSITIONS:
                        PAPER_POSITIONS[sym]["open_pnl"] = opnl
                    if ACTIVE_POSITION.get("symbol") == sym:
                        ACTIVE_POSITION["open_pnl"] = opnl

                    # Break-even logic (mirrors backtest)
                    if not be_done:
                        if act=="BUY"  and h >= entry + sd * BE_TRIGGER:
                            sl = entry + sd * BE_BUFFER; be_done = True
                            PAPER_POSITIONS[sym]["sl"] = sl
                            PAPER_POSITIONS[sym]["be_triggered"] = True
                        elif act=="SELL" and l <= entry - sd * BE_TRIGGER:
                            sl = entry - sd * BE_BUFFER; be_done = True
                            PAPER_POSITIONS[sym]["sl"] = sl
                            PAPER_POSITIONS[sym]["be_triggered"] = True

                    # Check SL
                    if act=="BUY"  and l <= sl:
                        exit_price = sl
                        pnl = round((sl - entry) * qty, 2)
                        outcome = ("BE" if be_done else "LOSS", exit_price, pnl)
                        break
                    elif act=="SELL" and h >= sl:
                        exit_price = sl
                        pnl = round((entry - sl) * qty, 2)
                        outcome = ("BE" if be_done else "LOSS", exit_price, pnl)
                        break

                    # Check TP
                    if act=="BUY"  and h >= tp:
                        pnl = round((tp - entry) * qty, 2)
                        outcome = ("WIN", tp, pnl)
                        break
                    elif act=="SELL" and l <= tp:
                        pnl = round((entry - tp) * qty, 2)
                        outcome = ("WIN", tp, pnl)
                        break

                    # Timeout: 200 bars ≈ 16h — close at last price
                    if bars_seen >= 200:
                        exit_price = (h + l) / 2
                        pnl = round((exit_price - entry)*qty if act=="BUY" else (entry - exit_price)*qty, 2)
                        outcome = ("WIN" if pnl > 0 else "LOSS", round(exit_price, 2), pnl)
                        break

                if outcome:
                    result_tag, exit_price, pnl = outcome
                    result   = "WIN" if pnl > 0 else "LOSS"
                    rr_got   = round(abs(pnl) / (sd * qty), 2) if sd * qty > 0 else 0
                    be_done  = pos.get("be_triggered", False)
                    setup_ex = pos.get("explanation", "")
                    full_ex  = _build_outcome_explanation(
                        setup_ex, exit_price, pnl, result, rr_got, be_done, bars_seen
                    )
                    del PAPER_POSITIONS[sym]
                    ACTIVE_POSITION.clear()
                    _record_paper_outcome(sym, act, entry, sl, tp, pnl, result, exit_price, rr_got, full_ex)

            except Exception as e:
                print(f"[PAPER TRACKER] Error {sym}: {e}")

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
            bull_fvgs.append({"top": c0["low"], "bot": c2["high"], "bar": i, "creation_bar": i})

        if c2["low"] > c0["high"]:          # Bearish FVG
            bear_fvgs.append({"top": c2["low"], "bot": c0["high"], "bar": i, "creation_bar": i})

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
                    "creation_bar": fvg["creation_bar"],
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
                    "creation_bar": fvg["creation_bar"],
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
                        "creation_bar": zone.get("creation_bar"),
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
                        "creation_bar": zone.get("creation_bar"),
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


def _15m_structure(yf_sym: str, action: str) -> tuple[bool, str]:
    """
    Confluencia de timeframe superior (15m).
    Verifica que la estructura de las últimas 4 velas de 15m
    coincida con la dirección de la señal de 5m.
    Returns (ok, reason_string).
    """
    try:
        import yfinance as yf
        df = yf.Ticker(yf_sym).history(period="5d", interval="15m", auto_adjust=True)
        if df.empty or len(df) < 5:
            return True, "15m: sin datos (pass)"  # no bloquear si no hay datos

        bars = list(df.iloc[-5:].itertuples())
        highs  = [b.High  for b in bars]
        lows   = [b.Low   for b in bars]
        closes = [b.Close for b in bars]

        # Structure: últimas 3 velas
        hh = highs[-1]  > highs[-2]   # higher high
        hl = lows[-1]   > lows[-2]    # higher low
        lh = highs[-1]  < highs[-2]   # lower high
        ll = lows[-1]   < lows[-2]    # lower low

        # Precio vs midpoint de la vela anterior
        prev_mid = (highs[-2] + lows[-2]) / 2
        above_mid = closes[-1] > prev_mid

        if action == "BUY":
            if (hh or hl) and above_mid:
                return True, f"15m: estructura alcista (HH={hh} HL={hl} > mid={prev_mid:.0f})"
            elif ll and not hl:
                return False, f"15m: estructura bajista — señal BUY contra tendencia"
            else:
                return True, "15m: estructura mixta (pass)"
        else:  # SELL
            if (lh or ll) and not above_mid:
                return True, f"15m: estructura bajista (LH={lh} LL={ll} < mid={prev_mid:.0f})"
            elif hh and not lh:
                return False, f"15m: estructura alcista — señal SELL contra tendencia"
            else:
                return True, "15m: estructura mixta (pass)"
    except Exception as e:
        return True, f"15m: error ({e}) — pass"


def ifvg_scanner():
    """Background thread: scans for IFVGs every ~60s on bar close."""
    import yfinance as yf

    print("[SCANNER] IFVG detector started — watching:", WATCH_SYMBOLS)

    last_processed = {}  # sym → last bar unix timestamp processed
    last_reset_day = None

    while True:
        time.sleep(55)   # ~1 min loop

        # Reset daily counters on new trading day
        today = _now_ny().date()
        if last_reset_day != today:
            DETECTOR_STATE["signals_today"] = 0
            last_reset_day = today

        if not DETECTOR_STATE["enabled"]:
            DETECTOR_STATE["status"] = "paused"
            continue

        # Day-of-week filter: usa LIVE_FILTERS (vacío = todos los días, bias controla dirección)
        _now = _now_ny()
        _skip = LIVE_FILTERS.get("skip_weekdays", ())
        if _skip and _now.weekday() in _skip:
            DETECTOR_STATE["status"] = "idle"
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

                # Displacement filter: FVG creation candle body ≥ min_displacement pts
                min_disp = LIVE_FILTERS.get("min_displacement", 0)
                if min_disp > 0:
                    cb = sig.get("creation_bar")
                    if cb is not None:
                        # creation_bar = índice de c0 (3ª vela del patrón FVG) en el slice de 50
                        # La vela de desplazamiento real es c1 (la del medio, cb-1 en el slice)
                        slice_offset = max(0, len(candles) - 50)
                        abs_c1 = slice_offset + cb - 1   # vela del medio = desplazamiento real
                        if 0 <= abs_c1 < len(candles):
                            c1 = candles[abs_c1]
                            body = abs(c1["close"] - c1.get("open", c1["close"]))
                            if body < min_disp:
                                print(f"[SCANNER] IFVG {action} on {sym} — filtered (displacement {body:.1f}pt < {min_disp}pt)")
                                continue

                # Skip if already have active position
                if ACTIVE_POSITION:
                    print(f"[SCANNER] IFVG {action} on {sym} — filtered (position open)")
                    continue

                # Max 1 trade per day (backtesting shows 67.6% WR vs 56.7% with 2/day)
                if DETECTOR_STATE["signals_today"] >= 1:
                    print(f"[SCANNER] IFVG {action} on {sym} — filtered (max 1 trade/day reached)")
                    continue

                # 15m structure confluence — verifica que el TF superior no esté en contra
                yf_sym_15m = YF_SYMBOLS_DETECT.get(sym, sym)
                ok_15m, reason_15m = _15m_structure(yf_sym_15m, action)
                if not ok_15m:
                    print(f"[SCANNER] IFVG {action} on {sym} — filtered (15m: {reason_15m})")
                    continue
                if reason_15m:
                    reason = reason + f" | {reason_15m}"

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


def morning_bias_scheduler():
    """
    Auto-refresh + auto-apply bias a las 8:25 ET cada día de mercado.
    Corre analyze_bias() (W/D/4H) y aplica automáticamente si conf >= 55%.
    Si conf < 55% → NEUTRAL (no operar ese día).
    El usuario puede sobreescribir manualmente via /api/bias.
    """
    import datetime as _dt
    print("[SCHEDULER] Morning bias scheduler started (8:25 ET daily — auto-apply)")
    last_triggered = None

    while True:
        time.sleep(30)   # check every 30s
        now = _now_ny()
        if now.weekday() >= 5:  # skip weekend
            continue
        today = now.date()
        if last_triggered == today:
            continue
        # Trigger entre 8:15-8:29 ET (15-min window para sobrevivir reinicios del watchdog)
        # last_triggered == today garantiza que solo se ejecuta una vez al día
        if now.hour == 8 and 15 <= now.minute <= 29:
            # last_triggered se marca DENTRO del try para que un error de red
            # permita reintentar cada 30s hasta el cierre de la ventana (8:29).
            # Sin esto: un fallo a las 8:15 marca el día como "hecho" y el bias
            # queda NEUTRAL sin operaciones ni aviso durante todo el día.
            try:
                sym = "^NDX"
                print(f"[SCHEDULER] 8:25 ET — auto-calculando bias W/D/4H...")
                result = analyze_bias(sym)
                BIAS_CACHE["result"] = result
                BIAS_CACHE["ts"] = time.time()
                suggested = result["suggested"]
                conf = result["confidence"]
                last_triggered = today   # marcar solo si analyze_bias() tuvo éxito

                # Auto-apply: si confianza >= 55% aplicar el bias sugerido,
                # si no hay claridad suficiente → NEUTRAL (no operar ese día)
                if conf >= 55:
                    DAILY_BIAS["value"] = suggested
                    print(f"[SCHEDULER] Bias APLICADO automaticamente: {suggested} ({conf:.0f}% conf)")
                    send_telegram(
                        f"*Daily Bias {today}*\n"
                        f"Direccion: *{suggested}* ({conf:.0f}% conf)\n"
                        f"Aplicado automaticamente — puede sobreescribir en /api/bias"
                    )
                else:
                    DAILY_BIAS["value"] = "NEUTRAL"
                    print(f"[SCHEDULER] Conf baja ({conf:.0f}%) → NEUTRAL — no operar hoy")
                    send_telegram(
                        f"*Daily Bias {today}*\n"
                        f"Confianza insuficiente ({conf:.0f}%) → NEUTRAL\n"
                        f"_No se operara hoy salvo override manual_"
                    )
            except Exception as e:
                print(f"[SCHEDULER] Error calculando bias: {e} — reintentando en 30s")


# ── Telegram ─────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN   = "8683889993:AAEe9Va_TCaReMWkg3T4vfBjY6fH2aQSWCs"
TELEGRAM_CHAT_ID = "5631114912"

def send_telegram(msg: str, parse_mode: str = "Markdown") -> bool:
    """Envía un mensaje de Telegram. Retorna True si OK."""
    import urllib.request, urllib.parse
    try:
        body = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": parse_mode}).encode()
        req  = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data=body, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read()).get("ok", False)
    except Exception as e:
        print(f"[TELEGRAM] Error: {e}")
        return False


def _build_daily_report() -> str:
    """Construye el mensaje del reporte diario en Markdown para Telegram."""
    now_ny = _now_ny()
    date_str = now_ny.strftime("%d/%m/%Y")

    # Bias
    bias_result = BIAS_CACHE.get("result") or {}
    suggested   = bias_result.get("suggested", "—")
    score       = bias_result.get("score", 0)
    max_score   = bias_result.get("max_score", 10)
    conf        = bias_result.get("confidence", 0)
    signals_b   = bias_result.get("signals", [])

    bias_icon = {"BULLISH": "📈", "BEARISH": "📉", "NEUTRAL": "➡️"}.get(suggested, "—")

    # Daily state — usar DAILY_STATE (memoria) pero recalcular desde closed_today si bot fue reiniciado
    daily_pnl    = DAILY_STATE.get("pnl", 0.0)
    daily_trades = DAILY_STATE.get("trades", 0)
    cb_active    = DAILY_STATE.get("circuit_breaker", False)
    scanner_sigs = DETECTOR_STATE.get("signals_today", 0)

    # Closed trades today — in-memory first, fallback to disk (sobrevive reinicios)
    today_str    = now_ny.strftime("%Y-%m-%d")
    closed_today = [t for t in TRADES_LOG
                    if t.get("event") == "trade_closed"
                    and t.get("ts", "").startswith(today_str)]
    if not closed_today and PAPER_LOG.exists():
        # Bot reiniciado durante el día: leer PAPER_LOG (disco) y reconstruir lista
        try:
            disk_recs = [json.loads(l) for l in PAPER_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
            closed_today = [
                {"event":"trade_closed","ts":r.get("ts",""),"symbol":r.get("symbol","?"),
                 "pnl":r.get("pnl",0),"rr_achieved":r.get("rr",0),
                 "balance_after":r.get("balance",0),"explanation":r.get("explanation","")}
                for r in disk_recs if r.get("date","") == today_str
            ]
        except Exception:
            pass

    # Si daily_pnl en memoria es 0 pero closed_today tiene trades (bot reiniciado),
    # recalcular desde los trades del día para mantener coherencia en el reporte
    if daily_pnl == 0.0 and closed_today:
        daily_pnl    = round(sum(t.get("pnl", 0) for t in closed_today), 2)
        daily_trades = len(closed_today)

    # Paper trading cumulative
    total_pnl = 0.0; total_t = 0; total_w = 0
    if PAPER_LOG.exists():
        try:
            recs = [json.loads(l) for l in PAPER_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
            total_pnl = round(sum(r["pnl"] for r in recs), 2)
            total_t   = len(recs)
            total_w   = sum(1 for r in recs if r["result"] == "WIN")
        except Exception:
            pass

    wr_cum  = round(total_w / total_t * 100, 1) if total_t else 0
    progress= round(total_pnl / 3000 * 100, 1) if total_pnl > 0 else 0

    # Signals breakdown
    sig_lines = "\n".join(f"  • {s}" for s in signals_b) if signals_b else "  • Sin datos"

    # Trade details today
    if daily_trades > 0:
        trade_lines = ""
        for t in closed_today[-3:]:
            sym    = t.get("symbol","?")
            res    = "✅" if t.get("pnl",0)>0 else "❌"
            pnl_t  = t.get("pnl",0)
            rr_t   = t.get("rr_achieved","?")
            trade_lines += f"\n  {res} {sym} ${pnl_t:+.0f} (RR {rr_t})"
        trades_section = f"*Operaciones:*{trade_lines}"
    else:
        trades_section = "*Operaciones:* Ninguna hoy — sin señales válidas en kill zone"

    cb_line = "⛔ *Circuit breaker activado* — pérdida diaria $800+" if cb_active else ""

    msg = f"""🤖 *IFVG Bot — Informe {date_str}*

{bias_icon} *Bias del día: {suggested}* ({score}/{max_score} pts, {conf:.0f}% confianza)
{sig_lines}

📊 *Sesión de hoy:*
  • Señales detectadas: {scanner_sigs}
  • PnL día: {'+'if daily_pnl>=0 else''}${daily_pnl:.0f}
  • {trades_section}
{cb_line}

📈 *Acumulado paper trading:*
  • Trades: {total_t} | WR: {wr_cum}% | PnL: {'+'if total_pnl>=0 else''}${total_pnl:.0f}
  • Progreso hacia $3k prop target: {progress}%

_Bot activo · Bias auto (W/D/4H) · Todos los días · Ventana A+B+SB · Disp≥21pts · Sin BE (RR 2.5) · Riesgo 1.3% · Max 2/dia · CB $-800_"""

    return msg.strip()


def daily_report_scheduler():
    """
    Envía reporte de fin de día por Telegram a las 16:15 ET (tras cierre de mercado).
    También envía alerta matutina a las 8:20 ET con el bias sugerido.
    """
    print("[TELEGRAM] Daily report scheduler started (8:31 + 16:15 ET)")
    sent_morning = None
    sent_eod     = None

    while True:
        time.sleep(30)
        now = _now_ny()
        if now.weekday() >= 5:  # skip weekend
            continue
        today = now.date()

        # 8:31 ET — alerta matutina con bias (después de que morning_bias_scheduler calcule a las 8:25)
        # sent_morning solo se marca después de envío exitoso para garantizar reintento si falla
        if now.hour == 8 and 31 <= now.minute <= 33 and sent_morning != today:
            try:
                bias_result = BIAS_CACHE.get("result") or {}
                suggested   = bias_result.get("suggested", "calculando...")
                conf        = bias_result.get("confidence", 0)
                icon        = {"BULLISH":"📈","BEARISH":"📉","NEUTRAL":"➡️"}.get(suggested,"—")
                news_today  = _get_today_events()
                news_str    = "\n".join(f"  ⚠️ {e['time_et']} ET — {e['short']}" for e in news_today) \
                              if news_today else "  Sin noticias HIGH impact"
                bias_applied = DAILY_BIAS.get("value", "NEUTRAL")
                if bias_applied == suggested and conf >= 55:
                    estado = f"*APLICADO automaticamente* ✓"
                elif bias_applied == "NEUTRAL" and conf < 55:
                    estado = f"_Confianza baja ({conf:.0f}%) — NEUTRAL, no se opera hoy_"
                else:
                    estado = f"_Override manual: {bias_applied}_"

                msg = f"""{icon} *IFVG Bot — Buenos días {now.strftime('%d/%m')}*

*Bias: {suggested}* ({conf:.0f}% conf) — {estado}
Kill zone activa (8:30-11:00 ET)

*Noticias hoy:*
{news_str}

_Si quieres cambiar: /api/bias en el dashboard_"""
                if send_telegram(msg):
                    print(f"[TELEGRAM] Alerta matutina enviada")
                    sent_morning = today  # solo marcar si Telegram confirmó OK
            except Exception as e:
                print(f"[TELEGRAM] Error alerta matutina: {e}")

        # 16:15 ET — reporte fin de día
        # sent_eod solo se marca después de envío exitoso
        if now.hour == 16 and 14 <= now.minute <= 16 and sent_eod != today:
            try:
                report = _build_daily_report()
                if send_telegram(report):
                    print(f"[TELEGRAM] Reporte diario enviado")
                    sent_eod = today  # solo marcar si Telegram confirmó OK
            except Exception as e:
                print(f"[TELEGRAM] Error reporte EOD: {e}")


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

@app.get("/api/daily-state")
async def daily_state_api():
    _reset_daily_if_needed()
    return {**DAILY_STATE, "circuit_breaker_limit": CIRCUIT_BREAKER_LIMIT}

@app.get("/api/accounts")
async def accounts_api():
    """Estado de las 4 cuentas de fondeo."""
    result = []
    for acc in PROP_ACCOUNTS:
        profit     = acc["balance"] - acc["start"]
        profit_pct = profit / acc["start"] * 100
        dd_pct     = (acc["peak"] - acc["balance"]) / acc["peak"] * 100 if acc["peak"] > 0 else 0
        wr         = round(acc["wins"] / acc["trades"] * 100, 1) if acc["trades"] else 0
        to_target  = acc["profit_target"] - profit
        result.append({
            "id":           acc["id"],
            "name":         acc["name"],
            "firm":         acc["firm"],
            "balance":      round(acc["balance"], 2),
            "profit":       round(profit, 2),
            "profit_pct":   round(profit_pct, 2),
            "dd_pct":       round(dd_pct, 2),
            "max_dd_pct":   acc["max_dd_pct"],
            "daily_pnl":    acc["daily_pnl"],
            "trades":       acc["trades"],
            "wins":         acc["wins"],
            "losses":       acc["losses"],
            "wr":           wr,
            "status":       acc["status"],
            "to_target":    round(max(to_target, 0), 2),
            "target_pct":   round(min(profit / acc["profit_target"] * 100, 100), 1) if acc["profit_target"] > 0 else 0,
            "start_date":   acc["start_date"],
        })
    total_profit = sum(a["balance"] - a["start"] for a in PROP_ACCOUNTS)
    passed       = sum(1 for a in PROP_ACCOUNTS if a["status"] == "PASSED")
    failed       = sum(1 for a in PROP_ACCOUNTS if a["status"] == "FAILED")
    return {"accounts": result, "total_profit": round(total_profit, 2),
            "passed": passed, "failed": failed, "active": len(PROP_ACCOUNTS) - failed}

@app.post("/api/accounts/reset")
async def accounts_reset_api():
    """Resetea todas las cuentas a $50k (para nuevo ciclo de evaluación)."""
    today = _now_ny().strftime("%Y-%m-%d")
    for acc in PROP_ACCOUNTS:
        acc.update({"balance": acc["start"], "peak": acc["start"],
                    "daily_pnl": 0.0, "daily_date": today,
                    "trades": 0, "wins": 0, "losses": 0,
                    "status": "EVAL", "start_date": today})
    return {"ok": True, "message": "4 cuentas reseteadas a estado EVAL"}

@app.post("/api/accounts/{account_id}/rename")
async def account_rename_api(account_id: int, body: dict):
    """Renombra una cuenta (nombre, firma)."""
    for acc in PROP_ACCOUNTS:
        if acc["id"] == account_id:
            if "name" in body: acc["name"] = body["name"]
            if "firm" in body: acc["firm"] = body["firm"]
            return {"ok": True}
    return {"ok": False, "error": "Account not found"}

@app.get("/api/paper-report")
async def paper_report_api():
    """Returns daily P&L summary for the paper trading period."""
    if not PAPER_LOG.exists():
        return {"days": [], "total_trades": 0, "total_pnl": 0.0, "win_rate": 0}
    try:
        trades = [json.loads(l) for l in PAPER_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    except Exception:
        return {"days": [], "error": "No se pudo leer el log"}

    from collections import defaultdict
    by_day: dict = defaultdict(list)
    for t in trades:
        by_day[t["date"]].append(t)

    days = []
    for date in sorted(by_day.keys()):
        ts = by_day[date]
        wins   = [t for t in ts if t["result"] == "WIN"]
        losses = [t for t in ts if t["result"] == "LOSS"]
        pnl    = round(sum(t["pnl"] for t in ts), 2)
        days.append({
            "date":   date,
            "trades": len(ts),
            "wins":   len(wins),
            "losses": len(losses),
            "pnl":    pnl,
            "wr":     round(len(wins)/len(ts)*100, 1) if ts else 0,
        })

    total_pnl = round(sum(d["pnl"] for d in days), 2)
    total_t   = sum(d["trades"] for d in days)
    total_w   = sum(d["wins"]   for d in days)
    return {
        "days":         days,
        "total_trades": total_t,
        "total_wins":   total_w,
        "total_pnl":    total_pnl,
        "win_rate":     round(total_w / total_t * 100, 1) if total_t else 0,
        "target_pnl":   3000.0,   # prop firm $50k target
        "progress_pct": round(total_pnl / 3000 * 100, 1) if total_pnl > 0 else 0,
    }

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

@app.get("/api/backtest")
async def run_backtest(symbol:str="NQ1!", days:int=60, rr:float=2.0, stop_pct:float=0.5, bias:str="BOTH"):
    """Run backtest from dashboard — returns metrics + last 20 trades."""
    import subprocess, sys
    try:
        result = subprocess.run(
            [sys.executable, "backtest.py",
             "--symbol", symbol, "--days", str(days),
             "--rr", str(rr), "--stop-pct", str(stop_pct),
             "--bias", bias,
             "--json"],
            capture_output=True, text=True, timeout=120,
            cwd=str(Path(__file__).parent),
            encoding="utf-8", errors="replace",
        )
        if result.returncode != 0:
            return {"error": result.stderr[-500:] if result.stderr else "backtest failed"}
        # Extract JSON — use raw_decode to stop at first complete object
        idx = result.stdout.find('{')
        if idx >= 0:
            try:
                data, _ = json.JSONDecoder().raw_decode(result.stdout, idx)
                if "trades" in data:
                    data["trades"] = data["trades"][-20:]
                return data
            except Exception as e:
                return {"error": f"JSON parse: {e}", "stdout": result.stdout[-300:]}
        return {"error": "no JSON in output", "stdout": result.stdout[-300:]}
    except subprocess.TimeoutExpired:
        return {"error": "timeout (>120s) — reduce --days"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/news")
async def news_today():
    """Today's HIGH-impact economic events from ForexFactory."""
    try:
        from news_calendar import get_today_events, get_week_events, next_event_status
        today  = get_today_events("HIGH")
        status = next_event_status(today)
        return {"today": today, "next": status, "blackout": status["blackout"] if status else False}
    except Exception as e:
        return {"today": [], "next": None, "blackout": False, "error": str(e)}

OPTIMIZE_STATE = {"running": False, "last_result": None, "last_run": None}

@app.get("/api/optimize")
async def get_optimize():
    return OPTIMIZE_STATE

@app.post("/api/optimize")
async def run_optimize(symbol:str="NQ1!", days:int=60, apply:bool=False):
    """Launch parameter optimizer in background thread. Returns immediately."""
    if OPTIMIZE_STATE["running"]:
        return {"status": "already running"}

    # Reset stale result so UI shows fresh state; set running BEFORE thread to avoid race
    OPTIMIZE_STATE["last_result"] = None
    OPTIMIZE_STATE["last_run"] = None
    OPTIMIZE_STATE["running"] = True

    def _run():
        import subprocess, sys, re
        try:
            cmd = [sys.executable, "optimize.py",
                   "--symbol", symbol, "--days", str(days), "--json"]
            if apply:
                cmd.append("--apply")
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=600,
                cwd=str(Path(__file__).parent), encoding="utf-8", errors="replace",
            )
            idx = result.stdout.find('{')
            data = {}
            if idx >= 0:
                try:
                    data, _ = json.JSONDecoder().raw_decode(result.stdout, idx)
                except Exception:
                    pass
            if data:
                OPTIMIZE_STATE["last_result"] = data.get("best")
                # Auto-apply best params to live CONFIG
                if apply and data.get("best"):
                    b = data["best"]
                    CONFIG["STOP_PCT"] = b["stop_pct"]
                    CONFIG["MIN_RR"]   = b["rr"]
                    print(f"[OPTIMIZE] Applied: STOP_PCT={b['stop_pct']} MIN_RR={b['rr']} score={b['score']}")
        except Exception as e:
            OPTIMIZE_STATE["last_result"] = {"error": str(e)}
        finally:
            OPTIMIZE_STATE["running"] = False
            OPTIMIZE_STATE["last_run"] = _ts()

    threading.Thread(target=_run, daemon=True).start()
    return {"status": "started", "symbol": symbol, "days": days}

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

@app.post("/api/send-report")
async def send_report_now():
    """Fuerza el envío del reporte diario ahora (para testing)."""
    try:
        report = _build_daily_report()
        ok = send_telegram(report)
        return {"sent": ok, "preview": report[:300]+"..."}
    except Exception as e:
        return {"sent": False, "error": str(e)}

@app.post("/api/reset")
async def reset():
    TRADES_LOG.clear(); EQUITY_CURVE.clear(); SIGNALS_QUEUE.clear()
    ACTIVE_POSITION.clear(); PAPER_POSITIONS.clear()
    ACCOUNT.update({"balance":ACCOUNT["start"],"peak":ACCOUNT["start"]})
    DAILY_BIAS["value"]="NEUTRAL"
    DETECTOR_STATE.update({"signals_today":0,"last_signal":None})
    DAILY_STATE.update({"date":"","pnl":0.0,"trades":0,"circuit_breaker":False})
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

/* ── Mobile responsive ────────────────────────────────────────────── */
@media (max-width:768px){
  body{overflow-y:auto;overflow-x:hidden;height:auto}

  /* Header compacto en 2 filas */
  .hdr{flex-wrap:wrap;gap:5px;padding:8px 10px;min-height:auto}
  .hdr h1{font-size:14px}
  .hdr-right{margin-left:auto}
  .et{font-size:11px}

  /* Symbar: scroll horizontal, ocultar texto largo */
  .symbar{overflow-x:auto;-webkit-overflow-scrolling:touch;padding:6px 10px;gap:5px}
  .symbar>span:last-child{display:none}
  .symbar select{max-width:130px}
  .sep{display:none}

  /* Layout principal: apilado vertical */
  .main{flex-direction:column;flex:none}
  .chart-col{border-right:none;border-bottom:1px solid var(--border);flex:none}

  /* Chart más pequeño en móvil */
  #tv-container{height:220px}

  /* Equity mini más compacto */
  .equity-bar{height:60px;padding:5px 10px}
  #eq-canvas{height:30px}

  /* Sidebar ocupa todo el ancho */
  .sidebar{width:100%;overflow-y:visible;max-height:none}

  /* Panels: padding más cómodo para touch */
  .panel{padding:12px 12px}
  .panel-title{margin-bottom:8px}

  /* Botones touch-friendly */
  .btn-long,.btn-short{padding:14px;font-size:14px}
  .bias-btn{padding:10px 4px;font-size:12px}
  .btn-reset{padding:6px 12px;font-size:12px}

  /* Inputs más grandes para touch */
  .rc-input,.cfg-input,.sig-sel{padding:8px;font-size:13px}
  .rc-input:focus,.cfg-input:focus{font-size:16px} /* evita zoom automático iOS */

  /* Métricas: grid 2 cols (ya lo es, pero ajustar tamaños) */
  .m-val{font-size:18px}
  .metrics-grid{gap:8px}
  .m-card{padding:10px 12px}

  /* Risk calc: 2 cols siguen bien */
  .rc-grid{gap:8px}
  .rc-result{padding:10px 12px;gap:6px}
  .rc-r-val{font-size:16px}

  /* Trade log: scroll horizontal en tabla */
  .log-wrap{overflow-x:auto}
  .log-table{min-width:560px}
  .log-table td{padding:6px 12px}

  /* Config rows */
  .cfg-row{gap:6px}
  .cfg-label{font-size:12px}
  .cfg-input{width:80px;font-size:13px}

  /* Scanner / backtest */
  #scanner-info,#scanner-windows{font-size:11px}
  #bt-result{font-size:11px}

  /* Pos card */
  .pos-pnl{font-size:20px}
  .pos-sym{font-size:15px}
}

/* Pantallas muy pequeñas (< 380px) */
@media (max-width:380px){
  .hdr h1{font-size:13px}
  .badge{font-size:9px;padding:2px 6px}
  #tv-container{height:180px}
  .m-val{font-size:15px}
}
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

    <!-- News Calendar -->
    <div class="panel">
      <div class="panel-title">
        <span>Noticias Hoy</span>
        <span style="color:var(--text2);font-size:10px">ForexFactory</span>
      </div>
      <div id="news-list" style="font-size:10px;line-height:1.9;color:var(--text2)">
        Cargando calendario...
      </div>
    </div>

    <!-- Backtest -->
    <div class="panel">
      <div class="panel-title">
        <span>Backtest</span>
        <span id="bt-status" style="font-size:10px;color:var(--text2)">listo</span>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-bottom:6px">
        <div>
          <div style="font-size:9px;color:var(--text2);margin-bottom:2px">Stop %</div>
          <input id="bt-stop" type="number" value="0.5" step="0.1" min="0.1" max="2"
            style="width:100%;background:var(--bg3);border:1px solid var(--border);color:var(--text1);
                   padding:4px;border-radius:3px;font-size:10px;font-family:inherit">
        </div>
        <div>
          <div style="font-size:9px;color:var(--text2);margin-bottom:2px">RR</div>
          <input id="bt-rr" type="number" value="2.0" step="0.5" min="1" max="5"
            style="width:100%;background:var(--bg3);border:1px solid var(--border);color:var(--text1);
                   padding:4px;border-radius:3px;font-size:10px;font-family:inherit">
        </div>
        <div>
          <div style="font-size:9px;color:var(--text2);margin-bottom:2px">Dias</div>
          <input id="bt-days" type="number" value="60" step="10" min="10" max="730"
            style="width:100%;background:var(--bg3);border:1px solid var(--border);color:var(--text1);
                   padding:4px;border-radius:3px;font-size:10px;font-family:inherit">
        </div>
        <div>
          <div style="font-size:9px;color:var(--text2);margin-bottom:2px">Bias</div>
          <select id="bt-bias"
            style="width:100%;background:var(--bg3);border:1px solid var(--border);color:var(--text1);
                   padding:4px;border-radius:3px;font-size:10px;font-family:inherit">
            <option value="BOTH">BOTH</option>
            <option value="BULLISH">BULLISH</option>
            <option value="BEARISH">BEARISH</option>
          </select>
        </div>
      </div>
      <button onclick="runBacktest()"
        style="width:100%;background:#1a2a3a;border:1px solid #2a6aaa;color:#6aadee;
               padding:6px;border-radius:4px;cursor:pointer;font-size:10px;font-family:inherit;font-weight:bold">
        Correr Backtest + Self-Improve
      </button>
      <div id="bt-result" style="font-size:10px;color:var(--text2);margin-top:8px;min-height:40px;line-height:1.7"></div>
    </div>

    <!-- Self-Improve Optimizer -->
    <div class="panel">
      <div class="panel-title">
        <span>Self-Improve</span>
        <span id="opt-status" style="font-size:10px;color:var(--text2)">listo</span>
      </div>
      <div style="font-size:10px;color:var(--text2);margin-bottom:8px">
        Testea 24 combinaciones de params y aplica la mejor configuracion.
        <span style="color:var(--yellow)"> Se lanza automaticamente tras cada backtest.</span>
      </div>
      <div style="display:flex;gap:6px">
        <button onclick="runOptimize(false)"
          style="flex:1;background:var(--bg3);border:1px solid var(--border);color:var(--text2);
                 padding:6px;border-radius:4px;cursor:pointer;font-size:10px;font-family:inherit">
          Solo analizar
        </button>
        <button onclick="runOptimize(true)"
          style="flex:1;background:#1a3a1a;border:1px solid var(--green);color:var(--green);
                 padding:6px;border-radius:4px;cursor:pointer;font-size:10px;font-family:inherit">
          Analizar + Aplicar
        </button>
      </div>
      <div id="opt-result" style="font-size:10px;color:var(--text2);margin-top:8px;min-height:32px"></div>
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

    <!-- Circuit Breaker + Daily P&L -->
    <div class="panel" id="cb-panel">
      <div class="panel-title">
        <span>Hoy</span>
        <span id="cb-badge" style="font-size:10px;padding:2px 8px;border-radius:8px;background:#222;color:var(--text2);border:1px solid var(--border)">ACTIVO</span>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:6px">
        <div class="m-card">
          <div class="m-label">PnL hoy</div>
          <div class="m-val" id="cb-pnl">$0</div>
          <div class="m-sub">límite $-800</div>
        </div>
        <div class="m-card">
          <div class="m-label">Trades hoy</div>
          <div class="m-val" id="cb-trades">0</div>
          <div class="m-sub">max 1/día</div>
        </div>
      </div>
      <div id="cb-msg" style="font-size:10px;color:var(--text2)">Scanner activo — circuit breaker en $-800</div>
      <div style="margin-top:6px;padding:5px 7px;background:#0d1a0d;border:1px solid #1a3a1a;border-radius:5px;font-size:9px;color:#4caf50;line-height:1.6">
        <b>Filtros OOS validados (2yr, PF=1.24, MaxDD=7.8%):</b><br>
        ✓ Todos los días &nbsp;·&nbsp; ✓ Ventana A+B+SB &nbsp;·&nbsp; ✓ Desplazamiento ≥21pts &nbsp;·&nbsp; ✓ Sin BE (RR 2.5) &nbsp;·&nbsp; ✓ Riesgo 1.3%
      </div>
    </div>

    <!-- Multi-Account Prop Firm Tracker -->
    <div class="panel">
      <div class="panel-title">
        <span>Cuentas de Fondeo</span>
        <span style="font-size:10px;color:var(--text2)" id="acc-summary">4 activas</span>
      </div>
      <!-- Total profit bar -->
      <div style="margin-bottom:8px">
        <div style="display:flex;justify-content:space-between;font-size:10px;color:var(--text2);margin-bottom:3px">
          <span>Profit total (4 cuentas)</span>
          <span id="acc-total-pnl" style="color:var(--green)">$0</span>
        </div>
        <div style="background:var(--bg3);border-radius:3px;height:5px;overflow:hidden">
          <div id="acc-total-bar" style="height:100%;background:var(--green);width:0%;border-radius:3px;transition:width .5s"></div>
        </div>
        <div style="font-size:9px;color:var(--text2);text-align:right;margin-top:2px">target: $20,000 (4×$5k)</div>
      </div>
      <!-- Account grid 2×2 -->
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px" id="acc-grid">
        <!-- Filled by JS -->
      </div>
    </div>

    <!-- Paper Trading — histórico -->
    <div class="panel">
      <div class="panel-title">
        <span>Paper Trading</span>
        <span style="font-size:10px;color:var(--text2)" id="pt-period">—</span>
      </div>
      <!-- Progress bar hacia $3k target -->
      <div style="margin-bottom:8px">
        <div style="display:flex;justify-content:space-between;font-size:10px;color:var(--text2);margin-bottom:3px">
          <span>Progreso hacia $3k (prop target)</span>
          <span id="pt-pct">0%</span>
        </div>
        <div style="background:var(--bg3);border-radius:3px;height:6px;overflow:hidden">
          <div id="pt-bar" style="height:100%;background:var(--green);width:0%;border-radius:3px;transition:width .5s"></div>
        </div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:4px;margin-bottom:8px">
        <div class="m-card" style="padding:6px 8px">
          <div class="m-label">PnL total</div>
          <div class="m-val" id="pt-pnl" style="font-size:14px">$0</div>
        </div>
        <div class="m-card" style="padding:6px 8px">
          <div class="m-label">Win Rate</div>
          <div class="m-val" id="pt-wr" style="font-size:14px">—</div>
        </div>
        <div class="m-card" style="padding:6px 8px">
          <div class="m-label">Trades</div>
          <div class="m-val" id="pt-trades" style="font-size:14px">0</div>
        </div>
      </div>
      <!-- Daily table -->
      <div style="overflow-x:auto">
        <table style="width:100%;border-collapse:collapse;font-size:10px" id="pt-table">
          <thead>
            <tr style="color:var(--text2);border-bottom:1px solid var(--border)">
              <td style="padding:3px 4px">Fecha</td>
              <td style="padding:3px 4px;text-align:center">Trades</td>
              <td style="padding:3px 4px;text-align:center">WR%</td>
              <td style="padding:3px 4px;text-align:right">PnL</td>
            </tr>
          </thead>
          <tbody id="pt-body">
            <tr><td colspan="4" style="color:var(--text2);padding:8px 4px;text-align:center">Sin datos aún — empezando hoy</td></tr>
          </tbody>
        </table>
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
  setTimeout(()=>loadBiasSuggestion(),1500);
  setTimeout(()=>loadNews(),2000);
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

// ── News calendar ─────────────────────────────────────────────────────────────
async function loadNews(){
  try{
    const d=await fetch("/api/news").then(r=>r.json());
    const el=document.getElementById("news-list");
    if(!d.today||d.today.length===0){
      el.innerHTML='<span style="color:#555">Sin eventos HIGH impact hoy</span>';
      return;
    }
    el.innerHTML=d.today.map(ev=>{
      const isNext=d.next&&d.next.name===ev.short;
      const bk=d.blackout&&isNext;
      const col=bk?"var(--red)":isNext?"var(--yellow)":"var(--text2)";
      const tag=bk?' <span style="color:var(--red)">[BLACKOUT]</span>':
                 isNext?' <span style="color:var(--yellow)">[PROXIMO]</span>':"";
      return `<div style="color:${col}">${ev.time_et} ET &nbsp;<b>${ev.short}</b>&nbsp;
        prev=${ev.previous||"—"} fcst=${ev.forecast||"—"}${tag}</div>`;
    }).join("");
  }catch(e){
    const el=document.getElementById("news-list");
    if(el) el.innerHTML='<span style="color:#555">Sin conexion a ForexFactory</span>';
  }
}

// ── Backtest ──────────────────────────────────────────────────────────────────
async function runBacktest(){
  const sym=(document.getElementById("sym-sel")||{}).value||"NQ1!";
  const stop=document.getElementById("bt-stop").value||"0.5";
  const rr=document.getElementById("bt-rr").value||"2.0";
  const days=document.getElementById("bt-days").value||"60";
  const bias=document.getElementById("bt-bias").value||"BOTH";
  const btStatus=document.getElementById("bt-status");
  const btResult=document.getElementById("bt-result");
  btStatus.textContent="corriendo...";
  btStatus.style.color="var(--yellow)";
  btResult.innerHTML='<span style="color:var(--yellow)">Descargando datos y detectando IFVGs...</span>';
  try{
    const url=`/api/backtest?symbol=${encodeURIComponent(sym)}&days=${days}&rr=${rr}&stop_pct=${stop}&bias=${bias}`;
    const d=await fetch(url).then(r=>r.json());
    if(d.error){
      btResult.innerHTML=`<span style="color:var(--red)">Error: ${d.error}</span>`;
      btStatus.textContent="error"; btStatus.style.color="var(--red)";
      return;
    }
    const m=d.metrics||{};
    const wr=((m.win_rate||0)*100).toFixed(1);
    const pf=(m.profit_factor||0).toFixed(2);
    const dd=(m.max_drawdown_pct||0).toFixed(1);
    const ret=(m.return_pct||0).toFixed(1);
    const n=m.trades_taken||0;
    const wrColor=parseFloat(wr)>=45?"var(--green)":parseFloat(wr)>=30?"var(--yellow)":"var(--red)";
    btResult.innerHTML=`
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:2px 10px">
        <div>WR: <b style="color:${wrColor}">${wr}%</b></div>
        <div>PF: <b style="color:${parseFloat(pf)>=1.5?"var(--green)":"var(--yellow)"}">${pf}</b></div>
        <div>DD: <b style="color:${parseFloat(dd)>15?"var(--red)":"var(--text1)"}">${dd}%</b></div>
        <div>Return: <b style="color:${parseFloat(ret)>0?"var(--green)":"var(--red)"}">${ret>0?"+":""}${ret}%</b></div>
        <div>Trades: <b>${n}</b></div>
      </div>
      <div style="color:var(--yellow);margin-top:6px">Lanzando Self-Improve...</div>`;
    btStatus.textContent="listo "+new Date().toLocaleTimeString("es");
    btStatus.style.color="var(--text2)";
    // Auto-launch optimizer with apply=true after backtest
    setTimeout(()=>runOptimize(true), 500);
  }catch(e){
    btResult.innerHTML=`<span style="color:var(--red)">Error: ${e.message}</span>`;
    btStatus.textContent="error"; btStatus.style.color="var(--red)";
  }
}

// ── Self-Improve Optimizer ────────────────────────────────────────────────────
let optimizePolling=null;
async function runOptimize(apply){
  const sym=(document.getElementById("sym-sel")||{}).value||"NQ1!";
  const res=await fetch(`/api/optimize?symbol=${sym}&days=60&apply=${apply}`,{method:"POST"}).then(r=>r.json());
  document.getElementById("opt-status").textContent="corriendo...";
  document.getElementById("opt-result").textContent="Testando 24 configuraciones (~3-5 min)...";
  // Poll for result
  if(optimizePolling) clearInterval(optimizePolling);
  optimizePolling=setInterval(async()=>{
    const st=await fetch("/api/optimize").then(r=>r.json());
    // Animate dots while running
    if(st.running){
      const dots=".".repeat((Math.floor(Date.now()/800)%3)+1);
      document.getElementById("opt-status").textContent="corriendo"+dots;
      return;
    }
    // Guard: keep polling if still running OR if run hasn't started yet (last_result=null, last_run=null)
    if(st.running || (!st.last_run && !st.last_result)) return;
    clearInterval(optimizePolling); optimizePolling=null;
    const timeStr=new Date(st.last_run||Date.now()).toLocaleTimeString("es");
    const r=st.last_result;
    if(r&&r.score){
      const m=r.metrics||{};
      const wr=((m.win_rate||0)*100).toFixed(1);
      const wrColor=parseFloat(wr)>=45?"var(--green)":parseFloat(wr)>=30?"var(--yellow)":"var(--red)";
      document.getElementById("opt-status").textContent="listo "+timeStr;
      document.getElementById("opt-status").style.color="var(--green)";
      document.getElementById("opt-result").innerHTML=
        `<div style="border:1px solid var(--green);border-radius:4px;padding:6px;background:#0a1a0a">
           <div style="color:var(--green);font-weight:bold;margin-bottom:4px">MEJOR CONFIG — ${timeStr}</div>
           <div>Stop: <b>${r.stop_pct}%</b> &nbsp; RR: <b>${r.rr}</b> &nbsp; Score: <b>${r.score}</b></div>
           <div>WR: <b style="color:${wrColor}">${wr}%</b> &nbsp; PF: <b>${(m.profit_factor||0).toFixed(2)}</b> &nbsp; DD: <b>${(m.max_drawdown_pct||0).toFixed(1)}%</b></div>
           ${apply?'<div style="color:var(--green);margin-top:4px">Aplicado al bot. Actualizando backtest...</div>':''}
         </div>`;
      // Flash the panel border
      const panel=document.getElementById("opt-result").closest(".panel");
      if(panel){ panel.style.boxShadow="0 0 12px var(--green)"; setTimeout(()=>panel.style.boxShadow="",4000); }
      // Update backtest inputs with optimized params and re-run to confirm WR
      if(apply){
        document.getElementById("bt-stop").value=r.stop_pct;
        document.getElementById("bt-rr").value=r.rr;
        setTimeout(async()=>{
          const sym=(document.getElementById("sym-sel")||{}).value||"NQ1!";
          const days=document.getElementById("bt-days").value||"60";
          const bias=document.getElementById("bt-bias").value||"BOTH";
          const btResult=document.getElementById("bt-result");
          btResult.innerHTML='<span style="color:var(--yellow)">Confirmando WR con params optimizados...</span>';
          try{
            const d=await fetch(`/api/backtest?symbol=${encodeURIComponent(sym)}&days=${days}&rr=${r.rr}&stop_pct=${r.stop_pct}&bias=${bias}`).then(x=>x.json());
            const mm=d.metrics||{};
            const ww=((mm.win_rate||0)*100).toFixed(1);
            const wc=parseFloat(ww)>=45?"var(--green)":parseFloat(ww)>=30?"var(--yellow)":"var(--red)";
            btResult.innerHTML=`
              <div style="font-size:9px;color:var(--text2);margin-bottom:3px">Con params optimizados (stop=${r.stop_pct}% RR=${r.rr}):</div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:2px 10px">
                <div>WR: <b style="color:${wc}">${ww}%</b></div>
                <div>PF: <b>${(mm.profit_factor||0).toFixed(2)}</b></div>
                <div>DD: <b>${(mm.max_drawdown_pct||0).toFixed(1)}%</b></div>
                <div>Return: <b style="color:${(mm.return_pct||0)>0?"var(--green)":"var(--red)"}">${(mm.return_pct||0)>0?"+":""}${(mm.return_pct||0).toFixed(1)}%</b></div>
              </div>`;
          }catch(e){}
        },1000);
      }
    } else {
      document.getElementById("opt-status").textContent="sin resultados "+timeStr;
      document.getElementById("opt-status").style.color="var(--red)";
      document.getElementById("opt-result").textContent=r?.error||"Ninguna combinacion paso los constraints. Prueba mas dias.";
    }
  },3000);
}

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

function toggleEx(id){
  const el=document.getElementById(id);
  if(el) el.style.display=el.style.display==="none"?"table-row":"none";
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
      const rows=t.trades.slice().reverse().map((ev,i)=>{
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
          const pnlStr=`<span style="color:${c}">${ev.pnl>0?"+":""}$${(ev.pnl||0).toFixed(2)}</span>`;
          const explId=`ex-${i}`;
          const hasEx=ev.explanation&&ev.explanation.length>0;
          const exBtn=hasEx?`<button onclick="toggleEx('${explId}')"
            style="margin-left:6px;background:var(--bg3);border:1px solid var(--border);color:var(--text2);
                   padding:1px 6px;border-radius:3px;font-size:9px;cursor:pointer;font-family:inherit">
            📋 análisis</button>`:"";
          detail=`${pnlStr} · RR ${ev.rr_achieved} · Bal $${(ev.balance_after||0).toLocaleString("es",{maximumFractionDigits:0})}${exBtn}`;
          if(hasEx){
            const escaped=ev.explanation.replace(/</g,"&lt;").replace(/>/g,"&gt;");
            return `<tr><td style="color:var(--text2);white-space:nowrap">${tsStr}</td><td>${badge}</td><td>${sym}</td><td>${side}</td>
              <td style="color:var(--text2);max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${detail}</td></tr>
              <tr id="${explId}" style="display:none"><td colspan="5" style="padding:0">
                <pre style="background:var(--bg3);border-left:3px solid ${c};margin:0;padding:10px 14px;
                     font-size:10px;line-height:1.6;white-space:pre-wrap;color:var(--text2);overflow-x:auto">${escaped}</pre>
              </td></tr>`;
          }
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

// ── Circuit breaker + Daily state ─────────────────────────────────────────────
async function refreshDaily(){
  try{
    const [ds, pr] = await Promise.all([
      fetch("/api/daily-state").then(r=>r.json()),
      fetch("/api/paper-report").then(r=>r.json()),
    ]);

    // Circuit breaker panel
    const pnl = ds.pnl||0;
    const cb  = ds.circuit_breaker;
    document.getElementById("cb-pnl").textContent = (pnl>=0?"+":"")+"$"+pnl.toFixed(0);
    document.getElementById("cb-pnl").style.color  = pnl>=0?"var(--green)":pnl<-400?"var(--red)":"var(--yellow)";
    document.getElementById("cb-trades").textContent = ds.trades||0;
    const badge = document.getElementById("cb-badge");
    const msg   = document.getElementById("cb-msg");
    if(cb){
      badge.textContent="DETENIDO"; badge.style.background="#3a1a1a"; badge.style.color="var(--red)"; badge.style.borderColor="#da3633";
      msg.textContent="⛔ Circuit breaker activo — límite $-800 alcanzado. Reanuda mañana.";
      msg.style.color="var(--red)";
    } else {
      badge.textContent="ACTIVO"; badge.style.background="#1a2e1a"; badge.style.color="var(--green)"; badge.style.borderColor="#2ea043";
      const rem = Math.abs(ds.circuit_breaker_limit||800) + pnl;
      msg.textContent=`Scanner activo · Margen hasta circuit breaker: $${rem.toFixed(0)}`;
      msg.style.color="var(--text2)";
    }

    // Paper trading report
    if(pr.days && pr.days.length>0){
      document.getElementById("pt-pnl").textContent   = (pr.total_pnl>=0?"+":"")+"$"+pr.total_pnl.toFixed(0);
      document.getElementById("pt-pnl").style.color   = pr.total_pnl>=0?"var(--green)":"var(--red)";
      document.getElementById("pt-wr").textContent    = pr.win_rate+"%";
      document.getElementById("pt-wr").style.color    = pr.win_rate>=60?"var(--green)":pr.win_rate>=50?"var(--yellow)":"var(--red)";
      document.getElementById("pt-trades").textContent= pr.total_trades;
      const pct = Math.min(100, pr.progress_pct||0);
      document.getElementById("pt-bar").style.width   = pct+"%";
      document.getElementById("pt-pct").textContent   = pct.toFixed(1)+"%";
      document.getElementById("pt-period").textContent= pr.days.length+" días";
      const tbody = document.getElementById("pt-body");
      tbody.innerHTML = pr.days.slice().reverse().slice(0,14).map(d=>{
        const c = d.pnl>=0?"var(--green)":"var(--red)";
        return `<tr style="border-top:1px solid var(--border2)">
          <td style="padding:3px 4px;color:var(--text2)">${d.date.slice(5)}</td>
          <td style="padding:3px 4px;text-align:center">${d.trades}</td>
          <td style="padding:3px 4px;text-align:center;color:${d.wr>=60?"var(--green)":d.wr>=50?"var(--yellow)":"var(--red)"}">${d.wr}%</td>
          <td style="padding:3px 4px;text-align:right;color:${c};font-weight:600">${d.pnl>=0?"+":""}$${d.pnl.toFixed(0)}</td>
        </tr>`;
      }).join("");
    }
  }catch(e){ console.warn("refreshDaily",e); }
}

// ── Multi-account prop firm tracker ───────────────────────────────────────────
const STATUS_META = {
  EVAL:   {label:"EVAL",   bg:"#1a2a1a", color:"#4caf50", border:"#1a3a1a"},
  PASSED: {label:"✅ APROBADA", bg:"#0d2a0d", color:"#69f569", border:"#1a6a1a"},
  FAILED: {label:"❌ ELIMINADA", bg:"#2a0d0d", color:"#f56969", border:"#6a1a1a"},
  FUNDED: {label:"💰 FONDEADA", bg:"#0d1a2a", color:"#69b4f5", border:"#1a3a6a"},
};

function renderAccounts(data) {
  const grid = document.getElementById("acc-grid");
  if (!grid || !data) return;

  // Summary line
  const s = document.getElementById("acc-summary");
  if (s) s.textContent = `${data.active} activas · ${data.passed} aprobadas · ${data.failed} eliminadas`;

  // Total profit bar (target 20k = 4x5k)
  const totalPnl = data.total_profit || 0;
  const totalPct = Math.min(100, totalPnl / 20000 * 100);
  const tpEl = document.getElementById("acc-total-pnl");
  const tbEl = document.getElementById("acc-total-bar");
  if (tpEl) { tpEl.textContent = (totalPnl>=0?"+":"")+"$"+totalPnl.toFixed(0); tpEl.style.color = totalPnl>=0?"var(--green)":"var(--red)"; }
  if (tbEl) tbEl.style.width = totalPct+"%";

  grid.innerHTML = data.accounts.map(acc => {
    const m = STATUS_META[acc.status] || STATUS_META.EVAL;
    const pnlColor = acc.profit >= 0 ? "var(--green)" : "var(--red)";
    const ddColor  = acc.dd_pct > acc.max_dd_pct * 0.7 ? "var(--red)" : acc.dd_pct > acc.max_dd_pct * 0.4 ? "var(--yellow)" : "var(--text2)";
    const barPct   = Math.min(100, acc.target_pct);
    return `<div style="background:${m.bg};border:1px solid ${m.border};border-radius:6px;padding:7px;font-size:10px">
      <div style="display:flex;justify-content:space-between;margin-bottom:4px">
        <span style="font-weight:700;color:#ccc">${acc.name}</span>
        <span style="color:${m.color};font-size:9px;font-weight:600">${m.label}</span>
      </div>
      <div style="font-size:13px;font-weight:700;color:${pnlColor};margin-bottom:2px">
        ${acc.profit>=0?"+":""}$${acc.profit.toFixed(0)}
        <span style="font-size:10px;font-weight:400;color:var(--text2)">(${acc.profit_pct>=0?"+":""}${acc.profit_pct.toFixed(1)}%)</span>
      </div>
      <!-- progress bar toward target -->
      <div style="background:#111;border-radius:3px;height:4px;overflow:hidden;margin-bottom:4px">
        <div style="height:100%;background:${m.color};width:${barPct}%;transition:width .5s;border-radius:3px"></div>
      </div>
      <div style="display:flex;justify-content:space-between;color:var(--text2)">
        <span>DD <span style="color:${ddColor}">${acc.dd_pct.toFixed(1)}%</span>/${acc.max_dd_pct}%</span>
        <span>WR <span style="color:var(--green)">${acc.wr}%</span></span>
        <span>${acc.trades}T</span>
      </div>
      ${acc.status==="EVAL" ? `<div style="color:var(--text2);margin-top:3px">Falta $${acc.to_target.toFixed(0)} para aprobar</div>` : ""}
    </div>`;
  }).join("");
}

async function refreshAccounts() {
  try {
    const r = await fetch("/api/accounts");
    if (r.ok) renderAccounts(await r.json());
  } catch(e) { console.warn("refreshAccounts", e); }
}

refresh();
refreshDaily();
refreshAccounts();
setInterval(refresh,3000);
setInterval(refreshDaily,30000);  // daily state + paper report every 30s
setInterval(refreshAccounts,60000); // accounts refresh every 60s
setInterval(loadNews,300000);     // news refresh every 5 min (cached 1h on server)
window.addEventListener("resize",()=>drawEq(eqData,eqStart));
</script>
</body>
</html>"""

@app.get("/dashboard",response_class=HTMLResponse)
async def dashboard(): return DASHBOARD

@app.get("/",response_class=HTMLResponse)
async def root(): return HTMLResponse('<meta http-equiv="refresh" content="0;url=/dashboard">',302)

# ── Paper Trading Review Scheduler (4 semanas) ───────────────────────────────

PAPER_START_FILE = Path("paper_start_date.txt")

def _get_or_set_paper_start() -> str:
    """Devuelve la fecha de inicio del paper trading. La crea si no existe."""
    if PAPER_START_FILE.exists():
        return PAPER_START_FILE.read_text(encoding="utf-8").strip()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    PAPER_START_FILE.write_text(today, encoding="utf-8")
    print(f"[PAPER-REVIEW] Inicio paper trading registrado: {today}")
    return today

def _build_4week_report() -> str:
    """Construye el informe completo de 4 semanas para Telegram."""
    if not PAPER_LOG.exists():
        return "*Sin trades paper en 4 semanas*"

    trades = [json.loads(l) for l in PAPER_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not trades:
        return "*Sin trades paper registrados aún*"

    wins   = [t for t in trades if t.get("result") == "WIN"]
    losses = [t for t in trades if t.get("result") == "LOSS"]
    total_pnl = sum(t.get("pnl", 0) for t in trades)
    wr    = len(wins) / len(trades) * 100 if trades else 0
    avg_rr = sum(t.get("rr", 0) for t in wins) / len(wins) if wins else 0

    # Drawdown máximo
    bal = ACCOUNT["start"]
    peak, max_dd = bal, 0.0
    for t in trades:
        bal += t.get("pnl", 0)
        peak = max(peak, bal)
        dd   = (peak - bal) / ACCOUNT["start"] * 100
        max_dd = max(max_dd, dd)

    balance_final = ACCOUNT["start"] + total_pnl
    return_pct    = total_pnl / ACCOUNT["start"] * 100

    # Estado de cuentas simuladas
    acc_lines = []
    for a in PROP_ACCOUNTS:
        icon = {"EVAL":"🔄","PASSED":"✅","FAILED":"❌","FUNDED":"💰"}.get(a["status"],"—")
        pct  = (a["balance"] - a["start"]) / a["start"] * 100
        target_pct = a["profit_target"] / a["start"] * 100
        acc_lines.append(
            f"{icon} *{a['name']}* ({a['firm']})\n"
            f"   Balance: ${a['balance']:,.0f} ({pct:+.1f}%) | Target: +{target_pct:.0f}% | DD max: {a['max_dd_pct']}%"
        )

    # Veredicto
    if return_pct >= 8 and max_dd < 8:
        verdict = "SISTEMA LISTO para challenge real"
        verdict_icon = "LISTO"
    elif return_pct >= 4 and max_dd < 10:
        verdict = "Resultados prometedores — continuar 2 semanas mas"
        verdict_icon = "EN PROGRESO"
    elif return_pct < 0 or max_dd >= 10:
        verdict = "Revisar sistema antes de ir live"
        verdict_icon = "REVISAR"
    else:
        verdict = "Muestra inicial positiva — continuar observando"
        verdict_icon = "OK"

    lines = [
        "*INFORME 4 SEMANAS — Paper Trading IFVG*",
        f"_{datetime.now(timezone.utc).strftime('%d/%m/%Y')}_",
        "",
        "*Resumen de operaciones:*",
        f"  Trades: {len(trades)} ({len(wins)}W / {len(losses)}L)",
        f"  Win Rate: {wr:.1f}%",
        f"  Avg RR ganador: {avg_rr:.2f}x",
        f"  PnL total: ${total_pnl:+,.0f}",
        f"  Retorno: {return_pct:+.1f}%",
        f"  Max Drawdown: {max_dd:.1f}%",
        f"  Balance final: ${balance_final:,.0f}",
        "",
        "*Cuentas simuladas:*",
        *acc_lines,
        "",
        f"*Veredicto: {verdict_icon}*",
        f"_{verdict}_",
        "",
        "_Bot activo · Sin BE · RR 2.5 · Riesgo 1.3% · Bias auto_",
    ]
    return "\n".join(lines)


def paper_review_scheduler():
    """
    A las 4 semanas exactas del inicio del paper trading, envía un informe
    completo por Telegram con los resultados y un veredicto sobre si el sistema
    está listo para el challenge real.
    """
    start_date_str = _get_or_set_paper_start()
    from datetime import timedelta
    start_dt  = datetime.strptime(start_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    target_dt = start_dt + timedelta(weeks=4)
    # Si paper_review_4w.txt ya existe es que el informe se envió en una sesión anterior.
    # Sin este check el watchdog reenvía el informe en cada reinicio post 4 semanas.
    sent      = Path("paper_review_4w.txt").exists()

    print(f"[PAPER-REVIEW] Informe de 4 semanas programado para {target_dt.strftime('%Y-%m-%d')}")

    while True:
        time.sleep(3600)  # comprobar cada hora
        now = datetime.now(timezone.utc)

        if not sent and now >= target_dt:
            print("[PAPER-REVIEW] Generando informe de 4 semanas...")
            report = _build_4week_report()
            if send_telegram(report):
                print("[PAPER-REVIEW] Informe enviado por Telegram")
                Path("paper_review_4w.txt").write_text(report, encoding="utf-8")
                sent = True  # solo marcamos enviado si Telegram confirmó OK
            else:
                print("[PAPER-REVIEW] Error enviando Telegram — reintentando en 1h")
                # No marcamos sent=True → reintenta cada hora hasta que llegue


# ── State persistence: restaurar desde disco tras reinicio ─────────────────────
def _restore_state_from_disk():
    """
    Tras un reinicio (watchdog, crash, reboot), reconstruye el estado en memoria
    leyendo PAPER_LOG (trades históricos) y PROP_ACCOUNTS_LOG (snapshots de cuentas).

    Sin esto: ACCOUNT["balance"], DAILY_STATE y PROP_ACCOUNTS se resetean a cero
    cada vez que el watchdog reinicia el bot, haciendo el paper trading inútil.
    """
    # ── 1. Restaurar ACCOUNT["balance"] y DAILY_STATE desde PAPER_LOG ──────────
    if PAPER_LOG.exists():
        try:
            recs = [json.loads(l) for l in PAPER_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
            if recs:
                cumulative_pnl = sum(r.get("pnl", 0) for r in recs)
                ACCOUNT["balance"] = round(ACCOUNT["start"] + cumulative_pnl, 2)
                # Peak: reconstruir leyendo curva de equity para obtener máximo real
                bal = ACCOUNT["start"]
                peak = bal
                for r in recs:
                    bal += r.get("pnl", 0)
                    peak = max(peak, bal)
                ACCOUNT["peak"] = round(peak, 2)

                # DAILY_STATE para hoy
                today = _now_ny().strftime("%Y-%m-%d")
                today_recs = [r for r in recs if r.get("date", "") == today]
                if today_recs:
                    daily_pnl = round(sum(r.get("pnl", 0) for r in today_recs), 2)
                    DAILY_STATE["date"]            = today
                    DAILY_STATE["pnl"]             = daily_pnl
                    DAILY_STATE["trades"]          = len(today_recs)
                    DAILY_STATE["circuit_breaker"] = daily_pnl <= CIRCUIT_BREAKER_LIMIT
                    if DAILY_STATE["circuit_breaker"]:
                        print(f"[RESTORE] ⛔ Circuit breaker reactivado: PnL hoy ${daily_pnl:.0f}")

                print(f"[RESTORE] Balance restaurado: ${ACCOUNT['balance']:,.0f} "
                      f"(pico ${ACCOUNT['peak']:,.0f}, {len(recs)} trades)")
        except Exception as e:
            print(f"[RESTORE] Error restaurando ACCOUNT desde PAPER_LOG: {e}")

    # ── 2. Restaurar PROP_ACCOUNTS reproduciendo el historial completo ──────────
    # Reproducir todos los trades del PAPER_LOG una vez por cuenta (misma lógica que
    # _mirror_trade_to_accounts) para obtener balance, peak, DD y estado exactos.
    if PAPER_LOG.exists():
        try:
            recs = [json.loads(l) for l in PAPER_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
            if recs:
                today = _now_ny().strftime("%Y-%m-%d")
                for acc in PROP_ACCOUNTS:
                    bal = acc["start"]
                    peak = bal
                    wins = losses = trades = 0
                    daily_pnl = 0.0
                    status = "EVAL"
                    for r in recs:
                        if status == "FAILED":
                            break
                        pnl = r.get("pnl", 0)
                        res = r.get("result", "")
                        bal   = round(bal + pnl, 2)
                        peak  = max(peak, bal)
                        trades += 1
                        if res == "WIN":
                            wins += 1
                        else:
                            losses += 1
                        if r.get("date", "") == today:
                            daily_pnl = round(daily_pnl + pnl, 2)
                        # Reglas prop firm (mismas que _mirror_trade_to_accounts)
                        dd = (peak - bal) / peak * 100 if peak > 0 else 0
                        profit_pct = (bal - acc["start"]) / acc["start"] * 100
                        if dd >= acc["max_dd_pct"]:
                            status = "FAILED"
                        elif profit_pct >= acc["profit_target"] / acc["start"] * 100:
                            status = "PASSED"

                    acc["balance"]    = bal
                    acc["peak"]       = peak
                    acc["trades"]     = trades
                    acc["wins"]       = wins
                    acc["losses"]     = losses
                    acc["daily_pnl"]  = daily_pnl
                    acc["daily_date"] = today
                    acc["status"]     = status
                print(f"[RESTORE] {len(PROP_ACCOUNTS)} cuentas de fondeo restauradas")
        except Exception as e:
            print(f"[RESTORE] Error restaurando PROP_ACCOUNTS desde PAPER_LOG: {e}")

    # ── 3. Sincronizar estado FAILED desde último snapshot de PROP_ACCOUNTS_LOG ─
    # El replay de PAPER_LOG no puede reproducir fallos por daily-DD (no hay
    # PnL diario histórico por cuenta en PAPER_LOG).  Si el snapshot más reciente
    # marcó una cuenta como FAILED, respetamos ese estado.
    if PROP_ACCOUNTS_LOG.exists():
        try:
            snap_recs = [json.loads(l) for l in
                         PROP_ACCOUNTS_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
            if snap_recs:
                last_snap = {a["id"]: a for a in snap_recs[-1]["accounts"]}
                for acc in PROP_ACCOUNTS:
                    if acc["id"] in last_snap and last_snap[acc["id"]]["status"] == "FAILED":
                        acc["status"] = "FAILED"
                print(f"[RESTORE] Estado FAILED sincronizado desde último snapshot")
        except Exception as e:
            print(f"[RESTORE] Error leyendo PROP_ACCOUNTS_LOG para sync FAILED: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__=="__main__":
    print("\n"+"="*55)
    print("  IFVG Trading Cockpit — v2")
    print("  Dashboard: http://localhost:8000/dashboard")
    print("  Ctrl+C para parar")
    print("="*55+"\n")
    _restore_state_from_disk()   # restaura balance, daily state y cuentas tras reinicio
    threading.Thread(target=simulated_executor,daemon=True).start()
    threading.Thread(target=paper_position_tracker,daemon=True).start()
    threading.Thread(target=ifvg_scanner,daemon=True).start()
    threading.Thread(target=morning_bias_scheduler,daemon=True).start()
    threading.Thread(target=daily_report_scheduler,daemon=True).start()
    threading.Thread(target=paper_review_scheduler,daemon=True).start()
    threading.Thread(target=lambda:(time.sleep(1.5),webbrowser.open("http://localhost:8000/dashboard")),daemon=True).start()
    uvicorn.run(app,host="0.0.0.0",port=8000,log_level="warning")
