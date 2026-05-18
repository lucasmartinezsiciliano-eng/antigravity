"""
Background Jobs for VISAI MVP
- Daily leaderboard recalculation (03:00 UTC)
- Weekly Telegram summary (Sunday 08:00 UTC)
- Daily auto-approval of high-quality photos
"""

import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.models.barber import BarberPartner
from app.models.barber_leaderboard_stats import (
    BarberLeaderboardStats,
    RankingTier,
)
from app.models.barber_reference_photos import BarberReferencePhoto, PhotoValidationStatus
from app.models.barber_telegram_accounts import BarberTelegramAccount
from app.services.telegram_service import send_notification, NotificationType

logger = logging.getLogger(__name__)


async def recalculate_leaderboard_rankings():
    """
    Daily job (03:00 UTC): Recalculate leaderboard rankings for all barberos.

    Updates:
    - Weekly ranking position (resets Sundays at 00:00 UTC)
    - Monthly ranking position (resets 1st of month at 00:00 UTC)
    - All-time ranking position
    - Tier badge assignment (Platinum > Gold > Silver > Bronze)
    """
    async with AsyncSessionLocal() as db:
        try:
            # Fetch all leaderboard stats with barber data
            result = await db.execute(
                select(BarberLeaderboardStats).options(
                    selectinload(BarberLeaderboardStats.barber_partner)
                )
            )
            all_stats = result.scalars().all()

            if not all_stats:
                logger.info("No leaderboard stats found, skipping recalculation")
                return

            now = datetime.now(timezone.utc)

            # Sort by clients (this_week, this_month, all_time) to determine rankings
            # Week ranking (clients_this_week)
            week_sorted = sorted(
                all_stats,
                key=lambda x: x.clients_this_week,
                reverse=True
            )

            # Month ranking (clients_this_month)
            month_sorted = sorted(
                all_stats,
                key=lambda x: x.clients_this_month,
                reverse=True
            )

            # All-time ranking (clients_all_time)
            alltime_sorted = sorted(
                all_stats,
                key=lambda x: x.clients_all_time,
                reverse=True
            )

            # Update rankings and tiers
            for idx, stat in enumerate(week_sorted, 1):
                stat.week_ranking_position = idx

            for idx, stat in enumerate(month_sorted, 1):
                stat.month_ranking_position = idx

            for idx, stat in enumerate(alltime_sorted, 1):
                stat.all_time_ranking_position = idx

            # Assign tier badges based on all-time ranking
            # Top 10 = Platinum, 11-25 = Gold, 26-50 = Silver, 51+ = Bronze
            for stat in all_stats:
                if stat.all_time_ranking_position <= 10:
                    stat.current_tier = RankingTier.PLATINUM
                elif stat.all_time_ranking_position <= 25:
                    stat.current_tier = RankingTier.GOLD
                elif stat.all_time_ranking_position <= 50:
                    stat.current_tier = RankingTier.SILVER
                else:
                    stat.current_tier = RankingTier.BRONZE

                stat.last_updated = now

            await db.commit()
            logger.info(
                "Leaderboard rankings recalculated: %d barberos updated",
                len(all_stats)
            )

        except Exception as e:
            logger.error("Error recalculating leaderboard rankings: %s", str(e))
            await db.rollback()


async def send_weekly_telegram_summary():
    """
    Weekly job (Sunday 08:00 UTC): Send Telegram summary to all connected barberos.

    Sends:
    - Their current ranking position (week/month/all-time)
    - Current tier badge
    - Clients count for the period
    - Top 3 peers nearby in ranking
    """
    async with AsyncSessionLocal() as db:
        try:
            # Fetch all Telegram accounts that have notifications enabled
            result = await db.execute(
                select(BarberTelegramAccount).where(
                    BarberTelegramAccount.is_connected == True,
                    BarberTelegramAccount.notifications_enabled == True,
                    BarberTelegramAccount.notify_on_weekly_summary == True,
                ).options(
                    selectinload(BarberTelegramAccount.barber_partner).selectinload(
                        BarberPartner.leaderboard_stats
                    )
                )
            )
            telegram_accounts = result.scalars().all()

            if not telegram_accounts:
                logger.info("No Telegram accounts with weekly summary enabled")
                return

            sent_count = 0
            for account in telegram_accounts:
                try:
                    # Get stats for this barbero
                    stats = account.barber_partner.leaderboard_stats
                    if not stats:
                        continue

                    # Send weekly summary notification
                    await send_notification(
                        telegram_chat_id=account.telegram_chat_id,
                        notification_type=NotificationType.WEEKLY_SUMMARY,
                        data={
                            "barber_name": account.barber_partner.name,
                            "week_clients": stats.clients_this_week,
                            "week_ranking": stats.week_ranking_position,
                            "month_clients": stats.clients_this_month,
                            "month_ranking": stats.month_ranking_position,
                            "all_time_clients": stats.clients_all_time,
                            "all_time_ranking": stats.all_time_ranking_position,
                            "current_tier": stats.current_tier.value if stats.current_tier else "bronze",
                        },
                        language_code=account.language_code or "es",
                    )

                    # Update last_webhook_delivery_at
                    account.last_webhook_delivery_at = datetime.now(timezone.utc)
                    account.webhook_delivery_status = "success"
                    sent_count += 1

                except Exception as e:
                    logger.error(
                        "Error sending weekly summary to %s: %s",
                        account.telegram_user_id,
                        str(e),
                    )
                    account.webhook_delivery_status = "failed"
                    account.consecutive_failures = (account.consecutive_failures or 0) + 1

            await db.commit()
            logger.info("Weekly Telegram summaries sent to %d barberos", sent_count)

        except Exception as e:
            logger.error("Error in weekly telegram summary job: %s", str(e))
            await db.rollback()


async def auto_approve_high_quality_photos():
    """
    Daily job (03:00 UTC): Auto-approve reference photos with quality_score >= 0.80.

    Criteria:
    - status == PENDING
    - quality_score >= 0.80
    - Sets status to APPROVED
    - Sets validated_at to current timestamp
    """
    async with AsyncSessionLocal() as db:
        try:
            now = datetime.now(timezone.utc)

            # Find all pending photos with high quality
            result = await db.execute(
                select(BarberReferencePhoto).where(
                    BarberReferencePhoto.validation_status == PhotoValidationStatus.PENDING,
                    BarberReferencePhoto.quality_score >= 0.80,
                )
            )
            high_quality_photos = result.scalars().all()

            if not high_quality_photos:
                logger.info("No high-quality pending photos found")
                return

            # Auto-approve all high-quality photos
            for photo in high_quality_photos:
                photo.validation_status = PhotoValidationStatus.APPROVED
                photo.validated_at = now

            await db.commit()
            logger.info(
                "Auto-approved %d high-quality reference photos",
                len(high_quality_photos)
            )

        except Exception as e:
            logger.error("Error auto-approving high-quality photos: %s", str(e))
            await db.rollback()
