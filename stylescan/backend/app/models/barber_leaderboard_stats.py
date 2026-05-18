from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from app.core.database import Base


class RankingTier(str, Enum):
    """Cosmetic ranking tiers based on position."""
    PLATINUM = "platinum"  # Top 10
    GOLD = "gold"  # Top 11-25
    SILVER = "silver"  # Top 26-50
    BRONZE = "bronze"  # Top 51+


class LeaderboardPeriod(str, Enum):
    """Time period for leaderboard snapshot."""
    WEEK = "week"
    MONTH = "month"
    ALL_TIME = "all_time"


class BarberLeaderboardStats(Base):
    """
    Leaderboard stats for barbers, tracking client usage of their promo codes.
    Updated weekly (Sunday midnight) to reflect cumulative and period-based rankings.
    Used for cosmetic ranking badges (no monetary rewards in MVP).
    """
    __tablename__ = "barber_leaderboard_stats"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Foreign key
    barber_partner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("barber_partners.id"), unique=True, index=True
    )

    # Weekly stats (reset every Sunday 00:00 UTC)
    clients_this_week: Mapped[int] = mapped_column(Integer, default=0)
    week_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    week_ranking_position: Mapped[int] = mapped_column(Integer, nullable=True)
    # Position in weekly ranking (1=first place)

    # Monthly stats (reset every 1st of month 00:00 UTC)
    clients_this_month: Mapped[int] = mapped_column(Integer, default=0)
    month_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    month_ranking_position: Mapped[int] = mapped_column(Integer, nullable=True)

    # All-time cumulative
    clients_all_time: Mapped[int] = mapped_column(Integer, default=0)
    all_time_ranking_position: Mapped[int] = mapped_column(Integer, nullable=True)

    # Revenue (for future Month 2+)
    revenue_this_week_cents: Mapped[int] = mapped_column(Integer, default=0)
    revenue_all_time_cents: Mapped[int] = mapped_column(Integer, default=0)

    # Ranking tier (cosmetic, based on all_time_ranking_position)
    current_tier: Mapped[str] = mapped_column(
        SQLEnum(RankingTier),
        default=RankingTier.BRONZE
    )

    # Last update timestamp
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationship
    barber_partner: Mapped["BarberPartner"] = relationship(back_populates="leaderboard_stats")  # noqa: F821
