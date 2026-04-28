"""
Beta test — simulates TradingView webhook signals.
Fires real HTTP requests to the local webhook-api.

Usage:
    python test_signals.py                     # fire one IFVG long on NQ
    python test_signals.py --symbol AAPL       # stock signal
    python test_signals.py --scenario session  # full session simulation
    python test_signals.py --scenario stress   # stress test: 10 rapid signals
"""

import argparse
import datetime
import json
import random
import sys
import time
import os

import requests

BASE_URL = os.getenv("WEBHOOK_URL", "http://localhost:8000")
API_KEY  = os.getenv("WEBHOOK_API_KEY", "")

HEADERS = {"X-Api-Key": API_KEY, "Content-Type": "application/json"}


# ── Signal templates ──────────────────────────────────────────────────────────

def make_signal(action: str, symbol: str = "NQ1!", close: float = 19250.0,
                reason: str = "IFVG_long") -> dict:
    return {
        "action":    action,
        "symbol":    symbol,
        "timeframe": "1",
        "close":     close,
        "time":      datetime.datetime.utcnow().isoformat() + "Z",
        "reason":    reason,
    }


SCENARIOS = {
    "long": [
        make_signal("BUY", "NQ1!", 19250.0, "IFVG_long"),
    ],
    "short": [
        make_signal("SELL", "NQ1!", 19800.0, "IFVG_short"),
    ],
    "session": [
        # Simulates a typical NY AM session: 2 signals, 1 valid + 1 filtered
        make_signal("BUY",  "NQ1!", 19300.0, "IFVG_long"),
        make_signal("SELL", "NQ1!", 19280.0, "IFVG_short"),  # should be filtered (max 2 trades or wrong bias)
    ],
    "stocks": [
        make_signal("BUY",  "AAPL",  172.5,  "IFVG_long"),
        make_signal("SELL", "NVDA", 875.0,  "IFVG_short"),
        make_signal("BUY",  "MSFT",  415.0,  "IFVG_long"),
    ],
    "stress": [make_signal(
        random.choice(["BUY", "SELL"]),
        random.choice(["NQ1!", "ES1!", "AAPL", "MSFT"]),
        random.uniform(100, 20000),
        "IFVG_stress_test"
    ) for _ in range(10)],
}


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def send_signal(signal: dict, verbose: bool = True) -> dict | None:
    try:
        r = requests.post(f"{BASE_URL}/webhook", json=signal, headers=HEADERS, timeout=5)
        result = {"status_code": r.status_code, "body": r.json()}
        if verbose:
            icon = "✓" if r.status_code == 200 else "✗"
            print(f"  {icon} {signal['action']} {signal['symbol']} @ {signal['close']} → {r.status_code} {r.json()}")
        return result
    except Exception as e:
        print(f"  ✗ Request failed: {e}")
        return None


def check_health() -> bool:
    try:
        r = requests.get(f"{BASE_URL}/status", timeout=3)
        data = r.json()
        ok = r.status_code == 200 and data.get("redis") == "ok"
        status = "online" if ok else "degraded"
        print(f"  Health: {status} | Redis: {data.get('redis')} | API: {r.status_code}")
        return ok
    except Exception as e:
        print(f"  Health check failed: {e}")
        return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="IFVG Trading Bot — webhook test signals")
    parser.add_argument("--scenario", default="long",
                        choices=list(SCENARIOS.keys()),
                        help="Scenario to run")
    parser.add_argument("--symbol",  default=None, help="Override symbol")
    parser.add_argument("--action",  default=None, choices=["BUY", "SELL"])
    parser.add_argument("--price",   default=None, type=float)
    parser.add_argument("--delay",   default=1.0,  type=float,
                        help="Seconds between signals in multi-signal scenarios")
    args = parser.parse_args()

    print(f"\n=== IFVG Trading Bot — Test Signals ===")
    print(f"Target: {BASE_URL}")
    print()

    # Health check first
    print("[ Health ]")
    if not check_health():
        print("  WARNING: API may be down. Sending anyway...")
    print()

    # Resolve signals
    if args.symbol or args.action or args.price:
        signals = [make_signal(
            args.action or "BUY",
            args.symbol  or "NQ1!",
            args.price   or 19250.0,
            "manual_test"
        )]
        scenario_name = "custom"
    else:
        scenario_name = args.scenario
        signals = SCENARIOS[scenario_name]

    print(f"[ Scenario: {scenario_name} — {len(signals)} signal(s) ]")
    for i, sig in enumerate(signals):
        send_signal(sig)
        if i < len(signals) - 1:
            time.sleep(args.delay)

    print("\nDone. Check trades.jsonl for execution log.")


if __name__ == "__main__":
    main()
