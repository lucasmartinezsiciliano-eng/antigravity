"""
news_calendar.py — Economic Calendar (ForexFactory)
====================================================
Descarga el calendario de noticias de alto impacto de ForexFactory.
Usado por el bot para:
  1. Blackout automatico: no operar 15 min antes/despues de HIGH impact
  2. Mostrar eventos del dia en el dashboard
  3. Alertas de sesion pre-market (que noticias hay hoy)

Fuente: https://nfs.faireconomy.media/ff_calendar_thisweek.json
  - Gratis, sin API key, actualizado cada hora
  - Cubre la semana actual (lunes a viernes)
  - Campos: title, country, date, time, impact, forecast, previous

Uso standalone:
    python news_calendar.py              # eventos de hoy (USD, HIGH)
    python news_calendar.py --all        # todos los impactos
    python news_calendar.py --week       # semana completa
    python news_calendar.py --json       # output JSON
"""

import io
import sys
import json
import pytz
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

NY = pytz.timezone("America/New_York")
CACHE_FILE = Path("news_cache.json")
CACHE_TTL  = 3600  # 1 hour

# URL de ForexFactory (usada por miles de herramientas de trading, es publica)
FF_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

# Eventos de alto impacto en USD que afectan directamente a NQ/ES
HIGH_IMPACT_EVENTS = {
    "Non-Farm Employment Change": "NFP",
    "FOMC Statement":             "FOMC",
    "Federal Funds Rate":         "FOMC",
    "CPI m/m":                    "CPI",
    "Core CPI m/m":               "CPI",
    "PPI m/m":                    "PPI",
    "GDP q/q":                    "GDP",
    "Unemployment Claims":        "CLAIMS",
    "ISM Manufacturing PMI":      "ISM-MFG",
    "ISM Services PMI":           "ISM-SVC",
    "Retail Sales m/m":           "RETAIL",
    "ADP Non-Farm Employment":    "ADP",
    "Fed Chair Powell Speaks":    "POWELL",
    "JOLTS Job Openings":         "JOLTS",
    "PCE Price Index m/m":        "PCE",
}

BLACKOUT_MINUTES = 15  # minutos de blackout antes y despues del evento


def fetch_calendar(force: bool = False) -> list:
    """Descarga o devuelve cached el calendario de esta semana."""
    import time as _time

    # Check cache
    if not force and CACHE_FILE.exists():
        try:
            cached = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            if _time.time() - cached.get("ts", 0) < CACHE_TTL:
                return cached["events"]
        except Exception:
            pass

    import urllib.request
    try:
        req = urllib.request.Request(FF_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = json.loads(r.read())
    except Exception as e:
        print(f"[CALENDAR] Error descargando: {e}")
        # Return cached if available even if expired
        if CACHE_FILE.exists():
            try:
                return json.loads(CACHE_FILE.read_text())["events"]
            except Exception:
                pass
        return []

    events = []
    for ev in raw:
        if ev.get("country") != "USD":
            continue

        title  = ev.get("title", "")
        impact = ev.get("impact", "").upper()
        date_s = ev.get("date", "")   # "2026-04-30T00:00:00-04:00"
        time_s = ev.get("time", "")   # "8:30am" or "All Day" or "Tentative"

        if not date_s:
            continue

        # Parse datetime
        try:
            # date is ISO with timezone offset
            dt_utc = datetime.fromisoformat(date_s.replace("Z", "+00:00"))
        except Exception:
            continue

        # Combine with time if available
        ev_dt = None
        if time_s and time_s not in ("All Day", "Tentative", ""):
            try:
                # time_s like "8:30am" or "2:00pm"
                t = datetime.strptime(time_s.strip(), "%I:%M%p")
                ev_dt = dt_utc.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
                # Convert to NY
                ev_dt_ny = ev_dt.astimezone(NY)
            except Exception:
                ev_dt_ny = dt_utc.astimezone(NY)
        else:
            ev_dt_ny = dt_utc.astimezone(NY)

        # Short name for well-known events
        short = HIGH_IMPACT_EVENTS.get(title, title[:20])

        # Mark truly all-day only when time is midnight (no specific time)
        is_all_day = (time_s in ("All Day", "Tentative")) or \
                     (time_s == "" and ev_dt_ny.hour == 0 and ev_dt_ny.minute == 0)

        events.append({
            "title":    title,
            "short":    short,
            "impact":   impact,
            "date":     ev_dt_ny.strftime("%Y-%m-%d"),
            "time_et":  ev_dt_ny.strftime("%H:%M"),
            "ts_unix":  int(ev_dt_ny.timestamp()),
            "forecast": ev.get("forecast", ""),
            "previous": ev.get("previous", ""),
            "all_day":  is_all_day,
        })

    # Cache to disk
    import time as _time
    CACHE_FILE.write_text(json.dumps({"ts": _time.time(), "events": events}), encoding="utf-8")
    return events


def get_today_events(impact_filter: str = "HIGH") -> list:
    """Devuelve eventos de hoy, filtrados por impacto."""
    now_ny = datetime.now(NY)
    today  = now_ny.strftime("%Y-%m-%d")
    events = fetch_calendar()
    result = [
        e for e in events
        if e["date"] == today
        and (impact_filter == "ALL" or e["impact"] == impact_filter)
        and not e["all_day"]
    ]
    return sorted(result, key=lambda e: e["ts_unix"])


def get_week_events(impact_filter: str = "HIGH") -> list:
    """Devuelve eventos de la semana."""
    events = fetch_calendar()
    result = [
        e for e in events
        if (impact_filter == "ALL" or e["impact"] == impact_filter)
        and not e["all_day"]
    ]
    return sorted(result, key=lambda e: e["ts_unix"])


def next_event_status(events: list = None) -> dict | None:
    """
    Devuelve el proximo evento relevante y si estamos en blackout.
    Usado por el bot para bloquear senales cerca de noticias.
    """
    if events is None:
        events = get_today_events("HIGH")

    now_unix = datetime.now(NY).timestamp()
    for ev in sorted(events, key=lambda e: e["ts_unix"]):
        delta_min = (ev["ts_unix"] - now_unix) / 60
        in_blackout = abs(delta_min) <= BLACKOUT_MINUTES

        if delta_min > -BLACKOUT_MINUTES:  # not yet past blackout window
            return {
                "name":       ev["short"],
                "time_et":    ev["time_et"],
                "delta_min":  round(delta_min, 1),
                "blackout":   in_blackout,
                "impact":     ev["impact"],
                "forecast":   ev["forecast"],
                "previous":   ev["previous"],
            }
    return None


def is_blackout_now(events: list = None) -> tuple[bool, str]:
    """Returns (is_blackout, reason_string)."""
    status = next_event_status(events)
    if status and status["blackout"]:
        delta = status["delta_min"]
        if delta > 0:
            reason = f"Blackout pre-{status['name']} en {delta:.0f}m ({status['time_et']} ET)"
        else:
            reason = f"Blackout post-{status['name']} hace {abs(delta):.0f}m"
        return True, reason
    return False, ""


# ── Standalone output ─────────────────────────────────────────────────────────
def print_events(events: list, label: str = "Eventos"):
    if not events:
        print(f"  {label}: sin eventos HIGH impact USD")
        return
    print(f"\n  {label} (USD, HIGH impact):")
    print("  " + "-"*55)
    for ev in events:
        now_unix = datetime.now(NY).timestamp()
        delta    = (ev["ts_unix"] - now_unix) / 60
        flag     = " <-- BLACKOUT" if abs(delta) <= BLACKOUT_MINUTES else (
                   f"  (en {delta:.0f}m)" if 0 < delta < 120 else "")
        print(f"  {ev['time_et']} ET  {ev['short']:<20}  prev={ev['previous']:>8}  fcst={ev['forecast']:>8}{flag}")
    print()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--week",   action="store_true", help="Semana completa")
    parser.add_argument("--all",    action="store_true", help="Todos los impactos")
    parser.add_argument("--json",   action="store_true")
    parser.add_argument("--force",  action="store_true", help="Forzar descarga (ignorar cache)")
    args = parser.parse_args()

    impact = "ALL" if args.all else "HIGH"

    if args.week:
        events = get_week_events(impact)
        label  = f"Semana (USD {impact})"
    else:
        events = get_today_events(impact)
        label  = f"Hoy {datetime.now(NY).strftime('%Y-%m-%d')} (USD {impact})"

    if args.json:
        status = next_event_status(events)
        print(json.dumps({"events": events, "next": status}, indent=2, ensure_ascii=False))
    else:
        now_ny = datetime.now(NY)
        print(f"\n  Hora ET: {now_ny.strftime('%H:%M:%S')} | Blackout: +-{BLACKOUT_MINUTES}min")
        print_events(events, label)

        status = next_event_status(events)
        if status:
            bk = "[BLACKOUT ACTIVO]" if status["blackout"] else ""
            print(f"  Proximo: {status['name']} a {status['time_et']} ET "
                  f"({status['delta_min']:+.0f}m) {bk}")
        else:
            print("  Sin eventos proximos hoy.")


if __name__ == "__main__":
    main()
