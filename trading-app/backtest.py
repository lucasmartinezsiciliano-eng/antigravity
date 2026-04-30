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

def is_in_kill_zone(ts_unix: int) -> bool:
    """Ventanas NY: A 8:30-9:00 + B 9:30-10:30 + Silver Bullet 10:00-11:00."""
    dt = datetime.fromtimestamp(ts_unix, tz=NY)
    if dt.weekday() >= 5:  # weekend
        return False
    t = dt.time()
    win_a = dtime(8, 30) <= t <= dtime(9, 0)
    win_b = dtime(9, 30) <= t <= dtime(10, 30)
    sb    = dtime(10, 0) <= t <= dtime(11, 0)
    return win_a or win_b or sb


# ── Data download ─────────────────────────────────────────────────────────────
YF_MAP = {
    "NQ1!": "^NDX", "ES1!": "^GSPC",
    "MNQ1!": "^NDX", "MES1!": "^GSPC",
    "AAPL": "AAPL", "MSFT": "MSFT", "NVDA": "NVDA",
}

def download_data(symbol: str, days: int = 180) -> list:
    """Descarga velas 5m de Yahoo Finance. Máx ~60 días para 5m."""
    import yfinance as yf
    yf_sym = YF_MAP.get(symbol, symbol)

    # Yahoo Finance limita 5m a ~60 días, 1h a ~730 días
    if days <= 60:
        interval, period = "5m", f"{days}d"
    else:
        # Para backtest largo: usar 1h y simular señales en cada barra
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


# ── Trade simulator ───────────────────────────────────────────────────────────
def build_news_blackout_set(days: int, blackout_min: int = 15) -> set:
    """
    Construye un set de timestamps (minuto exacto) en blackout de noticias.
    NOTA: ForexFactory solo provee la semana actual (7 días). Para backtests
    históricos el filtro solo cubre eventos de esta semana que caigan en el rango.
    Usa news_calendar.py si disponible; si no, devuelve set vacío.
    """
    try:
        from news_calendar import fetch_calendar
        events = fetch_calendar()
        now_unix = __import__("time").time()
        cutoff   = now_unix - days * 86400
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


BE_TRIGGER_RR = 1.0   # mueve SL a entry cuando precio alcanza 1:1
BE_BUFFER_R   = 0.08  # SL va a entry + 8% del stop (pequeña ganancia garantizada, no $0 exacto)

def simulate_trades(
    candles: list,
    signals: list,
    rr: float = 2.0,
    stop_pct: float = 0.5,
    account: float = 50_000.0,
    risk_pct: float = 0.01,
    kz_filter: bool = True,
    max_per_day: int = 2,
    news_filter: bool = True,
    blackout_set: set = None,
) -> list:
    """
    Simula ejecución de señales sobre datos históricos.
    Entrada en el cierre de la vela de señal.
    SL = stop_pct% del precio. TP = SL * rr.
    Gestión: BE a 1:1 con buffer +8% del stop — convierte cierres $0 en pequeña ganancia.
    news_filter=True omite trades en ventana ±15min de eventos HIGH impact.
    """
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
        if kz_filter and not is_in_kill_zone(bar_time):
            continue

        # News blackout filter
        if news_filter and is_news_blackout(bar_time, blackout_set):
            continue

        # Daily limit
        dt_ny = datetime.fromtimestamp(bar_time, tz=NY)
        day_key = dt_ny.date()
        if day_count.get(day_key, 0) >= max_per_day:
            continue

        # Skip if position open
        if open_pos:
            continue

        entry = signal_bar["close"]
        action = sig["action"]
        stop_d = entry * stop_pct / 100
        sl = entry - stop_d if action == "BUY" else entry + stop_d
        tp = entry + stop_d * rr if action == "BUY" else entry - stop_d * rr
        size_usd = account * risk_pct
        qty = max(1, int(size_usd / stop_d)) if stop_d > 0 else 1

        open_pos = {
            "action": action, "entry": entry, "sl": sl, "tp": tp,
            "qty": qty, "stop_d": stop_d, "bar_idx": bar_idx,
            "ts": bar_time, "be_triggered": False,
        }

        # Simulate forward from next bar
        result = None
        for future_bar in candles[bar_idx + 1:bar_idx + 200]:
            h, l = future_bar["high"], future_bar["low"]

            # Break-even at 1:1 with small buffer (converts $0 closes into tiny gain)
            if not open_pos["be_triggered"]:
                if action == "BUY"  and h >= entry + stop_d * BE_TRIGGER_RR:
                    open_pos["sl"] = entry + stop_d * BE_BUFFER_R
                    open_pos["be_triggered"] = True
                elif action == "SELL" and l <= entry - stop_d * BE_TRIGGER_RR:
                    open_pos["sl"] = entry - stop_d * BE_BUFFER_R
                    open_pos["be_triggered"] = True

            # Check SL
            if action == "BUY"  and l <= open_pos["sl"]:
                pnl = (open_pos["sl"] - entry) * qty
                result = {"exit": open_pos["sl"], "reason": "BE" if open_pos["be_triggered"] else "SL", "pnl": pnl}
                break
            elif action == "SELL" and h >= open_pos["sl"]:
                pnl = (entry - open_pos["sl"]) * qty
                result = {"exit": open_pos["sl"], "reason": "BE" if open_pos["be_triggered"] else "SL", "pnl": pnl}
                break

            # Check TP
            if action == "BUY"  and h >= tp:
                pnl = (tp - entry) * qty
                result = {"exit": tp, "reason": "TP", "pnl": pnl}
                break
            elif action == "SELL" and l <= tp:
                pnl = (entry - tp) * qty
                result = {"exit": tp, "reason": "TP", "pnl": pnl}
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
    parser.add_argument("--symbol",   default="NQ1!",    help="Símbolo (NQ1!, ES1!, AAPL...)")
    parser.add_argument("--days",     default=60,  type=int, help="Días históricos (max 60 para 5m)")
    parser.add_argument("--rr",       default=2.0, type=float, help="RR objetivo (default 2.0)")
    parser.add_argument("--stop-pct", default=0.5, type=float, help="Stop %% del precio (default 0.5)")
    parser.add_argument("--risk-pct", default=1.0, type=float, help="Riesgo %% por trade (default 1.0)")
    parser.add_argument("--account",  default=50000.0, type=float, help="Cuenta inicial USD")
    parser.add_argument("--no-kz",    action="store_true", help="Ignorar filtro kill zone")
    parser.add_argument("--no-news",  action="store_true", help="Ignorar blackout de noticias")
    parser.add_argument("--bias",     default="BOTH",      help="BULLISH | BEARISH | BOTH (default: BOTH)")
    parser.add_argument("--json",     action="store_true", help="Output JSON")
    parser.add_argument("--plot",     action="store_true", help="Mostrar equity curve ASCII")
    parser.add_argument("--save",     action="store_true", help="Guardar trades en backtest_result.json")
    args = parser.parse_args()
    args.bias = args.bias.upper()

    print(f"\n[BACKTEST] {args.symbol} | {args.days}d | bias={args.bias} | RR {args.rr} | Stop {args.stop_pct}% | Risk {args.risk_pct}%\n")

    # 1. Download data
    try:
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
    kz_signals = [s for s in all_signals if is_in_kill_zone(candles[s["bar_index"]]["time"])]
    print(f"[DETECT] {len(kz_signals)} senales dentro de kill zone")

    if not all_signals:
        print("\n[WARN] Sin senales -- prueba con mas dias o sin filtro KZ (--no-kz)")
        sys.exit(0)

    # 3. Build news blackout set
    blackout_set = set()
    if not getattr(args, "no_news", False):
        print(f"[NEWS] Cargando blackout de noticias (ForexFactory)...")
        blackout_set = build_news_blackout_set(args.days)
        print(f"[NEWS] {len(blackout_set)} minutos en blackout en {args.days}d")

    # 4. Simulate trades
    print(f"[SIM] Simulando trades...")
    trades = simulate_trades(
        candles, all_signals,
        rr=args.rr, stop_pct=args.stop_pct,
        account=args.account, risk_pct=args.risk_pct / 100,
        kz_filter=not args.no_kz,
        news_filter=not getattr(args, "no_news", False),
        blackout_set=blackout_set,
        max_per_day=2,
    )
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
