"""
Trading performance analytics.
Reads trades.jsonl and computes the metrics from Lo-Que-Necesitas-Para-Operar-Bien:
  - Win rate, Profit Factor, Avg RR, Max Drawdown
  - Compares against thresholds (PF≥1.5, WR≥50%, DD<20%)
  - Outputs structured recommendations (used by self-improve agent)

Usage:
    python analytics.py                  # full report
    python analytics.py --json           # machine-readable (for agent)
    python analytics.py --days 30        # last 30 days only
"""

import json
import argparse
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import defaultdict


LOG_FILE = Path(os.getenv("LOG_FILE", "trades.jsonl"))

# ── Thresholds (from Lo-Que-Necesitas-Para-Operar-Bien) ──────────────────────
THRESHOLDS = {
    "profit_factor":    {"min": 1.5, "excellent": 2.0},
    "win_rate":         {"min": 0.50},
    "avg_rr":           {"min": 2.0},
    "max_drawdown_pct": {"max": 0.20},
    "min_trades":       30,   # minimum before conclusions are valid
}


# ── Parse log ────────────────────────────────────────────────────────────────

def load_trades(days: int = None) -> list[dict]:
    if not LOG_FILE.exists():
        return []
    cutoff = None
    if days:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    trades = []
    with open(LOG_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if rec.get("event") not in ("order_placed", "trade_closed"):
                    continue
                if cutoff:
                    ts = datetime.fromisoformat(rec["ts"].replace("Z", "+00:00"))
                    if ts < cutoff:
                        continue
                trades.append(rec)
            except Exception:
                continue
    return trades


# ── Metrics ──────────────────────────────────────────────────────────────────

def compute_metrics(trades: list[dict]) -> dict:
    if not trades:
        return {}

    closed = [t for t in trades if t.get("event") == "trade_closed"]
    if not closed:
        # If no closed trades yet, estimate from open orders (no actual PnL)
        return {"note": "No closed trades yet — metrics require completed trades"}

    wins   = [t for t in closed if t.get("pnl", 0) > 0]
    losses = [t for t in closed if t.get("pnl", 0) <= 0]

    total_wins_usd   = sum(t.get("pnl", 0) for t in wins)
    total_losses_usd = abs(sum(t.get("pnl", 0) for t in losses))

    win_rate        = len(wins) / len(closed) if closed else 0
    profit_factor   = total_wins_usd / total_losses_usd if total_losses_usd > 0 else float("inf")
    avg_win         = total_wins_usd / len(wins) if wins else 0
    avg_loss        = total_losses_usd / len(losses) if losses else 0
    avg_rr          = avg_win / avg_loss if avg_loss > 0 else 0

    # Max drawdown (running peak → trough)
    equity_curve = []
    running = 0
    for t in sorted(closed, key=lambda x: x["ts"]):
        running += t.get("pnl", 0)
        equity_curve.append(running)
    peak = equity_curve[0]
    max_dd = 0
    for val in equity_curve:
        peak = max(peak, val)
        dd = (peak - val) / abs(peak) if peak != 0 else 0
        max_dd = max(max_dd, dd)

    # Per-symbol breakdown
    by_symbol = defaultdict(lambda: {"trades": 0, "wins": 0, "pnl": 0.0})
    for t in closed:
        sym = t.get("symbol", "?")
        by_symbol[sym]["trades"] += 1
        by_symbol[sym]["pnl"] += t.get("pnl", 0)
        if t.get("pnl", 0) > 0:
            by_symbol[sym]["wins"] += 1

    # Consecutive losses max
    max_consec_losses = 0
    cur = 0
    for t in sorted(closed, key=lambda x: x["ts"]):
        if t.get("pnl", 0) <= 0:
            cur += 1
            max_consec_losses = max(max_consec_losses, cur)
        else:
            cur = 0

    return {
        "total_trades":         len(closed),
        "wins":                 len(wins),
        "losses":               len(losses),
        "win_rate":             round(win_rate, 4),
        "profit_factor":        round(profit_factor, 2),
        "avg_win_usd":          round(avg_win, 2),
        "avg_loss_usd":         round(avg_loss, 2),
        "avg_rr":               round(avg_rr, 2),
        "total_pnl":            round(total_wins_usd - total_losses_usd, 2),
        "max_drawdown_pct":     round(max_dd, 4),
        "max_consecutive_loss": max_consec_losses,
        "by_symbol":            {k: dict(v) for k, v in by_symbol.items()},
    }


# ── Recommendations ──────────────────────────────────────────────────────────

def generate_recommendations(metrics: dict) -> list[dict]:
    """
    Compares metrics against thresholds and generates actionable recommendations.
    Each recommendation has: area, severity (info/warn/critical), message, action.
    """
    if not metrics or "note" in metrics:
        return [{"area": "data", "severity": "info",
                 "message": "Not enough closed trades yet for recommendations.",
                 "action": "Continue paper trading until 30+ closed trades."}]

    recs = []
    n = metrics["total_trades"]
    T = THRESHOLDS

    if n < T["min_trades"]:
        recs.append({"area": "sample_size", "severity": "info",
                     "message": f"Only {n} trades — need {T['min_trades']} for valid conclusions.",
                     "action": f"Keep trading. {T['min_trades'] - n} more trades needed."})

    # Profit Factor
    pf = metrics["profit_factor"]
    if pf < 1.0:
        recs.append({"area": "edge", "severity": "critical",
                     "message": f"Profit Factor {pf:.2f} < 1.0 — losing money structurally.",
                     "action": "STOP trading. Review: daily bias check, IFVG one-FVG rule, entry timing."})
    elif pf < T["profit_factor"]["min"]:
        recs.append({"area": "edge", "severity": "warn",
                     "message": f"Profit Factor {pf:.2f} below minimum {T['profit_factor']['min']}.",
                     "action": "Increase MIN_RR in .env (try 2.5). Check if taking B-quality setups."})
    elif pf >= T["profit_factor"]["excellent"]:
        recs.append({"area": "edge", "severity": "info",
                     "message": f"Excellent Profit Factor: {pf:.2f} — system has strong edge.",
                     "action": "Consider scaling: increase ACCOUNT_SIZE or add second symbol."})

    # Win Rate
    wr = metrics["win_rate"]
    if wr < 0.40:
        recs.append({"area": "win_rate", "severity": "critical",
                     "message": f"Win rate {wr:.0%} is critically low.",
                     "action": "Review: only trade when Daily Bias is clear. No neutral days. Check IFVG one-FVG rule."})
    elif wr < T["win_rate"]["min"] and metrics["avg_rr"] < 2.0:
        recs.append({"area": "win_rate", "severity": "warn",
                     "message": f"Win rate {wr:.0%} + avg RR {metrics['avg_rr']:.1f} = negative EV.",
                     "action": "Need either WR≥50% or RR≥2:1. Currently have neither. Pause and review."})

    # RR
    rr = metrics["avg_rr"]
    if rr < 1.5:
        recs.append({"area": "rr", "severity": "warn",
                     "message": f"Average RR {rr:.1f} below target 2:1.",
                     "action": "Set MIN_RR=2.0 in .env. Check if TP is being hit or manually closed early."})

    # Drawdown
    dd = metrics["max_drawdown_pct"]
    if dd > T["max_drawdown_pct"]["max"]:
        recs.append({"area": "drawdown", "severity": "critical",
                     "message": f"Max drawdown {dd:.0%} exceeds limit {T['max_drawdown_pct']['max']:.0%}.",
                     "action": "Reduce MAX_RISK_PCT to 0.5% immediately. Check MAX_CONSECUTIVE_LOSSES setting."})
    elif dd > 0.10:
        recs.append({"area": "drawdown", "severity": "warn",
                     "message": f"Drawdown {dd:.0%} approaching limit.",
                     "action": "Monitor closely. Consider reducing to 0.75% risk per trade."})

    # Consecutive losses
    cl = metrics["max_consecutive_loss"]
    if cl >= 5:
        recs.append({"area": "psychology", "severity": "warn",
                     "message": f"Max {cl} consecutive losses — possible system degradation or poor condition.",
                     "action": "Check: did consecutive losses happen on news days? Wrong bias? Review those trades."})

    # Per-symbol
    for sym, data in metrics.get("by_symbol", {}).items():
        sym_wr = data["wins"] / data["trades"] if data["trades"] > 0 else 0
        if data["trades"] >= 5 and sym_wr < 0.35:
            recs.append({"area": f"symbol_{sym}", "severity": "warn",
                         "message": f"{sym} win rate {sym_wr:.0%} over {data['trades']} trades.",
                         "action": f"Consider pausing {sym}. Check if sector bias is aligned."})

    if not recs:
        recs.append({"area": "overall", "severity": "info",
                     "message": "All metrics within acceptable range.",
                     "action": "System is performing well. Continue current settings."})

    return recs


# ── Suggested .env changes ────────────────────────────────────────────────────

def suggest_env_changes(metrics: dict, current_env: dict) -> dict[str, str]:
    """
    Returns a dict of .env key → suggested value based on metrics.
    Only safe, bounded changes. Never changes IBKR credentials.
    """
    suggestions = {}
    if not metrics or "note" in metrics:
        return suggestions

    pf = metrics.get("profit_factor", 0)
    dd = metrics.get("max_drawdown_pct", 0)
    rr = metrics.get("avg_rr", 0)

    current_risk = float(current_env.get("MAX_RISK_PCT", 0.01))

    # Reduce risk if drawdown is high
    if dd > 0.15 and current_risk > 0.005:
        suggestions["MAX_RISK_PCT"] = "0.005"

    # Increase RR target if currently underperforming
    if rr < 1.5 and pf < 1.5:
        suggestions["MIN_RR"] = "2.5"

    # Tighten daily loss limit if drawdown is large
    if dd > 0.10:
        suggestions["MAX_DAILY_LOSS_PCT"] = "0.02"

    return suggestions


# ── Report printer ────────────────────────────────────────────────────────────

def print_report(metrics: dict, recs: list[dict], env_changes: dict):
    SEV_ICONS = {"critical": "🔴", "warn": "🟡", "info": "🟢"}

    print("\n" + "="*60)
    print("  IFVG Trading Bot — Performance Report")
    print("="*60)

    if not metrics or "note" in metrics:
        print(f"\n  {metrics.get('note', 'No data')}")
        return

    n = metrics["total_trades"]
    print(f"\n  Trades: {n}  |  W/L: {metrics['wins']}/{metrics['losses']}")
    print(f"  Win Rate:      {metrics['win_rate']:.1%}  (target: ≥50%)")
    print(f"  Profit Factor: {metrics['profit_factor']:.2f}  (target: ≥1.5, excellent: ≥2.0)")
    print(f"  Avg RR:        {metrics['avg_rr']:.1f}:1  (target: ≥2.0)")
    print(f"  Total PnL:     ${metrics['total_pnl']:+.2f}")
    print(f"  Max Drawdown:  {metrics['max_drawdown_pct']:.1%}  (limit: 20%)")
    print(f"  Max Consec L:  {metrics['max_consecutive_loss']}")

    if metrics.get("by_symbol"):
        print("\n  By symbol:")
        for sym, d in metrics["by_symbol"].items():
            wr = d['wins']/d['trades'] if d['trades'] > 0 else 0
            print(f"    {sym:<10} {d['trades']} trades  WR {wr:.0%}  PnL ${d['pnl']:+.2f}")

    print("\n" + "-"*60)
    print("  Recommendations")
    print("-"*60)
    for r in recs:
        icon = SEV_ICONS.get(r["severity"], "•")
        print(f"\n  {icon} [{r['area'].upper()}] {r['message']}")
        print(f"     → {r['action']}")

    if env_changes:
        print("\n" + "-"*60)
        print("  Suggested .env changes")
        print("-"*60)
        for k, v in env_changes.items():
            print(f"  {k} = {v}")
        print("\n  Apply with: python analytics.py --apply")

    print("\n" + "="*60 + "\n")


def load_env(path: str = ".env") -> dict:
    env = {}
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    env[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    return env


def apply_env_changes(changes: dict, path: str = ".env"):
    env = load_env(path)
    env.update(changes)
    lines = []
    for k, v in env.items():
        lines.append(f"{k}={v}")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  Applied {len(changes)} change(s) to {path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days",  type=int, default=None, help="Analyze last N days")
    parser.add_argument("--json",  action="store_true", help="Output JSON for agent consumption")
    parser.add_argument("--apply", action="store_true", help="Auto-apply .env recommendations")
    args = parser.parse_args()

    trades  = load_trades(args.days)
    metrics = compute_metrics(trades)
    recs    = generate_recommendations(metrics)
    env     = load_env()
    changes = suggest_env_changes(metrics, env)

    if args.json:
        print(json.dumps({
            "metrics": metrics,
            "recommendations": recs,
            "suggested_env_changes": changes,
        }, indent=2))
        return

    print_report(metrics, recs, changes)

    if args.apply and changes:
        apply_env_changes(changes)


if __name__ == "__main__":
    main()
