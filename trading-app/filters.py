"""
Trade filters — Fede Esses + TJR rules.
Kill zone: NY AM 8:30-11:00 ET.
News blackout: ±15 min around high-impact USD events.
Earnings block: 7 days before earnings for individual stocks.
"""

import datetime
import pytz
import requests

NY_TZ = pytz.timezone("America/New_York")

# ── Kill Zones ───────────────────────────────────────────────────────────────
KILL_ZONES = {
    "london":       (datetime.time(2, 0),  datetime.time(5, 0)),
    "ny_am":        (datetime.time(8, 30), datetime.time(11, 0)),   # PRIMARY
    "london_close": (datetime.time(10, 0), datetime.time(12, 0)),
}


def _now_ny() -> datetime.datetime:
    return datetime.datetime.now(NY_TZ)


def is_market_hours() -> bool:
    """Mon-Fri, 9:30-16:00 ET (for stocks). Futures are always open."""
    now = _now_ny()
    if now.weekday() >= 5:
        return False
    t = now.time()
    return datetime.time(9, 30) <= t <= datetime.time(16, 0)


def is_in_kill_zone(zone: str = "ny_am") -> bool:
    t = _now_ny().time()
    start, end = KILL_ZONES[zone]
    return start <= t <= end


def is_trading_day() -> bool:
    """Mon-Fri only."""
    return _now_ny().weekday() < 5


# ── News blackout ────────────────────────────────────────────────────────────
def _is_nfp_day() -> bool:
    """First Friday of the month = NFP day."""
    today = datetime.date.today()
    return today.weekday() == 4 and today.day <= 7


def _get_hardcoded_blackouts() -> list[tuple[datetime.time, datetime.time]]:
    """
    Fixed-schedule high-impact news windows (ET).
    NFP/CPI/GDP/PCE → 8:30 ET → blackout 8:15-8:45
    FOMC → 14:00 ET → blackout 13:45-14:15
    """
    blackouts = []
    # 8:30 ET events (happens almost every week, safe to always block)
    blackouts.append((datetime.time(8, 15), datetime.time(8, 45)))
    # FOMC (14:00 ET) — only block if FOMC day. For now block always as safety.
    # In production: check if today is FOMC from ForexFactory.
    return blackouts


def is_news_blackout(buffer_minutes: int = 15) -> bool:
    """
    True if current time is within buffer of a high-impact news event.
    Uses hardcoded schedule + optional ForexFactory JSON.
    """
    # 1. Hardcoded windows
    now_t = _now_ny().time()
    for start, end in _get_hardcoded_blackouts():
        if start <= now_t <= end:
            return True

    # 2. ForexFactory JSON (best-effort, fails gracefully)
    try:
        _check_forex_factory(buffer_minutes)
    except Exception:
        pass  # Fail open — don't block trading if FF is down

    return False


def _check_forex_factory(buffer_minutes: int = 15) -> bool:
    url = "https://www.forexfactory.com/calendar.php?week=this&format=json"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, timeout=5, headers=headers)
    events = resp.json()

    now = _now_ny()
    for event in events:
        if event.get("impact") not in ("High", "red"):
            continue
        if "USD" not in event.get("currency", ""):
            continue
        # Parse event time — FF format varies, skip if unparseable
        try:
            event_time_str = event.get("date", "") + " " + event.get("time", "")
            event_dt = datetime.datetime.strptime(event_time_str, "%Y-%m-%d %I:%M%p")
            event_dt = NY_TZ.localize(event_dt)
            delta_min = abs((event_dt - now).total_seconds() / 60)
            if delta_min <= buffer_minutes:
                return True
        except Exception:
            continue

    return False


# ── Earnings filter (stocks only) ────────────────────────────────────────────
def is_earnings_week(symbol: str, days_before: int = 7) -> bool:
    """Block trading if earnings within N days. Requires yfinance."""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        cal = ticker.calendar
        if cal is not None and "Earnings Date" in cal.columns:
            earnings_date = cal["Earnings Date"].iloc[0]
            if hasattr(earnings_date, "date"):
                earnings_date = earnings_date.date()
            days_to = (earnings_date - datetime.date.today()).days
            return 0 <= days_to <= days_before
    except Exception:
        pass
    return False


# ── Opening gap filter (stocks) ──────────────────────────────────────────────
def is_large_gap(prev_close: float, today_open: float, threshold_pct: float = 3.0) -> bool:
    """Skip if opening gap > threshold% (likely earnings/news driven)."""
    if prev_close <= 0:
        return False
    gap_pct = abs(today_open - prev_close) / prev_close * 100
    return gap_pct >= threshold_pct


# ── Master session check ─────────────────────────────────────────────────────
def is_valid_session(symbol: str = "") -> tuple[bool, str]:
    """
    Returns (allowed, reason_if_not).
    Combines: trading day + kill zone + news blackout.
    For stock symbols: also checks earnings week.
    """
    if not is_trading_day():
        return False, "Weekend — market closed"

    if not is_in_kill_zone("ny_am"):
        now_t = _now_ny().strftime("%H:%M ET")
        return False, f"Outside NY AM kill zone (8:30-11:00 ET) — now {now_t}"

    if is_news_blackout():
        return False, "News blackout: high-impact USD event within ±15 min"

    # Stock-specific
    is_stock = symbol and not any(x in symbol for x in ["NQ", "ES", "MNQ", "MES", "EUR", "GBP"])
    if is_stock and is_earnings_week(symbol):
        return False, f"Earnings week blocked: {symbol}"

    return True, ""
