"""
Trade logger — writes to JSONL + sends Telegram summary.
Each line in trades.jsonl is one trade event (open or close).
"""

import os
import json
import datetime
from pathlib import Path

LOG_FILE = Path(os.getenv("LOG_FILE", "trades.jsonl"))


def _ts() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"


def log_trade(event: str, data: dict):
    """
    event: "signal_received" | "order_placed" | "trade_closed" | "skip" | "error"
    data: dict with trade details
    """
    record = {"ts": _ts(), "event": event, **data}
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def log_skip(reason: str, signal: dict):
    log_trade("skip", {"reason": reason, "signal": signal})


def log_order(signal: dict, qty: int, entry: float, sl: float, tp: float, account: float):
    log_trade("order_placed", {
        "symbol": signal["symbol"],
        "action": signal["action"],
        "qty": qty,
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "rr": round(abs(tp - entry) / abs(sl - entry), 2) if abs(sl - entry) > 0 else 0,
        "risk_usd": round(account * float(os.getenv("MAX_RISK_PCT", "0.01")), 2),
        "reason": signal.get("reason", ""),
    })


def log_error(msg: str, exc: Exception = None):
    log_trade("error", {"msg": msg, "exc": str(exc) if exc else ""})
