from datetime import datetime, timezone, timedelta
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from app.core.database import Base


class ConsentStatus(str, Enum):
    """Status of parental consent request."""
    PENDING = "pending"  # Waiting for parent response
    AUTHORIZED = "authorized"  # Parent confirmed via email link
    REJECTED = "rejected"  # Parent declined
    EXPIRED = "expired"  # Token expired (72 hours)


class ParentalConsentRequest(Base):
    """
    Parental consent request for clients under 18.
    RGPD Art. 8: biometric data of minors requires parental authorization.
    Process: child age detected → email sent to parent → parent clicks link with token → consent recorded.
    """
    __tablename__ = "parental_consent_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Analysis reference
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    # Note: We store analysis_id as string, not FK, because analysis might be deleted

    # Child info (detected from photos)
    child_age: Mapped[int] = mapped_column(Integer)
    # Age detected from facial analysis (approximate)

    # Parent contact
    parent_email: Mapped[str] = mapped_column(String(255), index=True)
    # Email provided by child or detected from barbershop

    # Authorization token (72-hour expiry)
    authorization_token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    # Random secure token for authorization link
    # Format: /consent/authorize?token={authorization_token}

    token_expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc) + timedelta(hours=72)
    )

    # Response
    consent_status: Mapped[str] = mapped_column(
        SQLEnum(ConsentStatus),
        default=ConsentStatus.PENDING
    )

    is_authorized: Mapped[bool] = mapped_column(Boolean, default=False)
    # Set to True when parent clicks authorization link before expiry

    authorized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Audit trail
    parent_ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    # IPv4 or IPv6
    parent_user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Email tracking
    email_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    email_opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    email_clicked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Retry tracking
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    last_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Analysis can proceed only if is_authorized=True and consent_status=AUTHORIZED before token_expires_at
