"""
Sends a weekly earnings summary to each connected VISAI barber via Telegram.

For each active barber whose Telegram account is connected:
  - Week earnings = sum(commissions.amount_cents) in the last 7 days
  - Pending payout = total_earned_cents - total_paid_out_cents
  - Ranking      = position by total_earned_cents (1 = top earner)

Run:
    python -m scripts.weekly_report
"""

from __future__ import annotations

import json
import logging
import os
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
LOG_PATH   = KB_DIR / "weekly_report_log.json"

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("weekly_report")


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


def _fmt_euros(cents: int) -> str:
    cents = max(0, int(cents or 0))
    return f"{cents // 100},{cents % 100:02d}"


def _send_telegram(token: str, chat_id: int, text: str) -> tuple[bool, Optional[str]]:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        resp = httpx.post(
            url,
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=15,
        )
        if resp.status_code != 200:
            return False, f"{resp.status_code}: {resp.text[:200]}"
        return True, None
    except Exception as e:
        return False, str(e)


def _connect_db() -> Optional[sqlite3.Connection]:
    if not DB_PATH.exists():
        logger.warning("Database not found at %s", DB_PATH)
        return None
    try:
        con = sqlite3.connect(str(DB_PATH))
        con.row_factory = sqlite3.Row
        return con
    except sqlite3.Error as e:
        logger.error("DB connect failed: %s", e)
        return None


def _append_log(entries: list[dict]) -> None:
    existing: list[dict] = []
    if LOG_PATH.exists():
        try:
            existing = json.loads(LOG_PATH.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = []
        except Exception:
            existing = []
    existing.extend(entries)
    try:
        LOG_PATH.write_text(json.dumps(existing[-2000:], ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.error("Could not write report log: %s", e)


def main() -> int:
    env = _read_dotenv(ENV_PATH)
    token = (
        env.get("BARBER_TELEGRAM_BOT_TOKEN")
        or os.environ.get("BARBER_TELEGRAM_BOT_TOKEN", "")
    ).strip()
    if not token:
        logger.warning("BARBER_TELEGRAM_BOT_TOKEN not set — exiting")
        return 0

    con = _connect_db()
    if con is None:
        return 0

    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    try:
        barbers = con.execute(
            """
            SELECT id, name, total_earned_cents, total_paid_out_cents
            FROM barber_partners
            WHERE is_active = 1
            ORDER BY total_earned_cents DESC
            """
        ).fetchall()
    except sqlite3.Error as e:
        logger.error("Could not query barber_partners: %s", e)
        con.close()
        return 0

    if not barbers:
        logger.info("No active barbers")
        con.close()
        return 0

    # Ranking: position by total_earned_cents (1 = top)
    ranking: dict[str, int] = {}
    total_active = len(barbers)
    for idx, row in enumerate(barbers, start=1):
        ranking[row["id"]] = idx

    sends: list[dict] = []
    sent_ok = 0
    sent_fail = 0
    skipped = 0
    now_iso = datetime.now(timezone.utc).isoformat()

    for row in barbers:
        barber_id = row["id"]
        # Telegram account
        try:
            tg = con.execute(
                """
                SELECT telegram_chat_id, is_connected, notify_on_weekly_summary, notifications_enabled
                FROM barber_telegram_accounts
                WHERE barber_partner_id = ?
                """,
                (barber_id,),
            ).fetchone()
        except sqlite3.Error as e:
            logger.warning("Telegram lookup failed for %s: %s", barber_id, e)
            tg = None

        if not tg or not tg["is_connected"] or not tg["telegram_chat_id"]:
            skipped += 1
            continue
        if not tg["notifications_enabled"] or not tg["notify_on_weekly_summary"]:
            skipped += 1
            continue

        # Week earnings
        try:
            week_row = con.execute(
                """
                SELECT COALESCE(SUM(amount_cents), 0) AS week_cents
                FROM commissions
                WHERE barber_partner_id = ?
                  AND created_at >= ?
                """,
                (barber_id, week_ago),
            ).fetchone()
            week_cents = int(week_row["week_cents"] or 0)
        except sqlite3.Error as e:
            logger.warning("Week earnings query failed for %s: %s", barber_id, e)
            week_cents = 0

        total_earned = int(row["total_earned_cents"] or 0)
        total_paid   = int(row["total_paid_out_cents"] or 0)
        pending      = max(0, total_earned - total_paid)
        rank         = ranking.get(barber_id, total_active)

        text = (
            "📊 *Tu resumen semanal VISAI*\n"
            "\n"
            f"💰 Esta semana: €{_fmt_euros(week_cents)}\n"
            f"📈 Acumulado pendiente de cobro: €{_fmt_euros(pending)}\n"
            f"🏆 Tu posición: #{rank} entre los barberos activos\n"
            "\n"
            "_El pago mensual se realiza el día 5 del mes siguiente._\n"
            "\n"
            "¿Alguna duda? Contacta con nosotros."
        )

        ok, err = _send_telegram(token, int(tg["telegram_chat_id"]), text)
        if ok:
            sent_ok += 1
        else:
            sent_fail += 1
            logger.warning("Send failed for %s: %s", barber_id, err)

        sends.append({
            "barber_id":   barber_id,
            "chat_id":     tg["telegram_chat_id"],
            "week_cents":  week_cents,
            "pending_cents": pending,
            "rank":        rank,
            "ok":          ok,
            "error":       err,
            "sent_at":     now_iso,
        })

    con.close()
    _append_log(sends)
    logger.info("Weekly report: %d sent, %d failed, %d skipped (of %d active)",
                sent_ok, sent_fail, skipped, total_active)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.exception("Unhandled error in weekly_report: %s", e)
        sys.exit(0)
