"""
optimize.py — Self-Improve Parameter Optimizer
===============================================
Grid search sobre los parametros clave del bot IFVG.
Corre el backtester para cada combinacion, rankea por score,
y aplica automaticamente la mejor configuracion al bot en vivo.

Uso:
    python optimize.py                   # grid completo (NQ, 60d)
    python optimize.py --apply           # aplica mejor config al bot
    python optimize.py --symbol ES1!     # otro instrumento
    python optimize.py --days 60         # dias de datos
    python optimize.py --json            # output JSON

Score = profit_factor * win_rate * (1 - drawdown/100)
Constrainst: max_drawdown < 20%, trades >= 10
"""

import io
import sys
import json
import time
import argparse
import itertools
import subprocess
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Parameter grid ────────────────────────────────────────────────────────────
# Optimizar: cuanto es el stop optimo y el RR optimo
# Bias se deja BOTH porque en produccion depende del analisis humano diario
PARAM_GRID = {
    "stop_pct": [0.3, 0.4, 0.5, 0.6, 0.8, 1.0],
    "rr":       [1.5, 2.0, 2.5, 3.0],
}

# Fijos para todos los runs
FIXED = {
    "bias":     "BOTH",   # simula mezcla realista de dias bull/bear
    "risk_pct": 1.0,
}

# Constraints para que un resultado sea valido
MIN_TRADES    = 10    # minimo de trades para ser estadisticamente relevante
MAX_DRAWDOWN  = 20.0  # maximo drawdown aceptable (%)
MIN_WIN_RATE  = 0.25  # minimo win rate (25% con RR alto puede ser rentable)


def score(m: dict) -> float:
    """
    Score compuesto: premia PF alto, WR alto, DD bajo.
    Formula: PF * WR * (1 - DD/100)
    Un sistema con PF=2.0, WR=50%, DD=10% → score = 2.0 * 0.5 * 0.9 = 0.90
    """
    pf = m.get("profit_factor") or 0
    wr = m.get("win_rate") or 0
    dd = m.get("max_drawdown_pct") or 100
    return round(pf * wr * (1 - dd / 100), 4)


def run_backtest(symbol: str, days: int, stop_pct: float, rr: float,
                 bias: str, risk_pct: float) -> dict | None:
    """Lanza backtest.py como subprocess y parsea el JSON de salida."""
    cmd = [
        sys.executable, "backtest.py",
        "--symbol",   symbol,
        "--days",     str(days),
        "--stop-pct", str(stop_pct),
        "--rr",       str(rr),
        "--bias",     bias,
        "--risk-pct", str(risk_pct),
        "--json",
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=120, cwd=str(Path(__file__).parent),
            encoding="utf-8", errors="replace",
        )
        stdout = result.stdout
        # Extract JSON — find first { and parse from there
        idx = stdout.find('{')
        if idx >= 0:
            try:
                data, _ = json.JSONDecoder().raw_decode(stdout, idx)
                return data.get("metrics", {})
            except Exception:
                pass
        return None
    except (subprocess.TimeoutExpired, Exception):
        return None


def apply_to_bot(best: dict, bot_url: str = "http://localhost:8000"):
    """Envia los mejores parametros al bot en vivo via /api/config."""
    try:
        import urllib.request, urllib.parse
        updates = {
            "STOP_PCT":    best["stop_pct"],
            "MIN_RR":      best["rr"],
        }
        for key, val in updates.items():
            body = json.dumps({"key": key, "value": val}).encode()
            req = urllib.request.Request(
                f"{bot_url}/api/config",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as r:
                resp = json.loads(r.read())
                print(f"  [APPLY] {key} = {val} -> {resp}")
        return True
    except Exception as e:
        print(f"  [APPLY] Error: {e} (bot no disponible)")
        return False


def print_table(results: list):
    """Imprime tabla de resultados ordenada por score."""
    print("\n" + "="*80)
    print("  OPTIMIZATION RESULTS — ranked by score")
    print("="*80)
    print(f"  {'Stop%':>6} {'RR':>5} {'Trades':>7} {'WR':>7} {'PF':>6} {'AvgRR':>7} {'DD%':>6} {'Return':>8} {'Score':>7}")
    print("  " + "-"*75)
    for r in results:
        m = r["metrics"]
        flag = " <-- BEST" if r == results[0] else ""
        pf  = m.get("profit_factor") or 0
        wr  = (m.get("win_rate") or 0) * 100
        dd  = m.get("max_drawdown_pct") or 0
        ret = m.get("return_pct") or 0
        arr = m.get("avg_rr") or 0
        n   = m.get("trades_taken") or 0
        sc  = r["score"]
        print(f"  {r['stop_pct']:>5}% {r['rr']:>5} {n:>7} {wr:>6.1f}% {pf:>6.2f} {arr:>6.2f}x {dd:>5.1f}% {ret:>+7.1f}%  {sc:>6.4f}{flag}")
    print("="*80)


def main():
    parser = argparse.ArgumentParser(description="IFVG Parameter Optimizer")
    parser.add_argument("--symbol",  default="NQ=F")
    parser.add_argument("--days",    default=60,   type=int)
    parser.add_argument("--apply",   action="store_true", help="Aplicar mejor config al bot en vivo")
    parser.add_argument("--json",    action="store_true")
    parser.add_argument("--save",    action="store_true")
    args = parser.parse_args()

    combinations = list(itertools.product(
        PARAM_GRID["stop_pct"],
        PARAM_GRID["rr"],
    ))
    total = len(combinations)

    print(f"\n[OPTIMIZE] {args.symbol} | {args.days}d | {total} combinaciones")
    print(f"[OPTIMIZE] Grid: stop_pct={PARAM_GRID['stop_pct']} x rr={PARAM_GRID['rr']}")
    print(f"[OPTIMIZE] Constraints: trades>={MIN_TRADES}, DD<{MAX_DRAWDOWN}%, WR>={MIN_WIN_RATE*100:.0f}%\n")

    results = []
    t0 = time.time()

    for i, (stop_pct, rr) in enumerate(combinations, 1):
        elapsed = time.time() - t0
        eta = elapsed / i * (total - i) if i > 1 else 0
        print(f"  [{i:02}/{total}] stop={stop_pct}% rr={rr} | elapsed {elapsed:.0f}s ETA {eta:.0f}s", end="\r")

        metrics = run_backtest(
            symbol=args.symbol, days=args.days,
            stop_pct=stop_pct, rr=rr,
            bias=FIXED["bias"], risk_pct=FIXED["risk_pct"],
        )

        if metrics is None or "error" in metrics:
            continue

        n  = metrics.get("trades_taken", 0)
        dd = metrics.get("max_drawdown_pct", 100)
        wr = metrics.get("win_rate", 0)

        # Apply constraints
        if n < MIN_TRADES or dd > MAX_DRAWDOWN or wr < MIN_WIN_RATE:
            continue

        sc = score(metrics)
        results.append({
            "stop_pct": stop_pct,
            "rr":       rr,
            "bias":     FIXED["bias"],
            "score":    sc,
            "metrics":  metrics,
        })

    print(f"\n[OPTIMIZE] Completado en {time.time()-t0:.0f}s | {len(results)}/{total} validos")

    if not results:
        print("[WARN] Ninguna combinacion paso los constraints. Prueba --days 60 sin cambios.")
        sys.exit(0)

    # Rank by score
    results.sort(key=lambda r: r["score"], reverse=True)
    best = results[0]

    if args.json:
        print(json.dumps({"best": best, "all": results[:10]}, indent=2))
    else:
        print_table(results[:15])
        print(f"\n  MEJOR CONFIG:")
        print(f"    STOP_PCT = {best['stop_pct']}%")
        print(f"    MIN_RR   = {best['rr']}")
        print(f"    Score    = {best['score']}")
        m = best["metrics"]
        print(f"    WR={m.get('win_rate',0)*100:.1f}% | PF={m.get('profit_factor',0)} | DD={m.get('max_drawdown_pct',0)}% | Return={m.get('return_pct',0):+.1f}%")

    if args.apply:
        print(f"\n[APPLY] Aplicando mejor config al bot en vivo...")
        applied = apply_to_bot(best)
        if applied:
            print(f"[APPLY] Listo. Restart executor si es necesario.")
            # Log optimization result
            log_path = Path("optimize_history.jsonl")
            with open(log_path, "a", encoding="utf-8") as f:
                from datetime import datetime
                entry = {
                    "ts": datetime.utcnow().isoformat() + "Z",
                    "symbol": args.symbol, "days": args.days,
                    "applied": {"stop_pct": best["stop_pct"], "rr": best["rr"]},
                    "score": best["score"],
                    "metrics": best["metrics"],
                }
                f.write(json.dumps(entry) + "\n")
            print(f"[APPLY] Guardado en optimize_history.jsonl")

    if args.save:
        out = Path("optimize_result.json")
        out.write_text(json.dumps({"best": best, "all": results}, indent=2, ensure_ascii=False))
        print(f"[SAVED] {out.absolute()}")

    return best


if __name__ == "__main__":
    main()
