from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, Boolean, DateTime, JSON, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Analysis(Base):
    """
    Stores completed analysis results.
    RGPD: Photos are NEVER stored. Only derived metrics + report text.
    Metrics are deleted after METRICS_RETENTION_DAYS.
    """
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Payment tracking
    stripe_payment_intent_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    stripe_session_id: Mapped[str] = mapped_column(String(255), nullable=True)
    amount_paid_cents: Mapped[int] = mapped_column(Integer, default=0)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Barber attribution
    barber_code_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    barber_partner_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("barber_partners.id"), nullable=True
    )

    # User identification
    phone_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    user_email: Mapped[str | None] = mapped_column(String(255), nullable=True)  # from Stripe after payment
    marketing_consent: Mapped[bool] = mapped_column(Boolean, default=False)     # RGPD: explicit email marketing opt-in
    marketing_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Face metrics (derived from MediaPipe — NOT raw landmarks, NOT photos)
    # Nullable: populated after photo processing, not at initiation
    face_shape: Mapped[str | None] = mapped_column(String(50), nullable=True)
    length_width_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    forehead_width_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    jaw_width_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    asymmetry_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    cranial_proportion: Mapped[str | None] = mapped_column(String(50), nullable=True)
    analysis_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    photos_analyzed: Mapped[int] = mapped_column(Integer, default=0)

    # Quiz answers (stored as JSON)
    quiz_answers: Mapped[dict] = mapped_column(JSON, default={})

    # Generated report (Claude output)
    report: Mapped[dict] = mapped_column(JSON, default={})

    # Purchased add-ons
    includes_colorimetry: Mapped[bool] = mapped_column(Boolean, default=False)
    includes_products_guide: Mapped[bool] = mapped_column(Boolean, default=False)
    includes_seasonal: Mapped[bool] = mapped_column(Boolean, default=False)
    colorimetry_report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    products_guide: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    seasonal_report: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Generated visuals (virtual try-on images via fal.ai)
    generated_visuals: Mapped[list | None] = mapped_column(JSON, nullable=True)
    visuals_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # visuals_status: None | "processing" | "ready" | "failed"

    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending")
    # pending → paid → processing → completed → expired

    # RGPD: deletion tracking
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    photos_deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    barber_partner: Mapped["BarberPartner | None"] = relationship(  # noqa: F821
        back_populates="analyses"
    )
    consent_log: Mapped["ConsentLog | None"] = relationship(  # noqa: F821
        back_populates="analysis", uselist=False
    )


class StripeEventLog(Base):
    """Idempotency log — prevents double-processing Stripe webhook retries."""
    __tablename__ = "stripe_event_log"
    __table_args__ = (UniqueConstraint("stripe_event_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stripe_event_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
