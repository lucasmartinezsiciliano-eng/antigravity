from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class BarberPartner(Base):
    """
    Barbershop / barber registered in the affiliate program.
    Each barber gets a unique promotion code.
    """
    __tablename__ = "barber_partners"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Barber info
    name: Mapped[str] = mapped_column(String(200))
    barbershop_name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(30))
    city: Mapped[str] = mapped_column(String(100))
    province: Mapped[str] = mapped_column(String(100), default="Tarragona")
    instagram_handle: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Code
    promo_code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    stripe_promo_code_id: Mapped[str] = mapped_column(String(255), nullable=True)
    stripe_coupon_id: Mapped[str] = mapped_column(String(255), nullable=True)

    # Commission tracking
    total_uses: Mapped[int] = mapped_column(Integer, default=0)
    total_earned_cents: Mapped[int] = mapped_column(Integer, default=0)
    total_paid_out_cents: Mapped[int] = mapped_column(Integer, default=0)

    # Payout info
    iban: Mapped[str | None] = mapped_column(String(34), nullable=True)  # Encrypted in prod
    iban_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    stripe_connect_account_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    contract_signed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Content creator tier (barbers who also post content)
    is_content_creator: Mapped[bool] = mapped_column(Boolean, default=False)
    content_bonus_rate: Mapped[float] = mapped_column(Float, default=0.0)

    # Relationships
    analyses: Mapped[list["Analysis"]] = relationship(  # noqa: F821
        back_populates="barber_partner"
    )
    commissions: Mapped[list["Commission"]] = relationship(
        back_populates="barber_partner"
    )


class Commission(Base):
    """
    Individual commission record per analysis that used a barber code.
    Aggregated monthly for payouts.
    """
    __tablename__ = "commissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    barber_partner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("barber_partners.id")
    )
    analysis_id: Mapped[str] = mapped_column(String(36))
    stripe_charge_id: Mapped[str] = mapped_column(String(255))

    amount_cents: Mapped[int] = mapped_column(Integer, default=100)  # €1.00
    status: Mapped[str] = mapped_column(String(50), default="unpaid")
    # unpaid → processing → paid

    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payout_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)

    barber_partner: Mapped["BarberPartner"] = relationship(back_populates="commissions")
