"""
Barber partner management routes.

POST /barbers/register      — Register a new barber partner (creates promo code)
GET  /barbers/{id}/dashboard — Barber dashboard: stats, earnings, link to pay
POST /barbers/{id}/payout   — Request payout (admin-triggered or self-service)
GET  /barbers               — List all barbers (admin only)
"""

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, Field

from app.core.config import settings
from app.core.database import get_db
from app.models.barber import BarberPartner, Commission
from app.models.analysis import Analysis
from app.services import stripe_service

router = APIRouter(prefix="/barbers", tags=["barbers"])
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class BarberRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    barbershop_name: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    phone: str = Field(..., min_length=9, max_length=20)
    city: str
    province: str = "Tarragona"
    instagram_handle: str | None = None
    iban: str | None = None


class BarberRegisterResponse(BaseModel):
    barber_id: str
    promo_code: str
    message: str


class BarberDashboard(BaseModel):
    barber_id: str
    name: str
    barbershop_name: str
    promo_code: str
    total_uses: int
    total_earned_euros: float
    total_paid_out_euros: float
    pending_payout_euros: float
    is_active: bool
    contract_signed_at: str | None
    recent_uses: list[dict]


# ---------------------------------------------------------------------------
# Register barber
# ---------------------------------------------------------------------------
@router.post("/register", response_model=BarberRegisterResponse, status_code=201)
@limiter.limit("5/hour")
async def register_barber(
    request: Request,
    body: BarberRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new barber in the affiliate program.
    Automatically creates a unique Stripe PromotionCode.
    """
    # Check duplicate email
    stmt = select(BarberPartner).where(BarberPartner.email == body.email)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(400, "Ya existe un barbero registrado con ese email.")

    barber_id = str(uuid.uuid4())

    # Create Stripe promo code
    try:
        code, stripe_promo_id = stripe_service.create_barber_promo_code(
            barber_id=barber_id,
            barber_name=body.name,
            barbershop_name=body.barbershop_name,
        )
    except Exception as e:
        logger.error("Stripe promo code creation failed: %s", e)
        raise HTTPException(500, "Error al crear el código en el sistema de pagos.")

    partner = BarberPartner(
        id=barber_id,
        name=body.name,
        barbershop_name=body.barbershop_name,
        email=body.email,
        phone=body.phone,
        city=body.city,
        province=body.province,
        instagram_handle=body.instagram_handle,
        iban=body.iban,
        promo_code=code,
        stripe_promo_code_id=stripe_promo_id,
        # contract_signed_at left None — set explicitly via POST /barbers/{id}/sign-contract
    )
    db.add(partner)
    await db.flush()

    logger.info("New barber partner registered: %s (%s) code=%s", body.name, barber_id, code)

    return BarberRegisterResponse(
        barber_id=barber_id,
        promo_code=code,
        message=(
            f"¡Bienvenido a VISAI, {body.name}! "
            f"Tu código es {code}. Compártelo con tus clientes "
            f"para que ahorren €2 en el análisis y tú ganes €2 por cada uso."
        ),
    )


# ---------------------------------------------------------------------------
# Sign contract
# ---------------------------------------------------------------------------
class SignContractRequest(BaseModel):
    contract_version: str = "1.0"
    ip_address: str | None = None
    user_agent: str | None = None


@router.post("/{barber_id}/sign-contract", status_code=200)
@limiter.limit("10/hour")
async def sign_contract(
    request: Request,
    barber_id: str,
    body: SignContractRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Barber explicitly accepts the partnership contract.
    Sets contract_signed_at — only after this is the promo code considered active.
    """
    partner = await _get_partner_or_404(barber_id, db)

    if partner.contract_signed_at is not None:
        return {"message": "Contrato ya firmado.", "signed_at": partner.contract_signed_at.isoformat()}

    from datetime import timezone
    partner.contract_signed_at = datetime.now(timezone.utc)
    await db.flush()

    logger.info(
        "Contract signed: barber=%s version=%s ip=%s",
        barber_id, body.contract_version, body.ip_address,
    )
    return {"message": "Contrato firmado correctamente.", "signed_at": partner.contract_signed_at.isoformat()}


# ---------------------------------------------------------------------------
# Barber dashboard
# ---------------------------------------------------------------------------
@router.get("/{barber_id}/dashboard", response_model=BarberDashboard)
async def get_barber_dashboard(
    barber_id: str,
    db: AsyncSession = Depends(get_db),
):
    partner = await _get_partner_or_404(barber_id, db)

    # Pending payout
    pending_cents = partner.total_earned_cents - partner.total_paid_out_cents

    # Recent 10 uses
    stmt = (
        select(Analysis)
        .where(
            Analysis.barber_partner_id == barber_id,
            Analysis.status == "completed",
        )
        .order_by(Analysis.created_at.desc())
        .limit(10)
    )
    recent_analyses = (await db.execute(stmt)).scalars().all()
    recent_uses = [
        {
            "date": a.created_at.strftime("%d/%m/%Y"),
            "earned_euros": settings.BARBER_COMMISSION_CENTS / 100,
        }
        for a in recent_analyses
    ]

    return BarberDashboard(
        barber_id=partner.id,
        name=partner.name,
        barbershop_name=partner.barbershop_name,
        promo_code=partner.promo_code,
        total_uses=partner.total_uses,
        total_earned_euros=partner.total_earned_cents / 100,
        total_paid_out_euros=partner.total_paid_out_cents / 100,
        pending_payout_euros=pending_cents / 100,
        is_active=partner.is_active,
        contract_signed_at=partner.contract_signed_at.isoformat() if partner.contract_signed_at else None,
        recent_uses=recent_uses,
    )


# ---------------------------------------------------------------------------
# Webhook: update barber stats when commission recorded
# ---------------------------------------------------------------------------
async def record_barber_commission(
    barber_id: str,
    analysis_id: str,
    stripe_charge_id: str,
    db: AsyncSession,
) -> None:
    """Called internally when a payment webhook confirms a barber code was used."""
    partner = await _get_partner_or_404(barber_id, db)

    commission = Commission(
        id=str(uuid.uuid4()),
        barber_partner_id=barber_id,
        analysis_id=analysis_id,
        stripe_charge_id=stripe_charge_id,
        amount_cents=settings.BARBER_COMMISSION_CENTS,
        status="unpaid",
    )
    db.add(commission)

    partner.total_uses += 1
    partner.total_earned_cents += settings.BARBER_COMMISSION_CENTS

    logger.info(
        "Commission recorded: barber=%s analysis=%s amount=€%.2f",
        barber_id, analysis_id, settings.BARBER_COMMISSION_CENTS / 100
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _get_partner_or_404(barber_id: str, db: AsyncSession) -> BarberPartner:
    stmt = select(BarberPartner).where(BarberPartner.id == barber_id)
    partner = (await db.execute(stmt)).scalar_one_or_none()
    if not partner:
        raise HTTPException(404, "Barbero no encontrado.")
    return partner
