from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class BarberTelegramAccount(Base):
    """
    Telegram integration for barber notifications.
    Barbero optionally connects their Telegram account to receive real-time
    commission and ranking notifications.
    """
    __tablename__ = "barber_telegram_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Foreign key
    barber_partner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("barber_partners.id"), unique=True, index=True
    )
    # unique=True: one Telegram per barber

    # Telegram identifiers
    telegram_user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    # User ID from Telegram (@username → user_id)

    telegram_chat_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    # Chat ID where messages are sent (usually = user_id for private chats)

    telegram_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # @username for user reference

    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Connection status
    is_connected: Mapped[bool] = mapped_column(Boolean, default=True)
    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Notification preferences
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_on_new_analysis: Mapped[bool] = mapped_column(Boolean, default=True)
    # Notify when client uses barber code

    notify_on_ranking_change: Mapped[bool] = mapped_column(Boolean, default=True)
    # Notify when ranking position changes

    notify_on_weekly_summary: Mapped[bool] = mapped_column(Boolean, default=True)
    # Notify every Sunday with weekly summary

    notify_on_commission_milestone: Mapped[bool] = mapped_column(Boolean, default=True)
    # Notify on €10, €50, €100 milestones (future)

    # Language preference
    language_code: Mapped[str] = mapped_column(String(10), default="es")
    # es, en, fr, etc. from Telegram locale

    # Last interaction
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Track if Telegram account is still active / responsive

    # Webhook delivery tracking
    last_webhook_delivery_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    webhook_delivery_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # success, failed, pending

    # Failed delivery count (for alerting)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)

    # Notes (for support)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship
    barber_partner: Mapped["BarberPartner"] = relationship(back_populates="telegram_account")  # noqa: F821
