from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ConsentLog(Base):
    """
    RGPD Article 9 compliance: explicit consent record for biometric data processing.
    Retained for 5 years (legal requirement), even after analysis data is deleted.
    This is NOT a user account — it's a per-transaction audit trail.
    """
    __tablename__ = "consent_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    analysis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("analyses.id"), unique=True
    )

    # Consent details — what the user agreed to (text version at time of consent)
    consent_version: Mapped[str] = mapped_column(String(20))  # e.g., "1.0"
    privacy_policy_version: Mapped[str] = mapped_column(String(20))
    consent_text_hash: Mapped[str] = mapped_column(String(64))  # SHA-256 of consent text shown

    # Explicit RGPD Article 9 affirmations (all must be True to proceed)
    consented_biometric_processing: Mapped[bool] = mapped_column(Boolean, default=False)
    consented_special_category_data: Mapped[bool] = mapped_column(Boolean, default=False)
    consented_retention_90_days: Mapped[bool] = mapped_column(Boolean, default=False)
    consented_immediate_photo_deletion: Mapped[bool] = mapped_column(Boolean, default=False)
    consented_age_verification: Mapped[bool] = mapped_column(Boolean, default=False)

    # Technical proof
    ip_address_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)  # SHA-256
    device_fingerprint_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    consent_timestamp_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Withdrawal tracking
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    withdrawal_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    analysis: Mapped["Analysis"] = relationship(back_populates="consent_log")  # noqa: F821
