"""
Telegram Service

Handles:
1. Webhook message parsing and routing
2. Sending notifications to barbers (commission alerts, ranking updates)
3. Handling /start, /help, /status commands

- send_notification(telegram_chat_id, message_type, data)
  → Sends formatted message via Telegram Bot API

- parse_webhook(body)
  → Parses Telegram webhook and routes to appropriate handler
"""

import logging
import httpx
import json
from typing import Optional, Dict, Any
from enum import Enum

from app.core.config import settings

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org"


class NotificationType(str, Enum):
    """Types of notifications barbers can receive."""
    NEW_ANALYSIS = "new_analysis"
    RANKING_UP = "ranking_up"
    RANKING_DOWN = "ranking_down"
    WEEKLY_SUMMARY = "weekly_summary"
    COMMISSION_MILESTONE = "commission_milestone"


async def send_notification(
    telegram_chat_id: int,
    notification_type: NotificationType,
    data: Dict[str, Any],
    language_code: str = "es",
) -> bool:
    """
    Send a notification to barber via Telegram.

    notification_type: NEW_ANALYSIS, RANKING_UP, RANKING_DOWN, WEEKLY_SUMMARY, COMMISSION_MILESTONE
    data: context-specific data (analysis count, ranking position, revenue, etc.)
    language_code: "es", "en", "fr", etc.

    Returns: True if sent successfully, False otherwise.
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not configured")
        return False

    # Build message
    message = _build_notification_message(
        notification_type=notification_type,
        data=data,
        language_code=language_code,
    )

    if not message:
        logger.warning("Could not build notification message for type %s", notification_type)
        return False

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{TELEGRAM_API_BASE}/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": telegram_chat_id,
                    "text": message,
                    "parse_mode": "HTML",
                },
            )

        if resp.status_code == 200:
            logger.info("Telegram notification sent: chat_id=%d type=%s", telegram_chat_id, notification_type)
            return True
        else:
            logger.error(
                "Telegram send failed: %d %s",
                resp.status_code,
                resp.text[:200],
            )
            return False

    except Exception as e:
        logger.error("Telegram send error: %s", e)
        return False


async def parse_webhook(body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse Telegram webhook and route to appropriate handler.

    Returns: response dict or None if webhook couldn't be processed.
    """
    try:
        # Extract message or callback query
        if "message" in body:
            message = body["message"]
            from_user = message.get("from", {})
            text = message.get("text", "")

            logger.info(
                "Telegram message from user %d: %s",
                from_user.get("id"),
                text[:50],
            )

            # Route based on command
            if text.startswith("/start"):
                return await _handle_start_command(message, from_user)
            elif text.startswith("/help"):
                return await _handle_help_command(message, from_user)
            elif text.startswith("/status"):
                return await _handle_status_command(message, from_user)
            else:
                return {"ok": True}  # Ignore non-command messages

        elif "callback_query" in body:
            callback_query = body["callback_query"]
            logger.info(
                "Telegram callback from user %d: %s",
                callback_query.get("from", {}).get("id"),
                callback_query.get("data"),
            )
            return {"ok": True}

        else:
            logger.debug("Unhandled Telegram webhook: %s", list(body.keys()))
            return {"ok": True}

    except Exception as e:
        logger.error("Webhook parse error: %s", e)
        return None


async def _handle_start_command(message: Dict, from_user: Dict) -> Dict:
    """Handle /start command."""
    user_id = from_user.get("id")
    first_name = from_user.get("first_name", "Barbero")

    # TODO: Link Telegram account to barber in database
    # For now, just acknowledge

    logger.info("Telegram /start from user %d", user_id)
    return {"ok": True}


async def _handle_help_command(message: Dict, from_user: Dict) -> Dict:
    """Handle /help command."""
    user_id = from_user.get("id")

    logger.info("Telegram /help from user %d", user_id)
    return {"ok": True}


async def _handle_status_command(message: Dict, from_user: Dict) -> Dict:
    """Handle /status command — show barber stats."""
    user_id = from_user.get("id")

    logger.info("Telegram /status from user %d", user_id)
    return {"ok": True}


def _build_notification_message(
    notification_type: NotificationType,
    data: Dict[str, Any],
    language_code: str = "es",
) -> Optional[str]:
    """Build formatted message text for notification."""
    if language_code != "es":
        language_code = "es"  # For now, only Spanish

    if notification_type == NotificationType.NEW_ANALYSIS:
        client_count = data.get("client_count", 1)
        total_clients = data.get("total_clients", 0)
        earned_euros = data.get("earned_euros", 1.50)
        return (
            f"🎯 <b>Nuevo análisis completado</b>\n\n"
            f"Un cliente ha usado tu código VISAI.\n"
            f"Has ganado <b>€{earned_euros:.2f}</b>\n\n"
            f"Total hoy: <b>{client_count}</b> análisis\n"
            f"Total (all-time): <b>{total_clients}</b> análisis"
        )

    elif notification_type == NotificationType.RANKING_UP:
        new_position = data.get("new_position", 1)
        old_position = data.get("old_position", 2)
        tier = data.get("tier", "BRONZE")
        return (
            f"📈 <b>¡Subiste en el ranking!</b>\n\n"
            f"Posición anterior: #{old_position}\n"
            f"Posición nueva: #{new_position}\n"
            f"Tier: <b>{tier}</b> 🏆"
        )

    elif notification_type == NotificationType.RANKING_DOWN:
        new_position = data.get("new_position", 50)
        old_position = data.get("old_position", 40)
        return (
            f"📉 Bajaste en el ranking.\n\n"
            f"Posición anterior: #{old_position}\n"
            f"Posición nueva: #{new_position}\n\n"
            f"¡Necesitas más clientes para subir!"
        )

    elif notification_type == NotificationType.WEEKLY_SUMMARY:
        week_clients = data.get("week_clients", 0)
        week_revenue = data.get("week_revenue_euros", 0)
        position = data.get("position", 50)
        total_clients = data.get("total_clients", 0)
        return (
            f"📊 <b>Resumen Semanal</b>\n\n"
            f"Análisis esta semana: <b>{week_clients}</b>\n"
            f"Ingresos: <b>€{week_revenue:.2f}</b>\n"
            f"Ranking: <b>#{position}</b> de {total_clients}\n\n"
            f"¡Sigue adelante! 💪"
        )

    elif notification_type == NotificationType.COMMISSION_MILESTONE:
        total_earned = data.get("total_earned_euros", 0)
        milestone = data.get("milestone_euros", 10)
        return (
            f"🎉 <b>¡Hito alcanzado!</b>\n\n"
            f"Has ganado <b>€{total_earned:.2f}</b> en total con VISAI.\n"
            f"¡{milestone}€ ya en tu bolsillo! 💰"
        )

    return None
