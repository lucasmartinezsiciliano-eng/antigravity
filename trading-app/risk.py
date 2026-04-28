"""
Risk management — TJR Day-13 rules.
1% max risk per trade. Daily/weekly loss limits. Max 2 trades/session.
"""

import os
from dataclasses import dataclass, field
from datetime import date


# ── Tick values per instrument ──────────────────────────────────────────────
TICK_VALUE = {
    "NQ":     5.0,   # NQ futures: $5/tick (0.25 pts)  → MNQ: $0.50/tick
    "MNQ":    0.5,
    "ES":    12.5,   # ES futures: $12.50/tick (0.25 pts)
    "MES":    1.25,
    "EURUSD": 1.0,   # Forex: $1 per pip per mini lot (10k units)
    "DEFAULT": 1.0,
}

TICK_SIZE = {
    "NQ":     0.25,
    "MNQ":    0.25,
    "ES":     0.25,
    "MES":    0.25,
    "EURUSD": 0.0001,
    "DEFAULT": 0.01,
}


def get_tick_value(symbol: str) -> float:
    for key in TICK_VALUE:
        if key in symbol:
            return TICK_VALUE[key]
    return TICK_VALUE["DEFAULT"]


def get_tick_size(symbol: str) -> float:
    for key in TICK_SIZE:
        if key in symbol:
            return TICK_SIZE[key]
    return TICK_SIZE["DEFAULT"]


def calculate_position_size(
    account: float,
    risk_pct: float,
    stop_distance: float,   # in price units (e.g. 2.5 pts for NQ = 10 ticks)
    symbol: str = "NQ",
) -> int:
    """
    TJR Day-13: qty = (account × risk%) / (stop_distance / tick_size × tick_value)
    Always returns at least 1.
    """
    tick_sz = get_tick_size(symbol)
    tick_val = get_tick_value(symbol)

    max_risk_usd = account * risk_pct
    ticks_at_risk = stop_distance / tick_sz
    risk_per_contract = ticks_at_risk * tick_val

    if risk_per_contract <= 0:
        return 1

    qty = int(max_risk_usd / risk_per_contract)
    return max(1, qty)


# ── Daily session state ──────────────────────────────────────────────────────
@dataclass
class SessionState:
    date: date = field(default_factory=date.today)
    trades_taken: int = 0
    daily_start_balance: float = 0.0
    consecutive_losses: int = 0
    daily_pnl: float = 0.0

    def reset_if_new_day(self):
        today = date.today()
        if self.date != today:
            self.date = today
            self.trades_taken = 0
            self.consecutive_losses = 0
            self.daily_pnl = 0.0
            # daily_start_balance is set by executor on first query

    def can_take_trade(self) -> tuple[bool, str]:
        """Returns (allowed, reason_if_not)."""
        self.reset_if_new_day()

        max_trades = int(os.getenv("MAX_TRADES_PER_SESSION", "2"))
        if self.trades_taken >= max_trades:
            return False, f"Max {max_trades} trades/session reached ({self.trades_taken} taken)"

        max_daily_loss_pct = float(os.getenv("MAX_DAILY_LOSS_PCT", "0.03"))
        if self.daily_start_balance > 0:
            daily_loss_pct = -self.daily_pnl / self.daily_start_balance
            if daily_loss_pct >= max_daily_loss_pct:
                return False, f"Daily loss limit hit: {daily_loss_pct:.1%} >= {max_daily_loss_pct:.1%}"

        max_consec = int(os.getenv("MAX_CONSECUTIVE_LOSSES", "3"))
        if self.consecutive_losses >= max_consec:
            return False, f"Consecutive losses limit: {self.consecutive_losses}"

        return True, ""

    def record_trade(self, pnl: float):
        self.trades_taken += 1
        self.daily_pnl += pnl
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0


# Singleton session state (lives in executor process memory)
session = SessionState()
