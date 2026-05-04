"""
Payment webhook handler.

POST /payments/webhook  — Stripe webhook endpoint
GET  /payments/success  — Payment success redirect (from Stripe)
GET  /payments/cancel   — Payment cancel redirect
"""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.analysis import Analysis
from app.services import stripe_service
from app.api.routes.barbers import record_barber_commission

router = APIRouter(prefix="/payments", tags=["payments"])
logger = logging.getLogger(__name__)


@router.post("/webhook", status_code=200)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(..., alias="stripe-signature"),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Stripe webhook events.
    Verifies signature, updates analysis status, records barber commissions.
    """
    payload = await request.body()

    try:
        event = stripe_service.verify_webhook(payload, stripe_signature)
    except ValueError as e:
        logger.warning("Invalid webhook signature: %s", e)
        raise HTTPException(400, "Invalid signature")

    event_type = event["type"]
    logger.info("Stripe webhook received: %s", event_type)

    if event_type == "checkout.session.completed":
        await _handle_checkout_completed(event, db)

    elif event_type == "checkout.session.expired":
        session = event["data"]["object"]
        analysis_id = session.get("metadata", {}).get("analysis_id")
        if analysis_id:
            await _update_analysis_status(analysis_id, "cancelled", db)

    return {"received": True}


async def _handle_checkout_completed(event, db: AsyncSession) -> None:
    session = event["data"]["object"]
    metadata = session.get("metadata", {})
    analysis_id = metadata.get("analysis_id")

    if not analysis_id:
        logger.warning("checkout.session.completed with no analysis_id in metadata")
        return

    stmt = select(Analysis).where(Analysis.id == analysis_id)
    analysis = (await db.execute(stmt)).scalar_one_or_none()
    if not analysis:
        logger.error("Analysis %s not found for completed checkout", analysis_id)
        return

    from datetime import datetime, timezone
    analysis.status = "paid"
    analysis.stripe_payment_intent_id = session.get("payment_intent")
    analysis.amount_paid_cents = session.get("amount_total", 0)
    analysis.paid_at = datetime.now(timezone.utc)
    analysis.includes_colorimetry = metadata.get("include_colorimetry") == "True"
    analysis.includes_products_guide = metadata.get("include_products_guide") == "True"

    logger.info(
        "Payment confirmed for analysis %s — amount=%d cents",
        analysis_id, analysis.amount_paid_cents
    )

    # Record barber commission if a barber code was used
    commission_data = stripe_service.extract_commission_data(event)
    if commission_data:
        await record_barber_commission(
            barber_id=commission_data["barber_id"],
            analysis_id=analysis_id,
            stripe_charge_id=commission_data["stripe_charge_id"],
            db=db,
        )


async def _update_analysis_status(analysis_id: str, new_status: str, db: AsyncSession) -> None:
    stmt = select(Analysis).where(Analysis.id == analysis_id)
    analysis = (await db.execute(stmt)).scalar_one_or_none()
    if analysis:
        analysis.status = new_status
