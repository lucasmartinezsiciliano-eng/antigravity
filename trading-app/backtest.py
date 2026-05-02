"""
backtest.py — IFVG Strategy Backtester
=======================================
Descarga datos históricos de 5m y testea la estrategia IFVG
con la misma lógica que usa el bot en producción.

Uso:
    python backtest.py                      # NQ últimos 6 meses
    python backtest.py --symbol ES1!        # ES
    python backtest.py --days 365           # 1 año
    python backtest.py --json               # output JSON (para el dashboard)
    python backtest.py --plot               # muestra equity curve ASCII

Métricas calculadas:
    Win rate, Profit Factor, Avg RR, Max Drawdown, Sharpe (simplificado),
    señales totales, señales en KZ, señales con bias correcto.
"""

import io
import json
import sys
import argparse
from datetime import datetime, time as dtime
from pathlib import Path

# Fix Windows console encoding (cp1252 chokes on special chars)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Reutiliza la lógica de detección del bot ──────────────────────────────────
# Importa detect_ifvg desde beta_local si está disponible, sino la redefine
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from beta_local import detect_ifvg
    print("[OK] Usando detect_ifvg() del bot en producción")
except ImportError:
    print("[INFO] Usando detect_ifvg() local (beta_local.py no encontrado)")

    def detect_ifvg(candles: list) -> list:
        """Copia exacta del detector del bot (3 etapas ICT)."""
        signals = []
        if len(candles) < 10:
            return signals
        ZONE_LOOKBACK = 40
        bull_fvgs, bear_fvgs, ifvg_zones = [], [], []

        for i in range(2, len(candles)):
            c0, c2 = candles[i], candles[i-2]

            if c2["high"] < c0["low"]:
                bull_fvgs.append({"top": c0["low"], "bot": c2["high"], "bar": i})
            if c2["low"] > c0["high"]:
                bear_fvgs.append({"top": c2["low"], "bot": c0["high"], "bar": i})

            bull_fvgs  = [f for f in bull_fvgs  if i - f["bar"] <= ZONE_LOOKBACK]
            bear_fvgs  = [f for f in bear_fvgs  if i - f["bar"] <= ZONE_LOOKBACK]
            ifvg_zones = [z for z in ifvg_zones if i - z["bar_inv"] <= ZONE_LOOKBACK]

            for fvg in bull_fvgs[:]:
                if i - fvg["bar"] < 1: continue
                if c0["close"] < fvg["bot"]:
                    ifvg_zones.append({"top": fvg["top"], "bot": fvg["bot"],
                                       "type": "sell", "bar_inv": i})
                    bull_fvgs.remove(fvg)

            for fvg in bear_fvgs[:]:
                if i - fvg["bar"] < 1: continue
                if c0["close"] > fvg["top"]:
                    ifvg_zones.append({"top": fvg["top"], "bot": fvg["bot"],
                                       "type": "buy", "bar_inv": i})
                    bear_fvgs.remove(fvg)

            for zone in ifvg_zones[:]:
                if i - zone["bar_inv"] < 1: continue
                if zone["bot"] <= c0["close"] <= zone["top"]:
                    signals.append({
                        "action": "SELL" if zone["type"] == "sell" else "BUY",
                        "close": c0["close"],
                        "reason": f"IFVG {'SELL' if zone['type']=='sell' else 'BUY'}",
                        "bar_index": i,
                        "fvg_bot": zone["bot"], "fvg_top": zone["top"],
                    })
                    ifvg_zones.remove(zone)
        return signals


# ── Kill zone filter ──────────────────────────────────────────────────────────
import pytz
NY = pytz.timezone("America/New_York")

def is_in_kill_zone(ts_unix: int, no_window_b: bool = False) -> bool:
    """Ventanas NY: A 8:30-9:00 + B 9:30-10:30 + Silver Bullet 10:00-11:00.
    no_window_b=True excluye la ventana B (9:30-10:00 única — SB cubre 10:00-11:00).
    """
    dt = datetime.fromtimestamp(ts_unix, tz=NY)
    if dt.weekday() >= 5:  # weekend
        return False
    t = dt.time()
    win_a = dtime(8, 30) <= t <= dtime(9, 0)
    win_b = dtime(9, 30) <= t <= dtime(10, 30)
    sb    = dtime(10, 0) <= t <= dtime(11, 0)
    if no_window_b:
        win_b = False   # drop 9:30-10:00 (backtests show worst sub-window)
    return win_a or win_b or sb


# ── Data download ─────────────────────────────────────────────────────────────
YF_MAP = {
    "NQ1!": "^NDX", "ES1!": "^GSPC",
    "MNQ1!": "^NDX", "MES1!": "^GSPC",
    "AAPL": "AAPL", "MSFT": "MSFT", "NVDA": "NVDA",
}

def load_from_file(path: str) -> list:
    """Carga velas desde JSON pre-descargado (ej. via data_av.py)."""
    candles = json.loads(Path(path).read_text(encoding="utf-8"))
    # Asegurar que tienen el campo 'open' (puede faltar en datos viejos)
    for c in candles:
        if "open" not in c:
            c["open"] = c["close"]
    candles.sort(key=lambda c: c["time"])
    print(f"[DATA] Cargadas {len(candles)} velas desde {path}")
    if candles:
        from datetime import datetime as _dt
        t0 = _dt.fromtimestamp(candles[0]["time"]).strftime("%Y-%m-%d")
        t1 = _dt.fromtimestamp(candles[-1]["time"]).strftime("%Y-%m-%d")
        print(f"[DATA] Rango: {t0} → {t1}")
    return candles


def download_data(symbol: str, days: int = 180) -> list:
    """Descarga velas 5m de Yahoo Finance. Máx ~60 días para 5m."""
    import yfinance as yf
    yf_sym = YF_MAP.get(symbol, symbol)

    if days <= 60:
        interval, period = "5m", f"{days}d"
    else:
        print(f"[INFO] >60 dias -> usando 1h (Yahoo Finance limita 5m a 60d)")
        interval, period = "1h", f"{min(days, 730)}d"

    print(f"[DATA] Descargando {symbol} ({yf_sym}) {period} @ {interval}...")
    df = yf.Ticker(yf_sym).history(period=period, interval=interval, auto_adjust=True)

    if df.empty:
        raise ValueError(f"Sin datos para {yf_sym}")

    candles = []
    for ts, row in df.iterrows():
        candles.append({
            "time":  int(ts.timestamp()),
            "open":  float(row["Open"]),
            "high":  float(row["High"]),
            "low":   float(row["Low"]),
            "close": float(row["Close"]),
        })

    print(f"[DATA] {len(candles)} velas descargadas")
    return candles


def download_15m(symbol: str, days: int = 60) -> list:
    """Descarga velas 15m para filtro de confluencia."""
    import yfinance as yf
    yf_sym = YF_MAP.get(symbol, symbol)
    days_capped = min(days, 60)
    df = yf.Ticker(yf_sym).history(period=f"{days_capped}d", interval="15m", auto_adjust=True)
    if df.empty:
        return []
    candles = []
    for ts, row in df.iterrows():
        candles.append({
            "time":  int(ts.timestamp()),
            "high":  float(row["High"]),
            "low":   float(row["Low"]),
            "close": float(row["Close"]),
        })
    return candles


def check_15m_confluence(signal_ts: int, action: str, candles_15m: list) -> tuple[bool, str]:
    """
    Confluencia 15m para señales IFVG.

    IFVG es una entrada contra el movimiento INMEDIATO (bounce hacia la zona),
    así que no se puede mirar la estructura de las últimas 2-3 velas — esas
    muestran el bounce y confunden el filtro.

    En cambio: mirar la TENDENCIA GLOBAL de las últimas 8 velas de 15m
    (excluyendo la más reciente que es el bounce).
    Si el 15m en conjunto es bajista → favorecer SELLs.
    Si el 15m en conjunto es alcista → favorecer BUYs.
    Si mixto → pass (no bloquear).
    """
    if not candles_15m:
        return True, "15m: sin datos (pass)"

    # Velas 15m antes del momento de la señal (excluir el bounce más reciente)
    prev = [c for c in candles_15m if c["time"] <= signal_ts]
    if len(prev) < 9:
        return True, "15m: datos insuficientes (pass)"

    # Últimas 8 velas excluyendo la más reciente (el bounce)
    bars = prev[-9:-1]
    closes = [b["close"] for b in bars]

    # Tendencia: precio inicial vs precio final del bloque
    trend_pct = (closes[-1] - closes[0]) / closes[0] * 100

    # Solo bloquear si la tendencia es FUERTEMENTE contraria (>0.3%)
    if action == "SELL" and trend_pct > 0.3:
        return False, f"15m: tendencia alcista fuerte ({trend_pct:+.2f}%) — contra SELL"
    if action == "BUY"  and trend_pct < -0.3:
        return False, f"15m: tendencia bajista fuerte ({trend_pct:+.2f}%) — contra BUY"

    return True, f"15m: tendencia {trend_pct:+.2f}% OK para {action}"


# ── Trade simulator ───────────────────────────────────────────────────────────
def build_historical_blackout_set(start_unix: int, end_unix: int,
                                   blackout_min: int = 15) -> set:
    """
    Genera blackout histórico para eventos HIGH impact USD recurrentes.
    Cubre el período completo del backtest (no solo la semana actual).

    Eventos incluidos:
      - NFP: primer viernes de cada mes, 8:30 ET
      - CPI/PPI: aprox día 10-13 de cada mes (mié/jue), 8:30 ET
      - Jobless Claims: TODOS los jueves, 8:30 ET
      - ISM Manufacturing: primer día hábil del mes, 10:00 ET
      - FOMC: fechas conocidas 2024-2026, 14:00 ET ± 30 min extra
      - Fed Chair Powell speaks: días post-FOMC, 14:30 ET

    Para backtests > 60 días (datos 1h o pre-descargados) donde ForexFactory
    no puede cubrir el historial.
    """
    import calendar as _cal
    blackout_ts = set()

    # FOMC fechas conocidas 2024-2026 (mes, día) → 14:00 ET
    FOMC_DATES = [
        (2024,1,31),(2024,3,20),(2024,5,1),(2024,6,12),(2024,7,31),
        (2024,9,18),(2024,11,7),(2024,12,18),
        (2025,1,29),(2025,3,19),(2025,5,7),(2025,6,18),(2025,7,30),
        (2025,9,17),(2025,11,5),(2025,12,17),
        (2026,1,28),(2026,3,18),(2026,5,6),(2026,6,17),
    ]

    def mark(ts: int, bmin: int = blackout_min):
        """Marca ±bmin minutos alrededor de ts."""
        ts_r = ts - (ts % 60)
        for d in range(-bmin * 60, bmin * 60 + 60, 60):
            blackout_ts.add(ts_r + d)

    def nth_weekday_of_month(year, month, weekday, n=1):
        """Devuelve el n-ésimo día de la semana (0=Lun) del mes."""
        first = _dt(year, month, 1)
        offset = (weekday - first.weekday()) % 7
        day = first + _timedelta(days=offset + (n-1)*7)
        return day if day.month == month else None

    from datetime import date as _date, datetime as _dt, timedelta as _timedelta

    # Rango de fechas del backtest
    start_date = _dt.fromtimestamp(start_unix, tz=NY).date()
    end_date   = _dt.fromtimestamp(end_unix,   tz=NY).date()

    cur = start_date.replace(day=1)
    while cur <= end_date:
        y, m = cur.year, cur.month

        # ── Jobless Claims — todos los jueves 8:30 ET ──────────────────────
        # Weekday 3 = Jueves
        d = _date(y, m, 1)
        while d.month == m:
            if d.weekday() == 3:  # Thursday
                dt_et = _dt(d.year, d.month, d.day, 8, 30, tzinfo=NY)
                ts = int(dt_et.timestamp())
                if start_unix <= ts <= end_unix:
                    mark(ts)
            d += _timedelta(days=1)

        # ── NFP — primer viernes del mes 8:30 ET ───────────────────────────
        nfp = nth_weekday_of_month(y, m, 4, 1)  # 4 = Friday
        if nfp:
            dt_et = _dt(nfp.year, nfp.month, nfp.day, 8, 30, tzinfo=NY)
            ts = int(dt_et.timestamp())
            if start_unix <= ts <= end_unix:
                mark(ts, blackout_min + 15)  # NFP más volátil → +15 min extra

        # ── CPI/PPI — aprox días 11-13 de cada mes 8:30 ET ────────────────
        # Suele ser el miércoles de la semana del 10-14
        for day_approx in (11, 12, 13):
            try:
                d = _date(y, m, day_approx)
                if d.weekday() in (2, 3):  # Miércoles o Jueves
                    dt_et = _dt(d.year, d.month, d.day, 8, 30, tzinfo=NY)
                    ts = int(dt_et.timestamp())
                    if start_unix <= ts <= end_unix:
                        mark(ts)
                    break
            except ValueError:
                pass

        # ── ISM Manufacturing — primer día hábil del mes 10:00 ET ─────────
        d = _date(y, m, 1)
        while d.weekday() >= 5: d += _timedelta(days=1)
        dt_et = _dt(d.year, d.month, d.day, 10, 0, tzinfo=NY)
        ts = int(dt_et.timestamp())
        if start_unix <= ts <= end_unix:
            mark(ts)

        # Avanzar al mes siguiente
        if m == 12: cur = _date(y+1, 1, 1)
        else:        cur = _date(y, m+1, 1)

    # ── FOMC fechas exactas 14:00 ET ± 30 min ──────────────────────────────
    for (fy, fm, fd) in FOMC_DATES:
        dt_et = _dt(fy, fm, fd, 14, 0, tzinfo=NY)
        ts = int(dt_et.timestamp())
        if start_unix <= ts <= end_unix:
            mark(ts, 30)

    return blackout_ts


def build_news_blackout_set(days: int, blackout_min: int = 15) -> set:
    """
    Construye blackout de noticias para el backtest.
    - Si days <= 60: usa ForexFactory (semana actual, datos reales)
    - Si days > 60 o hay data-file: usa calendario histórico aproximado
    """
    import time as _time
    now_unix = _time.time()
    cutoff   = now_unix - days * 86400

    # Para períodos históricos largos usa el calendario aproximado
    if days > 60:
        bs = build_historical_blackout_set(int(cutoff), int(now_unix), blackout_min)
        print(f"[NEWS] Calendario histórico aproximado: {len(bs)} minutos en blackout ({days}d)")
        return bs

    # Para 60d recientes: ForexFactory (datos reales esta semana)
    try:
        from news_calendar import fetch_calendar
        events = fetch_calendar()
        blackout_ts = set()
        week_events = 0
        for ev in events:
            ts = ev.get("ts_unix", 0)
            if ev.get("all_day"):
                continue
            if ts < cutoff:
                continue  # fuera de ventana del backtest
            week_events += 1
            # Mark every minute in ±blackout_min window
            for delta in range(-blackout_min * 60, blackout_min * 60 + 60, 60):
                blackout_ts.add(ts + delta - (ts % 60))
        if week_events == 0:
            print(f"[NEWS] Sin eventos esta semana en rango (ForexFactory solo provee 7d actuales)")
        return blackout_ts
    except Exception:
        return set()


def is_news_blackout(ts_unix: int, blackout_set: set) -> bool:
    """True si el timestamp cae en ventana de blackout de noticias."""
    if not blackout_set:
        return False
    ts_rounded = ts_unix - (ts_unix % 60)
    return ts_rounded in blackout_set


BE_TRIGGER_RR = 0.5   # mueve SL a entry cuando precio alcanza 0.5R (cambio: era 1.0R)
BE_BUFFER_R   = 0.08  # SL va a entry + 8% del stop (pequeña ganancia garantizada, no $0 exacto)


# ── VWAP Intraday (ICT Gap 6) ─────────────────────────────────────────────────

# ── Order Flow Tools: Volume Profile, Initial Balance, Delta Proxy ────────────

def build_session_vp(candles: list, date_str: str, resolution: float = 0.10) -> dict:
    """
    Volume Profile de la sesión RTH para una fecha dada.
    Usa datos reales de volumen si disponibles (QQQ ETF tiene volumen real).
    Retorna: {poc, vah, val, vp_dict, avg_vol_per_level}
    """
    session = []
    for c in candles:
        dt = datetime.fromtimestamp(c["time"], tz=NY)
        if dt.strftime("%Y-%m-%d") == date_str and dtime(9, 30) <= dt.time() <= dtime(16, 0):
            session.append(c)
    if not session:
        return {}

    vp = {}
    for c in session:
        vol = c.get("volume") or max(c["high"] - c["low"], 0.01) * 10000  # proxy si no hay vol
        levels_in_candle = max(1, round((c["high"] - c["low"]) / resolution))
        vol_per_level = vol / levels_in_candle
        price = c["low"]
        for _ in range(levels_in_candle):
            level = round(round(price / resolution) * resolution, 2)
            vp[level] = vp.get(level, 0) + vol_per_level
            price += resolution

    if not vp:
        return {}

    poc = max(vp, key=vp.get)
    total_vol = sum(vp.values())
    avg_vol   = total_vol / len(vp)

    # Value Area (70% del volumen total — expandir desde el POC hacia afuera)
    sorted_by_vol = sorted(vp.items(), key=lambda x: x[1], reverse=True)
    va_vol = 0
    va_levels = []
    for price_level, vol in sorted_by_vol:
        if va_vol >= total_vol * 0.70:
            break
        va_vol += vol
        va_levels.append(price_level)

    return {
        "poc":       poc,
        "vah":       max(va_levels) if va_levels else poc,
        "val":       min(va_levels) if va_levels else poc,
        "vp":        vp,
        "avg_vol":   avg_vol,
        "lvn_threshold": avg_vol * 0.80,  # LVN = <80% del vol promedio por nivel
    }


def build_ib_map(candles: list) -> dict:
    """
    Initial Balance por sesión: rango de la primera hora (9:30–10:30 ET).
    Retorna: {date_str: {high, low, mid}}
    """
    from collections import defaultdict
    ib_candles: dict = defaultdict(list)

    for c in candles:
        dt = datetime.fromtimestamp(c["time"], tz=NY)
        if dtime(9, 30) <= dt.time() <= dtime(10, 25):  # hasta las 10:30 inclusive
            ib_candles[dt.strftime("%Y-%m-%d")].append(c)

    ib_map = {}
    for date_str, bars in ib_candles.items():
        if bars:
            ib_map[date_str] = {
                "high": max(c["high"] for c in bars),
                "low":  min(c["low"]  for c in bars),
                "mid":  (max(c["high"] for c in bars) + min(c["low"] for c in bars)) / 2,
            }
    return ib_map


def build_vp_map(candles: list) -> dict:
    """
    Volume Profile del día ANTERIOR por cada fecha de trading.
    Retorna: {date_str: vp_data_dict}
    Para usar en el filtro LVN: el IFVG debe estar en un LVN de ayer.
    """
    dates = sorted({datetime.fromtimestamp(c["time"], tz=NY).strftime("%Y-%m-%d") for c in candles})
    vp_map = {}
    for i, date_str in enumerate(dates[1:], 1):
        prev_date = dates[i - 1]
        vp_map[date_str] = build_session_vp(candles, prev_date)
    return vp_map


def is_in_lvn_zone(price: float, vp_data: dict, tolerance: float = 0.30) -> bool:
    """True si el precio está en un Low Volume Node (LVN) del Volume Profile dado."""
    if not vp_data or "vp" not in vp_data:
        return True  # sin datos: no filtrar

    nearby_vol = sum(v for p, v in vp_data["vp"].items() if abs(p - price) <= tolerance)
    return nearby_vol < vp_data.get("lvn_threshold", 0)


def delta_confirms_entry(signal_bar: dict, action: str) -> bool:
    """
    Proxy del Delta adaptado al patrón IFVG:
    El retest llega a la zona con presión opuesta (eso ES el setup).
    Para BUY: la vela de retest baja HACIA la zona → close en mitad INFERIOR = precio
             aún en discount, sellers agotándose, zona soportando bien.
             Si close está en mitad SUPERIOR, el precio ya se fue de la zona → entrada tardía.
    Para SELL: inverso.

    Filtro: rechazar si la vela es un gap o tiene rango tan pequeño que no aplica.
    También rechazar si la sombra opuesta es muy grande (rechazo claro en contra).
    """
    rng = signal_bar["high"] - signal_bar["low"]
    if rng < 0.001:
        return True  # vela doji: no filtrar
    mid = signal_bar["low"] + rng / 2

    if action == "BUY":
        # Para BUY: el retest baja hacia la zona, queremos precio aún en zone (close ≤ mid)
        # O al menos que el lower wick sea > upper wick (rechazo de zona visible)
        lower_wick = signal_bar["close"] - signal_bar["low"]
        upper_wick = signal_bar["high"] - signal_bar["close"]
        # Válido si: close en zona inferior, O hay wick inferior grande (hammer)
        return signal_bar["close"] <= mid or lower_wick > upper_wick * 1.5
    else:
        # Para SELL: el retest sube hacia la zona, queremos precio aún en zone (close ≥ mid)
        # O que el upper wick sea > lower wick (shooting star)
        lower_wick = signal_bar["close"] - signal_bar["low"]
        upper_wick = signal_bar["high"] - signal_bar["close"]
        return signal_bar["close"] >= mid or upper_wick > lower_wick * 1.5


def compute_session_vwap(candles: list, bar_idx: int) -> float:
    """
    VWAP desde inicio de sesión RTH (9:30 ET) hasta bar_idx.
    Sin datos de volumen reales: usa rango de vela (high-low) como proxy.
    Lógica ICT: comprar en discount (precio < VWAP), vender en premium (precio > VWAP).
    """
    dt_bar = datetime.fromtimestamp(candles[bar_idx]["time"], tz=NY)
    session_open = dt_bar.replace(hour=9, minute=30, second=0, microsecond=0)

    cum_tp_vol = 0.0
    cum_vol    = 0.0

    for i in range(bar_idx, -1, -1):
        c   = candles[i]
        dt_c = datetime.fromtimestamp(c["time"], tz=NY)
        if dt_c.date() != dt_bar.date() or dt_c < session_open:
            break
        typical   = (c["high"] + c["low"] + c["close"]) / 3
        vol_proxy = max(c["high"] - c["low"], 0.01)
        cum_tp_vol += typical * vol_proxy
        cum_vol    += vol_proxy

    return cum_tp_vol / cum_vol if cum_vol > 0 else candles[bar_idx]["close"]


# ── Auto Daily Bias (Fede Esses Day 22 + TJR Day 34-36) ──────────────────────

def build_daily_candles(candles_5m: list) -> list:
    """
    Agrega velas 5m a velas diarias (RTH: 9:30-16:00 ET para QQQ/ETFs).
    Retorna: [{date, open, high, low, close, ts_open}]
    """
    from collections import defaultdict
    daily: dict = {}

    for c in sorted(candles_5m, key=lambda x: x["time"]):
        dt = datetime.fromtimestamp(c["time"], tz=NY)
        if not (dtime(9, 30) <= dt.time() <= dtime(16, 0)):
            continue
        dk = dt.date()
        if dk not in daily:
            daily[dk] = {"open": c["open"], "high": c["high"], "low": c["low"],
                         "close": c["close"], "ts_open": c["time"], "date": dk}
        else:
            d = daily[dk]
            d["high"]  = max(d["high"],  c["high"])
            d["low"]   = min(d["low"],   c["low"])
            d["close"] = c["close"]

    return [daily[k] for k in sorted(daily.keys())]


def build_auto_bias_map(candles_5m: list, lookback_days: int = 20) -> dict:
    """
    Calcula el daily bias automático para cada día de trading.
    Implementa el framework de Fede Esses Day 22 + TJR Day 34-36.

    Algoritmo (2 factores):
      1. Previous day close position en su propio rango (delivery):
         close > 60% del rango → +1 (bullish delivery, continuación esperada)
         close < 40% del rango → -1 (bearish delivery)

      2. Weekly premium/discount (Fede: 'operar en continuación, no en retrace'):
         open del día < 50% del rango de los últimos 20 días → discount → +1 (comprar)
         open del día > 50% del rango de los últimos 20 días → premium → -1 (vender)

    Score: +2/+1 → BULLISH | -2/-1 → BEARISH | 0 → NEUTRAL (no operar ese día)

    Retorna: {date_obj: "BULLISH" | "BEARISH" | "NEUTRAL"}
    """
    daily_candles = build_daily_candles(candles_5m)
    if len(daily_candles) < 3:
        return {}

    bias_map = {}
    for i in range(1, len(daily_candles)):
        today = daily_candles[i]
        prev  = daily_candles[i - 1]

        score = 0

        # Factor 1: Previous day delivery (close position in its range)
        prev_range = prev["high"] - prev["low"]
        if prev_range > 0:
            close_pos = (prev["close"] - prev["low"]) / prev_range
            if close_pos > 0.60:
                score += 1   # bullish close → expect continuation up
            elif close_pos < 0.40:
                score -= 1   # bearish close → expect continuation down

        # Factor 2: Weekly premium/discount context
        start_idx = max(0, i - lookback_days)
        window = daily_candles[start_idx:i]
        if window:
            period_high = max(d["high"] for d in window)
            period_low  = min(d["low"]  for d in window)
            period_mid  = (period_high + period_low) / 2
            if today["open"] < period_mid:
                score += 1   # opening in discount → buy bias
            elif today["open"] > period_mid:
                score -= 1   # opening in premium → sell bias

        if score >= 1:
            bias_map[today["date"]] = "BULLISH"
        elif score <= -1:
            bias_map[today["date"]] = "BEARISH"
        else:
            bias_map[today["date"]] = "NEUTRAL"

    return bias_map


def simulate_trades(
    candles: list,
    signals: list,
    rr: float = 2.0,
    stop_pct: float = 0.5,
    account: float = 50_000.0,
    risk_pct: float = 0.01,
    kz_filter: bool = True,
    max_per_day: int = 1,
    news_filter: bool = True,
    blackout_set: set = None,
    skip_weekdays: tuple = (0, 1),   # (0=Mon, 1=Tue) — worst WR days by data
    be_trigger_rr: float = None,     # None = use module default BE_TRIGGER_RR
    no_window_b: bool = False,
    min_displacement: float = 0.0,  # pts body of FVG creation candle (0 = off)
    auto_bias_map: dict = None,      # {date: BULLISH|BEARISH|NEUTRAL} — None = off
    slippage_pct: float = 0.0,       # slippage por side como % del precio (0.03 = 0.03%)
    commission_usd: float = 0.0,     # comisión fija por trade round-trip en $
    next_bar_entry: bool = False,    # True: entrar en open de sig. vela (no cierre actual)
    vwap_filter: bool = False,       # True: comprar solo bajo VWAP, vender solo sobre VWAP
    partial_exit_r: float = 0.0,    # >0: cerrar 50% posición en partial_exit_r×R, dejar runner a TP
    ib_filter: bool = False,        # True: señal post-10:30 debe estar fuera del Initial Balance
    delta_filter: bool = False,     # True: vela de retest cierra en mitad favorable (proxy delta)
    lvn_filter: bool = False,       # True: IFVG debe estar en LVN del VP del día anterior
    ib_map: dict = None,            # pre-calculado por build_ib_map()
    vp_map: dict = None,            # pre-calculado por build_vp_map()
) -> list:
    """
    Simula ejecución de señales sobre datos históricos.
    vwap_filter: solo BUY cuando precio < VWAP (discount), solo SELL cuando precio > VWAP (premium).
    partial_exit_r: si >0, cierra 50% de la posición en ese múltiplo de R y deja el resto ir al TP.
    """
    _be_trigger = be_trigger_rr if be_trigger_rr is not None else BE_TRIGGER_RR
    trades = []
    open_pos = None
    day_count  = {}   # date -> count
    last_bar_traded = -1  # one trade per bar max
    if blackout_set is None:
        blackout_set = set()

    for sig in signals:
        bar_idx = sig["bar_index"]
        if bar_idx >= len(candles):
            continue

        # One signal per bar (avoids duplicate trades on same timestamp)
        if bar_idx == last_bar_traded:
            continue

        signal_bar = candles[bar_idx]
        bar_time   = signal_bar["time"]

        # Kill zone filter
        if kz_filter and not is_in_kill_zone(bar_time, no_window_b=no_window_b):
            continue

        # News blackout filter
        if news_filter and is_news_blackout(bar_time, blackout_set):
            continue

        # Day-of-week filter (skip worst WR days)
        dt_ny = datetime.fromtimestamp(bar_time, tz=NY)
        if skip_weekdays and dt_ny.weekday() in skip_weekdays:
            continue

        # Daily limit
        day_key = dt_ny.date()
        if day_count.get(day_key, 0) >= max_per_day:
            continue

        # Displacement filter: body of FVG creation candle must exceed min_displacement pts
        if min_displacement > 0:
            cb = sig.get("creation_bar")
            if cb is not None and cb < len(candles):
                cc = candles[cb]
                body = abs(cc["close"] - cc.get("open", cc["close"]))
                if body < min_displacement:
                    continue

        # Auto daily bias filter (Fede Esses Day 22 + TJR Day 34-36)
        if auto_bias_map is not None:
            day_bias = auto_bias_map.get(day_key, "NEUTRAL")
            if day_bias == "NEUTRAL":
                continue  # no hay bias claro → no operar ese día
            action_needed = "BUY" if day_bias == "BULLISH" else "SELL"
            if sig["action"] != action_needed:
                continue  # señal contra el bias del día → skip

        # Initial Balance filter: post-10:30 señal debe estar FUERA del IB (breakout confirmado)
        if ib_filter and ib_map is not None:
            date_str = dt_ny.strftime("%Y-%m-%d")
            ib = ib_map.get(date_str)
            if ib and dt_ny.time() >= dtime(10, 30):
                action_pre = sig["action"]
                price_now  = signal_bar["close"]
                if action_pre == "BUY"  and price_now < ib["high"]:
                    continue  # precio dentro o bajo del IB → no confirma breakout alcista
                if action_pre == "SELL" and price_now > ib["low"]:
                    continue  # precio dentro o sobre del IB → no confirma breakdown bajista

        # Delta proxy filter: la vela de retest debe cerrar en la mitad correcta
        if delta_filter and not delta_confirms_entry(signal_bar, sig["action"]):
            continue  # delta contra la dirección → skip

        # LVN filter: el IFVG debe estar en un Low Volume Node del VP del día anterior
        if lvn_filter and vp_map is not None:
            date_str = dt_ny.strftime("%Y-%m-%d")
            vp_data  = vp_map.get(date_str)
            if vp_data and not is_in_lvn_zone(signal_bar["close"], vp_data):
                continue  # IFVG en zona de alto volumen → skip

        # VWAP filter: solo BUY en discount (precio < VWAP), solo SELL en premium (precio > VWAP)
        if vwap_filter:
            vwap = compute_session_vwap(candles, bar_idx)
            action_pre = sig["action"]
            if action_pre == "BUY"  and signal_bar["close"] >= vwap:
                continue  # comprando en premium — esperar descuento
            if action_pre == "SELL" and signal_bar["close"] <= vwap:
                continue  # vendiendo en descuento — esperar premium

        # Skip if position open
        if open_pos:
            continue

        # Entry price: close of signal bar, or open of next bar (more realistic)
        if next_bar_entry:
            next_idx = bar_idx + 1
            if next_idx >= len(candles):
                continue
            raw_entry = candles[next_idx]["open"]
            fwd_start = next_idx + 1
        else:
            raw_entry = signal_bar["close"]
            fwd_start = bar_idx + 1

        action = sig["action"]

        # Slippage on entry: BUY pays more, SELL receives less
        slip = raw_entry * slippage_pct / 100
        entry = raw_entry + slip if action == "BUY" else raw_entry - slip

        stop_d = entry * stop_pct / 100
        sl = entry - stop_d if action == "BUY" else entry + stop_d
        tp = entry + stop_d * rr if action == "BUY" else entry - stop_d * rr

        # Dynamic sizing: LVN-confirmed setups get 1.5× risk (máxima confluencia)
        effective_risk = risk_pct
        if vp_map is not None:
            date_str_entry = dt_ny.strftime("%Y-%m-%d")
            vp_entry = vp_map.get(date_str_entry)
            if vp_entry and is_in_lvn_zone(signal_bar["close"], vp_entry):
                effective_risk = min(risk_pct * 1.5, 0.02)  # max 2% por trade
        size_usd = account * effective_risk
        qty = max(1, int(size_usd / stop_d)) if stop_d > 0 else 1

        open_pos = {
            "action": action, "entry": entry, "sl": sl, "tp": tp,
            "qty": qty, "stop_d": stop_d, "bar_idx": bar_idx,
            "ts": bar_time, "be_triggered": False,
        }

        # Simulate forward from next bar
        result      = None
        partial_pnl = 0.0        # PnL acumulado de salidas parciales
        partial_qty = 0          # cantidad ya cerrada en parcial
        partial_done = False     # True cuando se ejecutó la salida parcial
        partial_price_level = (entry + stop_d * partial_exit_r) if action == "BUY" \
                         else (entry - stop_d * partial_exit_r)

        for future_bar in candles[fwd_start:fwd_start + 200]:
            h, l = future_bar["high"], future_bar["low"]

            # Partial exit: cierra la mitad cuando precio llega a partial_exit_r × R
            if partial_exit_r > 0 and not partial_done:
                if (action == "BUY"  and h >= partial_price_level) or \
                   (action == "SELL" and l <= partial_price_level):
                    partial_qty  = open_pos["qty"] // 2
                    remain_qty   = open_pos["qty"] - partial_qty
                    p_exit       = partial_price_level - slip if action == "BUY" \
                                   else partial_price_level + slip
                    partial_pnl  = (p_exit - entry) * partial_qty if action == "BUY" \
                                   else (entry - p_exit) * partial_qty
                    open_pos["qty"] = remain_qty   # restante sigue corriendo
                    # Mover SL a BE en el runner
                    open_pos["sl"]  = entry + stop_d * BE_BUFFER_R if action == "BUY" \
                                      else entry - stop_d * BE_BUFFER_R
                    open_pos["be_triggered"] = True
                    partial_done = True

            # Break-even at be_trigger*R with small buffer (si no hay partial exit)
            if not open_pos["be_triggered"]:
                if action == "BUY"  and h >= entry + stop_d * _be_trigger:
                    open_pos["sl"] = entry + stop_d * BE_BUFFER_R
                    open_pos["be_triggered"] = True
                elif action == "SELL" and l <= entry - stop_d * _be_trigger:
                    open_pos["sl"] = entry - stop_d * BE_BUFFER_R
                    open_pos["be_triggered"] = True

            # Check SL — apply exit slippage (adverse: fills worse than SL price)
            if action == "BUY"  and l <= open_pos["sl"]:
                exit_price = open_pos["sl"] - slip
                pnl = partial_pnl + (exit_price - entry) * open_pos["qty"] - commission_usd
                result = {"exit": exit_price, "reason": "BE" if open_pos["be_triggered"] else "SL", "pnl": pnl}
                break
            elif action == "SELL" and h >= open_pos["sl"]:
                exit_price = open_pos["sl"] + slip
                pnl = partial_pnl + (entry - exit_price) * open_pos["qty"] - commission_usd
                result = {"exit": exit_price, "reason": "BE" if open_pos["be_triggered"] else "SL", "pnl": pnl}
                break

            # Check TP — apply exit slippage
            if action == "BUY"  and h >= tp:
                exit_price = tp - slip
                pnl = partial_pnl + (exit_price - entry) * open_pos["qty"] - commission_usd
                result = {"exit": exit_price, "reason": "TP", "pnl": pnl}
                break
            elif action == "SELL" and l <= tp:
                exit_price = tp + slip
                pnl = partial_pnl + (entry - exit_price) * open_pos["qty"] - commission_usd
                result = {"exit": exit_price, "reason": "TP", "pnl": pnl}
                break

        if result:
            win = result["pnl"] > 0
            account += result["pnl"]
            rr_achieved = abs(result["pnl"] / (stop_d * qty)) if stop_d else 0
            trades.append({
                "ts":         datetime.fromtimestamp(open_pos["ts"], tz=NY).strftime("%Y-%m-%d %H:%M ET"),
                "action":     action,
                "entry":      round(entry, 2),
                "exit":       round(result["exit"], 2),
                "sl":         round(sl, 2),
                "tp":         round(tp, 2),
                "pnl":        round(result["pnl"], 2),
                "result":     "WIN" if win else "LOSS",
                "reason":     result["reason"],
                "be":         open_pos["be_triggered"],
                "rr":         round(rr_achieved, 2),
                "balance":    round(account, 2),
                "sig_reason": sig.get("reason", ""),
            })
            day_count[day_key] = day_count.get(day_key, 0) + 1
            last_bar_traded = bar_idx

        open_pos = None

    return trades


# ── Metrics ───────────────────────────────────────────────────────────────────
def compute_metrics(trades: list, start_balance: float = 50_000.0) -> dict:
    if not trades:
        return {"error": "Sin trades — sin señales en el período o todos filtrados"}

    wins   = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] <= 0]
    pnl_total = sum(t["pnl"] for t in trades)

    gross_win  = sum(t["pnl"] for t in wins)
    gross_loss = abs(sum(t["pnl"] for t in losses))

    # Drawdown
    peak = start_balance
    max_dd_usd = 0.0
    running = start_balance
    for t in trades:
        running = t["balance"]
        peak = max(peak, running)
        dd = peak - running
        max_dd_usd = max(max_dd_usd, dd)

    end_balance = trades[-1]["balance"] if trades else start_balance
    max_dd_pct = round(max_dd_usd / peak * 100, 2)

    # Sharpe (simplificado — usa PnL por trade como retornos)
    import statistics
    pnls = [t["pnl"] for t in trades]
    try:
        sharpe = round(statistics.mean(pnls) / statistics.stdev(pnls) * (252**0.5), 2) if len(pnls) > 1 else None
    except Exception:
        sharpe = None

    # Consecutive losses
    max_consec_loss = 0
    cur_l = 0
    for t in trades:
        if t["pnl"] <= 0:
            cur_l += 1; max_consec_loss = max(max_consec_loss, cur_l)
        else:
            cur_l = 0

    return {
        "period":             f"{trades[0]['ts'][:10]} a {trades[-1]['ts'][:10]}",
        "total_signals":      None,   # filled by caller
        "signals_in_kz":      None,
        "trades_taken":       len(trades),
        "wins":               len(wins),
        "losses":             len(losses),
        "win_rate":           round(len(wins) / len(trades), 3) if trades else 0,
        "profit_factor":      round(gross_win / gross_loss, 2) if gross_loss > 0 else None,
        "avg_win_usd":        round(gross_win  / len(wins),   2) if wins   else 0,
        "avg_loss_usd":       round(gross_loss / len(losses), 2) if losses else 0,
        "avg_rr":             round(sum(t["rr"] for t in trades) / len(trades), 2),
        "total_pnl":          round(pnl_total, 2),
        "start_balance":      start_balance,
        "end_balance":        round(end_balance, 2),
        "return_pct":         round((end_balance - start_balance) / start_balance * 100, 2),
        "max_drawdown_pct":   max_dd_pct,
        "max_consec_losses":  max_consec_loss,
        "sharpe_approx":      sharpe,
        "be_trades":          sum(1 for t in trades if t["be"]),
    }


# ── ASCII equity curve ────────────────────────────────────────────────────────
def print_equity_curve(trades: list, width: int = 60, height: int = 15):
    if not trades:
        return
    balances = [t["balance"] for t in trades]
    mn, mx = min(balances), max(balances)
    rng = mx - mn or 1

    print(f"\n  Equity Curve  ${mn:,.0f} — ${mx:,.0f}")
    print("  " + "─" * width)

    rows = []
    for row in range(height):
        threshold = mx - (row / height) * rng
        line = ""
        for b in balances:
            if b >= threshold:
                line += "█"
            else:
                line += " "
        rows.append(line[:width])

    for r in rows:
        print(f"  │{r}│")
    print("  " + "─" * width)
    print(f"  0{'trades':^{width-2}}{len(trades)}")


# ── Report printer ────────────────────────────────────────────────────────────
def print_report(metrics: dict, trades: list):
    print("\n" + "="*60)
    print("  IFVG STRATEGY — BACKTEST REPORT")
    print("="*60)
    print(f"  Período:           {metrics.get('period','—')}")
    print(f"  Total señales:     {metrics.get('total_signals','—')}")
    print(f"  Señales en KZ:     {metrics.get('signals_in_kz','—')}")
    print(f"  Trades ejecutados: {metrics['trades_taken']}")
    print()
    print(f"  Win Rate:          {metrics['win_rate']*100:.1f}%  (target ≥50%)")
    print(f"  Profit Factor:     {metrics.get('profit_factor','—')}  (target ≥1.5)")
    print(f"  Avg RR:            {metrics['avg_rr']:.2f}:1  (target ≥2.0)")
    print(f"  Sharpe (aprox):    {metrics.get('sharpe_approx','—')}")
    print()
    print(f"  Total PnL:         ${metrics['total_pnl']:+,.2f}")
    print(f"  Balance final:     ${metrics['end_balance']:,.2f}")
    print(f"  Retorno:           {metrics['return_pct']:+.1f}%")
    print(f"  Max Drawdown:      {metrics['max_drawdown_pct']}%")
    print(f"  Pérdidas consec.:  {metrics['max_consec_losses']}")
    print(f"  Trades con BE:     {metrics['be_trades']}")
    print()

    # Verdict
    pf = metrics.get("profit_factor") or 0
    wr = metrics["win_rate"]
    dd = metrics["max_drawdown_pct"]
    ok = pf >= 1.5 and wr >= 0.45 and dd <= 25

    if ok:
        print("  [OK] SISTEMA VALIDO -- metricas dentro de rangos aceptables")
        print("       Siguiente paso: paper trading 2-4 semanas con IBKR")
    elif pf >= 1.0:
        print("  [--] SISTEMA MARGINAL -- funciona pero necesita mas datos o ajuste")
        print("       Analiza las senales filtradas por bias para ver si mejora")
    else:
        print("  [X] SISTEMA NO VALIDO -- profit factor < 1.0 (pierde dinero)")
        print("      Revisar: logica IFVG, kill zones, o necesitas mas historico")

    print("="*60)

    # Last 10 trades
    if trades:
        print("\n  Últimos 10 trades:")
        print(f"  {'Fecha':<20} {'Dir':<5} {'Entry':>8} {'Exit':>8} {'PnL':>8} {'RR':>5} {'Result'}")
        print("  " + "─"*65)
        for t in trades[-10:]:
            pnl_str = f"${t['pnl']:+,.0f}"
            print(f"  {t['ts']:<20} {t['action']:<5} {t['entry']:>8.0f} {t['exit']:>8.0f} "
                  f"{pnl_str:>8} {t['rr']:>4.1f}  {t['result']}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="IFVG Backtest")
    parser.add_argument("--data-file", default=None,       help="JSON de velas pre-descargado (ej. qqq_24m_5m.json via data_av.py)")
    parser.add_argument("--symbol",   default="NQ1!",    help="Símbolo (NQ1!, ES1!, AAPL...)")
    parser.add_argument("--days",     default=60,  type=int, help="Días históricos (max 60 para 5m)")
    parser.add_argument("--rr",       default=2.0, type=float, help="RR objetivo (default 2.0)")
    parser.add_argument("--stop-pct", default=0.5, type=float, help="Stop %% del precio (default 0.5)")
    parser.add_argument("--risk-pct", default=1.0, type=float, help="Riesgo %% por trade (default 1.0)")
    parser.add_argument("--account",  default=50000.0, type=float, help="Cuenta inicial USD")
    parser.add_argument("--no-kz",           action="store_true", help="Ignorar filtro kill zone")
    parser.add_argument("--no-news",         action="store_true", help="Ignorar blackout de noticias")
    parser.add_argument("--no-15m",          action="store_true", help="Ignorar filtro confluencia 15m")
    parser.add_argument("--max-per-day",     default=1, type=int,   help="Max trades por día (default: 1)")
    parser.add_argument("--bias",            default="BOTH",         help="BULLISH | BEARISH | BOTH")
    parser.add_argument("--no-day-filter",   action="store_true",   help="No saltar Mon/Tue (peor WR)")
    parser.add_argument("--no-window-b",     action="store_true",   help="Excluir ventana B (9:30-10:00 ET)")
    parser.add_argument("--be-trigger",      default=0.5, type=float, help="Activar BE a X*R (default: 0.5)")
    parser.add_argument("--min-displacement",default=0.0, type=float, help="Body mín vela creación FVG en pts (default: 0 = off)")
    parser.add_argument("--auto-bias",       action="store_true",    help="Bias diario automático (prev close + weekly premium/discount)")
    parser.add_argument("--slippage",        default=0.0, type=float, help="Slippage por lado en %% del precio (default: 0 = off)")
    parser.add_argument("--commission",      default=0.0, type=float, help="Comisión fija por trade round-trip en USD (default: 0)")
    parser.add_argument("--next-bar-entry",  action="store_true",    help="Entrar al open de la vela siguiente (más realista)")
    parser.add_argument("--vwap-filter",     action="store_true",    help="Solo BUY bajo VWAP (discount), solo SELL sobre VWAP (premium)")
    parser.add_argument("--partial-exit",    default=0.0, type=float, help="Cerrar 50%% posición en X*R y dejar runner al TP (0 = off)")
    parser.add_argument("--ib-filter",       action="store_true",    help="Initial Balance: post-10:30 señal debe romper el rango 9:30-10:30")
    parser.add_argument("--delta-filter",    action="store_true",    help="Delta proxy: vela de retest debe cerrar en mitad favorable")
    parser.add_argument("--lvn-filter",      action="store_true",    help="LVN filter: IFVG debe estar en Low Volume Node del VP anterior")
    parser.add_argument("--order-flow",      action="store_true",    help="Aplica los 3 filtros order flow: IB + delta + LVN (necesita volumen)")
    parser.add_argument("--dynamic-sizing",  action="store_true",    help="1.5x risk en setups LVN-confirmados (Volume Profile del día anterior)")
    parser.add_argument("--ultra",           action="store_true",    help="Modo ultra-realista: slippage=0.01%% + limit-entry + auto-bias + vwap")
    parser.add_argument("--json",     action="store_true", help="Output JSON")
    parser.add_argument("--plot",     action="store_true", help="Mostrar equity curve ASCII")
    parser.add_argument("--save",     action="store_true", help="Guardar trades en backtest_result.json")
    args = parser.parse_args()
    args.bias = args.bias.upper()

    # --order-flow: activa los 3 filtros order flow juntos
    if getattr(args, "order_flow", False):
        args.ib_filter    = True
        args.delta_filter = True
        args.lvn_filter   = True
        print(f"[ORDER-FLOW] IB filter + Delta proxy + LVN filter activados")

    # --ultra: aplica slippage + next-bar-entry + auto-bias automáticamente
    if args.ultra:
        args.slippage         = args.slippage or 0.01
        args.next_bar_entry   = False
        args.auto_bias        = True
        args.vwap_filter      = True
        args.be_trigger       = args.be_trigger if args.be_trigger != 0.5 else 99   # sin BE en ultra
        args.rr               = args.rr if args.rr != 2.0 else 2.5                  # RR 2.5 por defecto
        args.min_displacement = args.min_displacement or 0.35
        print(f"[ULTRA] slippage={args.slippage}%/lado | auto-bias | VWAP | sin-BE | RR={args.rr} | disp≥{args.min_displacement}")

    print(f"\n[BACKTEST] {args.symbol} | {args.days}d | bias={args.bias} | RR {args.rr} | Stop {args.stop_pct}% | Risk {args.risk_pct}%\n")

    # 1. Download (or load) data
    try:
        if args.data_file:
            candles = load_from_file(args.data_file)
            print(f"[BACKTEST] Modo out-of-sample: datos de {args.data_file}")
        else:
            candles = download_data(args.symbol, args.days)
    except Exception as e:
        print(f"[ERROR] {e}"); sys.exit(1)

    # 2. Detect signals
    print(f"[DETECT] Corriendo detector IFVG en {len(candles)} velas...")
    all_signals = detect_ifvg(candles)
    print(f"[DETECT] {len(all_signals)} senales IFVG encontradas (sin filtros)")

    # Bias filter
    if args.bias in ("BULLISH", "BEARISH"):
        direction = "BUY" if args.bias == "BULLISH" else "SELL"
        all_signals = [s for s in all_signals if s["action"] == direction]
        print(f"[DETECT] {len(all_signals)} senales tras filtro bias={args.bias}")

    # Count signals in kill zone
    kz_signals = [s for s in all_signals if is_in_kill_zone(candles[s["bar_index"]]["time"],
                                                              no_window_b=args.no_window_b)]
    print(f"[DETECT] {len(kz_signals)} senales dentro de kill zone")

    # Gap filter descartado: señales de gaps pequeños tienen mejor WR en IFVG
    # (IFVG es counter-trend — el gap grande = movimiento extremo = retest más difícil)

    if not all_signals:
        print("\n[WARN] Sin senales -- prueba con mas dias o sin filtro KZ (--no-kz)")
        sys.exit(0)

    # 3. Build news blackout set
    blackout_set = set()
    if not getattr(args, "no_news", False):
        if args.data_file:
            # data-file: derive date range from candles themselves
            if candles:
                cs, ce = candles[0]["time"], candles[-1]["time"]
                days_span = max(1, (ce - cs) // 86400)
                print(f"[NEWS] Calendario histórico para data-file ({days_span}d)...")
                blackout_set = build_historical_blackout_set(cs, ce)
                print(f"[NEWS] {len(blackout_set)} minutos en blackout ({days_span}d)")
        else:
            # Normal: ForexFactory para ≤60d, histórico aproximado para >60d
            print(f"[NEWS] Cargando blackout de noticias...")
            blackout_set = build_news_blackout_set(args.days)
            print(f"[NEWS] {len(blackout_set)} minutos en blackout en {args.days}d")

    # 4a. Build order flow maps (IB + VP) if needed
    ib_map_data = None
    vp_map_data = None
    if getattr(args, "ib_filter", False):
        print(f"[IB] Calculando Initial Balance (9:30-10:30 ET) por sesión...")
        ib_map_data = build_ib_map(candles)
        print(f"[IB] {len(ib_map_data)} sesiones con Initial Balance")
    if getattr(args, "lvn_filter", False) or getattr(args, "dynamic_sizing", False):
        print(f"[VP] Calculando Volume Profile por sesión (LVN / dynamic sizing)...")
        vp_map_data = build_vp_map(candles)
        print(f"[VP] {len(vp_map_data)} sesiones con Volume Profile")

    # 4b. Build auto-bias map (if requested)
    auto_bias_map = None
    if getattr(args, "auto_bias", False):
        print(f"[BIAS] Calculando daily bias automatico (prev close + weekly premium/discount)...")
        auto_bias_map = build_auto_bias_map(candles)
        bullish_days = sum(1 for v in auto_bias_map.values() if v == "BULLISH")
        bearish_days = sum(1 for v in auto_bias_map.values() if v == "BEARISH")
        neutral_days = sum(1 for v in auto_bias_map.values() if v == "NEUTRAL")
        print(f"[BIAS] {bullish_days} dias BULLISH | {bearish_days} BEARISH | {neutral_days} NEUTRAL (skip)")

    # 5. Simulate trades
    print(f"[SIM] Simulando trades...")
    skip_days = () if args.no_day_filter else (0, 1)  # Mon+Tue skipped by default
    trades = simulate_trades(
        candles, all_signals,
        rr=args.rr, stop_pct=args.stop_pct,
        account=args.account, risk_pct=args.risk_pct / 100,
        kz_filter=not args.no_kz,
        news_filter=not getattr(args, "no_news", False),
        blackout_set=blackout_set,
        max_per_day=args.max_per_day,
        skip_weekdays=skip_days,
        be_trigger_rr=args.be_trigger,
        no_window_b=args.no_window_b,
        min_displacement=args.min_displacement,
        auto_bias_map=auto_bias_map,
        slippage_pct=args.slippage,
        commission_usd=args.commission,
        next_bar_entry=getattr(args, "next_bar_entry", False),
        vwap_filter=getattr(args, "vwap_filter", False),
        partial_exit_r=getattr(args, "partial_exit", 0.0),
        ib_filter=getattr(args, "ib_filter", False),
        delta_filter=getattr(args, "delta_filter", False),
        lvn_filter=getattr(args, "lvn_filter", False),
        ib_map=ib_map_data,
        vp_map=vp_map_data,
    )
    bias_label = "AUTO" if auto_bias_map is not None else args.bias
    real_label  = f" | slippage={args.slippage}% | comm=${args.commission}" if args.slippage or args.commission else ""
    print(f"[SIM] Filtros activos: day_filter={'Mon+Tue' if skip_days else 'OFF'} | "
          f"BE@{args.be_trigger}R | window_b={'OFF' if args.no_window_b else 'ON'} | "
          f"displacement≥{args.min_displacement}pts | bias={bias_label}{real_label}")
    print(f"[SIM] {len(trades)} trades ejecutados")

    # 4. Metrics
    metrics = compute_metrics(trades, args.account)
    metrics["total_signals"]  = len(all_signals)
    metrics["signals_in_kz"]  = len(kz_signals)

    # 5. Output
    if args.json:
        print(json.dumps({"metrics": metrics, "trades": trades}, indent=2))
    else:
        print_report(metrics, trades)
        if args.plot:
            print_equity_curve(trades)

    if args.save:
        out = Path("backtest_result.json")
        out.write_text(json.dumps({"metrics": metrics, "trades": trades}, indent=2))
        print(f"\n[SAVED] {out.absolute()}")

    return metrics


if __name__ == "__main__":
    main()
