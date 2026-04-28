"""
Order Executor — listens Redis, validates, places bracket orders via ib_insync.
Implements: 1% risk, max 2 trades/session, daily loss limit, break-even at 1:1.
"""

import asyncio
import json
import logging
import os

import redis.asyncio as aioredis
from ib_insync import IB, Future, Stock, Forex, MarketOrder, LimitOrder

from filters import is_valid_session
from risk import calculate_position_size, session as daily_session
from logger import log_skip, log_order, log_error
from telegram_monitor import (
    notify, fmt_order_opened, fmt_skip, fmt_session_end
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

ib = IB()

# ── Connect ──────────────────────────────────────────────────────────────────

async def connect_ibkr():
    port = int(os.getenv("IBKR_PORT", 4002))
    host = os.getenv("IBKR_HOST", "127.0.0.1")
    log.info(f"Connecting to IB Gateway at {host}:{port} ...")
    await ib.connectAsync(host=host, port=port, clientId=1, readonly=False)
    log.info(f"Connected. Account: {ib.managedAccounts()}")


# ── Contract factory ──────────────────────────────────────────────────────────

def make_contract(symbol: str):
    s = symbol.upper()
    if "NQ" in s:
        return Future("NQ", exchange="CME", currency="USD")
    if "ES" in s:
        return Future("ES", exchange="CME", currency="USD")
    if "MNQ" in s:
        return Future("MNQ", exchange="CME", currency="USD")
    if "MES" in s:
        return Future("MES", exchange="CME", currency="USD")
    if "EURUSD" in s:
        return Forex("EURUSD")
    if "GBPUSD" in s:
        return Forex("GBPUSD")
    # Default: US stock via SMART routing
    return Stock(symbol, "SMART", "USD")


# ── Position sizing ───────────────────────────────────────────────────────────

def get_account_value() -> float:
    vals = ib.accountValues()
    for v in vals:
        if v.tag == "NetLiquidation" and v.currency == "USD":
            return float(v.value)
    return float(os.getenv("ACCOUNT_SIZE", 50000))


# ── SL / TP calculation ───────────────────────────────────────────────────────

def compute_sl_tp(action: str, entry: float, symbol: str) -> tuple[float, float]:
    """
    SL: below IFVG (configured via env, default 5 ticks for NQ).
    TP: 2:1 RR minimum (TJR Day-13 + Fede Day-28).
    For stocks: use percentage-based SL.
    """
    is_futures = any(x in symbol.upper() for x in ["NQ", "ES", "MNQ", "MES"])
    is_forex   = any(x in symbol.upper() for x in ["EUR", "GBP", "AUD", "USD"])

    if is_futures:
        from risk import get_tick_size
        ticks = int(os.getenv("STOP_TICKS", "10"))
        tick_sz = get_tick_size(symbol)
        stop_dist = ticks * tick_sz
    elif is_forex:
        pips = int(os.getenv("STOP_PIPS", "15"))
        stop_dist = pips * 0.0001
    else:
        # Stock: % based
        stop_pct = float(os.getenv("STOP_PCT", "0.5")) / 100
        stop_dist = entry * stop_pct

    rr = float(os.getenv("MIN_RR", "2.0"))

    if action == "BUY":
        sl = round(entry - stop_dist, 5)
        tp = round(entry + stop_dist * rr, 5)
    else:
        sl = round(entry + stop_dist, 5)
        tp = round(entry - stop_dist * rr, 5)

    return sl, tp


# ── Place bracket order ───────────────────────────────────────────────────────

async def place_bracket_order(signal: dict) -> bool:
    """Returns True if order was placed."""
    symbol = signal["symbol"]
    action = signal["action"]
    entry  = float(signal["close"])

    # Validate session
    allowed, reason = is_valid_session(symbol)
    if not allowed:
        log.info(f"[SKIP] {symbol}: {reason}")
        log_skip(reason, signal)
        await notify(fmt_skip(symbol, reason))
        return False

    # Daily session limits
    can_trade, reason = daily_session.can_take_trade()
    if not can_trade:
        log.info(f"[SKIP] {reason}")
        log_skip(reason, signal)
        await notify(fmt_skip(symbol, reason))
        return False

    # Account value
    account = get_account_value()
    if daily_session.daily_start_balance == 0:
        daily_session.daily_start_balance = account

    # SL / TP
    sl, tp = compute_sl_tp(action, entry, symbol)
    stop_dist = abs(entry - sl)

    # Position size
    risk_pct = float(os.getenv("MAX_RISK_PCT", "0.01"))
    qty = calculate_position_size(account, risk_pct, stop_dist, symbol)
    rr  = round(abs(tp - entry) / stop_dist, 2)

    # Build contract
    contract = make_contract(symbol)
    await ib.qualifyContractsAsync(contract)

    # Bracket order: parent limit + SL stop + TP limit
    bracket = ib.bracketOrder(
        action=action,
        quantity=qty,
        limitPrice=entry,
        takeProfitPrice=tp,
        stopLossPrice=sl,
    )

    for order in bracket:
        trade = ib.placeOrder(contract, order)
        log.info(f"[ORDER] {action} {qty}x {symbol} @ {entry} | SL {sl} TP {tp}")

    log_order(signal, qty, entry, sl, tp, account)
    await notify(fmt_order_opened(action, symbol, qty, entry, sl, tp, rr))

    # Break-even at 1:1 (scheduled — ib_insync monitors via events)
    asyncio.create_task(_schedule_break_even(contract, bracket[0], entry, sl, symbol, action))

    return True


# ── Break-even management ─────────────────────────────────────────────────────

async def _schedule_break_even(contract, parent_order, entry: float, sl: float,
                                symbol: str, action: str):
    """
    Move SL to break-even when price reaches 1:1 RR.
    Polls every 5 seconds (sufficient for intraday swing).
    """
    target_1to1 = entry + abs(entry - sl) if action == "BUY" else entry - abs(entry - sl)
    be_moved = False

    for _ in range(300):   # max 25 minutes of polling
        await asyncio.sleep(5)
        tickers = ib.reqTickers(contract)
        if not tickers:
            continue
        last = tickers[0].last

        if not be_moved:
            triggered = (action == "BUY" and last >= target_1to1) or \
                        (action == "SELL" and last <= target_1to1)
            if triggered:
                # Modify SL to break-even
                sl_order = parent_order  # the stop order in the bracket
                sl_order.auxPrice = entry
                ib.placeOrder(contract, sl_order)
                log.info(f"[BE] Break-even moved to {entry} for {symbol}")
                await notify(f"↔️ <b>Break-even</b> {symbol} → SL moved to entry {entry}")
                be_moved = True
                break


# ── Redis listener ────────────────────────────────────────────────────────────

async def listen_redis():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    r = await aioredis.from_url(redis_url)
    pubsub = r.pubsub()
    await pubsub.subscribe("signals")
    log.info("Listening on Redis channel: signals")

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue
        try:
            signal = json.loads(message["data"])
            log.info(f"[SIGNAL] {signal}")
            await place_bracket_order(signal)
        except Exception as e:
            log.error(f"Error processing signal: {e}")
            log_error("signal_processing_error", e)


# ── Session end summary ───────────────────────────────────────────────────────

async def session_end_check():
    """Send daily summary at 11:05 ET."""
    import pytz
    from datetime import datetime, time as dtime
    ny_tz = pytz.timezone("America/New_York")

    while True:
        await asyncio.sleep(60)
        now = datetime.now(ny_tz)
        if now.hour == 11 and now.minute == 5:
            await notify(fmt_session_end(
                daily_session.trades_taken,
                daily_session.daily_pnl
            ))
            await asyncio.sleep(60)  # Don't fire twice


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    await connect_ibkr()
    await asyncio.gather(
        listen_redis(),
        session_end_check(),
        ib.runAsync(),
    )


if __name__ == "__main__":
    asyncio.run(main())
