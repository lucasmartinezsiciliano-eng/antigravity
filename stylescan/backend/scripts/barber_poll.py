"""
Weekly barber trend-question poll over Telegram.

Picks one connected barber (preferring those who haven't been polled
recently), sends a single trend question via the VISAI bot, and logs
the send to `knowledge_base/barber_poll_log.json`.

Replies are NOT captured here — they arrive on the existing Telegram
webhook handled at POST /telegram/webhook in
`app/api/routes/barber_gamification.py`. That endpoint is where reply
ingestion should be wired up in a follow-up.

Run:
    python -m scripts.barber_poll
"""

from __future__ import annotations

import json
import logging
import os
import random
import sqlite3
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import httpx

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).parent.parent
KB_DIR     = ROOT / "knowledge_base"
ENV_PATH   = ROOT / ".env"
DB_PATH    = KB_DIR / "stylescan.db"
LOG_PATH   = KB_DIR / "barber_poll_log.json"

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("barber_poll")

QUESTIONS: list[str] = [
    "¿Qué corte te están pidiendo más esta semana? (responde directamente aquí)",
    "¿Hay algún estilo nuevo que estés viendo mucho en los últimos días?",
    "¿Qué prefieren los clientes jóvenes (<25) esta semana?",
    "¿Skin fade, mid fade o low fade: cuál domina esta semana en tu barbería?",
    "¿Algún corte que ya nadie pida o que esté bajando en popularidad?",
]

# Don't poll the same barber twice within this window
COOLDOWN_DAYS = 14


def _read_dotenv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip().strip('"').strip("'")
    except Exception as e:
        logger.warning("Could not read .env: %s", e)
    return out


def _load_log() -> list[dict]:
    if not LOG_PATH.exists():
        return []
    try:
        data = json.loads(LOG_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_log(entries: list[dict]) -> None:
    try:
        LOG_PATH.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.error("Could not write poll log: %s", e)


def _recently_polled(log: list[dict], cooldown_days: int) -> set[str]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=cooldown_days)
    recent: set[str] = set()
    for entry in log:
        try:
            sent = datetime.fromisoformat(entry.get("sent_at", "").replace("Z", "+00:00"))
        except Exception:
            continue
        if sent >= cutoff:
            bid = entry.get("barber_id")
            if bid:
                recent.add(bid)
    return recent


def _fetch_connected_barbers() -> list[dict]:
    if not DB_PATH.exists():
        logger.warning("Database not found at %s", DB_PATH)
        return []
    try:
        con = sqlite3.connect(str(DB_PATH))
        con.row_factory = sqlite3.Row
        rows = con.execute(
            """
            SELECT
                bta.barber_partner_id    AS barber_id,
                bta.telegram_chat_id     AS chat_id,
                bta.telegram_user_id     AS user_id,
                bta.first_name           AS first_name,
                bp.name                  AS name
            FROM barber_telegram_accounts bta
            JOIN barber_partners bp ON bp.id = bta.barber_partner_id
            WHERE bta.is_connected = 1
              AND bp.is_active = 1
            """
        ).fetchall()
        con.close()
        return [dict(r) for r in rows]
    except sqlite3.Error as e:
        logger.error("DB error: %s", e)
        return []


def _send_telegram(token: str, chat_id: int, text: str) -> bool:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        resp = httpx.post(
            url,
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=15,
        )
        if resp.status_code != 200:
            logger.error("Telegram %d: %s", resp.status_code, resp.text[:200])
            return False
        return True
    except Exception as e:
        logger.error("Telegram send failed: %s", e)
        return False


def main() -> int:
    env = _read_dotenv(ENV_PATH)
    token = (
        env.get("BARBER_TELEGRAM_BOT_TOKEN")
        or os.environ.get("BARBER_TELEGRAM_BOT_TOKEN", "")
    ).strip()
    if not token:
        logger.warning("BARBER_TELEGRAM_BOT_TOKEN not set — exiting")
        return 0

    barbers = _fetch_connected_barbers()
    if not barbers:
        print("No barbers connected")
        return 0

    log = _load_log()
    recent = _recently_polled(log, COOLDOWN_DAYS)
    eligible = [b for b in barbers if b["barber_id"] not in recent]
    if not eligible:
        logger.info("All %d connected barbers polled in the last %d days — picking from full pool",
                    len(barbers), COOLDOWN_DAYS)
        eligible = barbers

    barber = random.choice(eligible)
    question = random.choice(QUESTIONS)
    first_name = (barber.get("first_name") or barber.get("name") or "").split(" ")[0]
    greeting = f"Hola {first_name}, " if first_name else "Hola, "
    text = f"{greeting}{question}"

    ok = _send_telegram(token, int(barber["chat_id"]), text)
    if not ok:
        logger.error("Could not deliver poll to barber %s", barber["barber_id"])
        return 0

    log.append({
        "barber_id":         barber["barber_id"],
        "telegram_chat_id":  barber["chat_id"],
        "question":          question,
        "sent_at":           datetime.now(timezone.utc).isoformat(),
    })
    # Keep only the last 500 entries
    _save_log(log[-500:])

    logger.info("Polled barber %s (chat %s): %s",
                barber["barber_id"], barber["chat_id"], question)
    print(f"Sent question to barber {barber['barber_id']}: {question}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.exception("Unhandled error in barber_poll: %s", e)
        sys.exit(0)
