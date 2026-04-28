"""
Telegram notifications — freqtrade-style alerts for every trade event.
Uses python-telegram-bot v20+ (async).
"""

import os
import asyncio
import logging
from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

_bot: Bot | None = None


def _get_bot() -> Bot | None:
    global _bot
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return None
    if _bot is None:
        _bot = Bot(token=token)
    return _bot


async def notify(message: str):
    """Send message to configured chat. Fails silently if not configured."""
    bot = _get_bot()
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not bot or not chat_id:
        return
    try:
        await bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
    except TelegramError as e:
        logger.warning(f"Telegram send failed: {e}")


def notify_sync(message: str):
    """Sync wrapper for use outside async context."""
    try:
        asyncio.get_event_loop().run_until_complete(notify(message))
    except RuntimeError:
        asyncio.run(notify(message))


# ── Pre-formatted alert builders ─────────────────────────────────────────────

def fmt_order_opened(action: str, symbol: str, qty: int,
                     entry: float, sl: float, tp: float, rr: float) -> str:
    icon = "🟢" if action == "BUY" else "🔴"
    direction = "LONG" if action == "BUY" else "SHORT"
    return (
        f"{icon} <b>{direction} {symbol}</b>\n"
        f"Entry: <code>{entry}</code> | Qty: {qty}\n"
        f"SL: <code>{sl}</code>  TP: <code>{tp}</code>  RR: {rr:.1f}:1"
    )


def fmt_trade_closed(symbol: str, pnl: float, rr_achieved: float) -> str:
    icon = "✅" if pnl >= 0 else "❌"
    return (
        f"{icon} <b>CLOSED {symbol}</b>\n"
        f"PnL: <code>{'+'if pnl>=0 else ''}{pnl:.2f}</code>  "
        f"RR achieved: {rr_achieved:.1f}"
    )


def fmt_skip(symbol: str, reason: str) -> str:
    return f"⏭ <b>SKIP {symbol}</b>\n{reason}"


def fmt_daily_summary(trades: int, wins: int, losses: int,
                       daily_pnl: float, dd_pct: float) -> str:
    wr = (wins / trades * 100) if trades > 0 else 0
    return (
        f"📊 <b>Daily Summary</b>\n"
        f"Trades: {trades}  W/L: {wins}/{losses}  WR: {wr:.0f}%\n"
        f"PnL: <code>{'+'if daily_pnl>=0 else ''}{daily_pnl:.2f}</code>  "
        f"DD: {dd_pct:.1f}%"
    )


def fmt_news_blackout(event_name: str, minutes: int) -> str:
    return f"⚠️ <b>News blackout</b>: {event_name} in ~{minutes} min — bot paused"


def fmt_session_start() -> str:
    return "🔔 <b>NY AM session started</b> — bot active (8:30-11:00 ET)"


def fmt_session_end(trades: int, pnl: float) -> str:
    return (
        f"🔕 <b>NY AM session ended</b>\n"
        f"Trades: {trades}  PnL: {pnl:+.2f}"
    )
