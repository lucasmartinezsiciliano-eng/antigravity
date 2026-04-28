"""
Daily Bias — TJR Day-34/35/36 + Fede Day-22.
Top-down: Weekly → Daily → 4H → confirmation.
For stocks: adds SPY + Sector ETF layer.
"""

import os
import logging
from datetime import date

log = logging.getLogger(__name__)

# Sector ETF mapping (Fede: 3-layer bias for stocks)
SECTOR_ETFS: dict[str, str] = {
    "AAPL": "XLK", "MSFT": "XLK", "NVDA": "XLK", "META": "XLK",
    "GOOGL": "XLC", "GOOG": "XLC",
    "TSLA": "XLY", "AMZN": "XLY",
    "JPM": "XLF", "BAC": "XLF", "GS": "XLF",
    "XOM": "XLE", "CVX": "XLE",
    "JNJ": "XLV", "PFE": "XLV",
}

# SMT confirmation pairs (Fede Day-26)
SMT_PAIRS: dict[str, str] = {
    "AAPL":   "MSFT",
    "NVDA":   "AMD",
    "META":   "GOOGL",
    "AMZN":   "MSFT",
    "NQ1!":   "ES1!",
    "EURUSD": "GBPUSD",
}


def _get_ibkr_bars(symbol: str, duration: str = "10 D", bar_size: str = "1 day",
                   use_rth: bool = True):
    """Fetch OHLCV bars from IBKR. Returns list of Bar objects."""
    try:
        from ib_insync import IB, Stock, Future, Forex
        ib = IB()
        ib.connect("127.0.0.1", int(os.getenv("IBKR_PORT", 4002)), clientId=99)

        if "NQ" in symbol or "ES" in symbol:
            contract = Future(symbol.replace("1!", ""), exchange="CME")
        elif "USD" in symbol:
            contract = Forex(symbol)
        else:
            contract = Stock(symbol, "SMART", "USD")

        ib.qualifyContracts(contract)
        bars = ib.reqHistoricalData(
            contract,
            endDateTime="",
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow="TRADES",
            useRTH=use_rth,
            formatDate=1,
        )
        ib.disconnect()
        return bars
    except Exception as e:
        log.warning(f"IBKR bars fetch failed for {symbol}: {e}")
        return []


def _detect_bos(bars) -> str:
    """
    Simple BOS detection: if last close > recent swing high → bullish BOS.
    If last close < recent swing low → bearish BOS.
    Returns "BULLISH", "BEARISH", or "NEUTRAL".
    """
    if len(bars) < 5:
        return "NEUTRAL"

    closes = [b.close for b in bars]
    highs  = [b.high  for b in bars]
    lows   = [b.low   for b in bars]

    last_close = closes[-1]
    swing_high = max(highs[-5:-1])
    swing_low  = min(lows[-5:-1])

    if last_close > swing_high:
        return "BULLISH"
    if last_close < swing_low:
        return "BEARISH"
    return "NEUTRAL"


def get_bias(symbol: str) -> str:
    """
    TJR Day-34: Weekly(line chart) → Daily BOS → that IS the daily bias.
    Returns "BULLISH", "BEARISH", or "NEUTRAL".
    """
    # Weekly structure
    weekly_bars = _get_ibkr_bars(symbol, duration="3 M", bar_size="1 week")
    weekly_bias = _detect_bos(weekly_bars)

    # Daily BOS — this IS the daily bias (TJR Day-34)
    daily_bars = _get_ibkr_bars(symbol, duration="20 D", bar_size="1 day")
    daily_bos  = _detect_bos(daily_bars)

    # 4H confirmation
    h4_bars = _get_ibkr_bars(symbol, duration="5 D", bar_size="4 hours")
    h4_bias = _detect_bos(h4_bars)

    log.info(f"[BIAS] {symbol}: weekly={weekly_bias} daily_bos={daily_bos} 4H={h4_bias}")

    # All must agree (or weekly+daily at minimum)
    if daily_bos == weekly_bias and daily_bos != "NEUTRAL":
        return daily_bos     # strong bias
    if daily_bos != "NEUTRAL" and h4_bias == daily_bos:
        return daily_bos     # medium bias
    return "NEUTRAL"


def get_stock_bias(symbol: str) -> str:
    """
    Fede Day-22: 3-layer bias for stocks.
    SPY + Sector ETF + Individual stock — all must agree.
    """
    from filters import is_earnings_week
    if is_earnings_week(symbol):
        return "BLOCKED_EARNINGS"

    spy_bias    = get_bias("SPY")
    sector_etf  = SECTOR_ETFS.get(symbol.upper())
    sector_bias = get_bias(sector_etf) if sector_etf else spy_bias
    stock_bias  = get_bias(symbol)

    log.info(f"[STOCK BIAS] {symbol}: SPY={spy_bias} {sector_etf}={sector_bias} {symbol}={stock_bias}")

    if spy_bias == sector_bias == stock_bias and stock_bias != "NEUTRAL":
        return stock_bias
    if spy_bias == stock_bias and stock_bias != "NEUTRAL":
        return stock_bias    # 2/3 agree
    return "NEUTRAL"


def signal_matches_bias(action: str, symbol: str) -> tuple[bool, str]:
    """
    Returns (True, bias) if signal direction matches daily bias.
    "Fede: no trade against the bias — no concept will save you." (Day-22)
    """
    is_stock = not any(x in symbol.upper() for x in ["NQ", "ES", "MNQ", "MES", "EUR", "GBP"])
    bias = get_stock_bias(symbol) if is_stock else get_bias(symbol)

    if bias == "BLOCKED_EARNINGS":
        return False, "BLOCKED_EARNINGS"

    if bias == "NEUTRAL":
        return False, "NEUTRAL — no clear bias, skip day"

    if (action == "BUY" and bias == "BULLISH") or (action == "SELL" and bias == "BEARISH"):
        return True, bias

    return False, f"Signal {action} against daily bias {bias}"
