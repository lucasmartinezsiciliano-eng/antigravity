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
    event_id = event.get("id", "")
    logger.info("Stripe webhook received: %s id=%s", event_type, event_id)

    # Idempotency: skip if we already processed this exact Stripe event
    if event_id:
        from app.models.analysis import StripeEventLog
        existing = (await db.execute(
            select(StripeEventLog).where(StripeEventLog.stripe_event_id == event_id)
        )).scalar_one_or_none()
        if existing:
            logger.info("Stripe event %s already processed — skipping", event_id)
            return {"received": True}
        db.add(StripeEventLog(stripe_event_id=event_id, event_type=event_type))
        await db.flush()

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        if session.get("metadata", {}).get("upsell_type"):
            await _handle_upsell_completed(event, db)
        else:
            await _handle_checkout_completed(event, db)

    elif event_type == "checkout.session.expired":
        session = event["data"]["object"]
        analysis_id = session.get("metadata", {}).get("analysis_id")
        if analysis_id:
            await _update_analysis_status(analysis_id, "cancelled", db)

    return {"received": True}


async def _handle_checkout_completed(event, db: AsyncSession) -> None:
    from datetime import datetime, timezone
    from app.services.email_service import send_payment_confirmed, trigger_n8n_marketing_sequence

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

    # B — capture email from Stripe customer_details
    user_email: str | None = (session.get("customer_details") or {}).get("email")
    if user_email:
        analysis.user_email = user_email

    analysis.status = "paid"
    analysis.stripe_payment_intent_id = session.get("payment_intent")
    analysis.amount_paid_cents = session.get("amount_total", 0)
    analysis.paid_at = datetime.now(timezone.utc)
    analysis.includes_colorimetry = metadata.get("include_colorimetry") == "True"
    analysis.includes_products_guide = metadata.get("include_products_guide") == "True"

    logger.info(
        "Payment confirmed for analysis %s — amount=%d cents — email=%s",
        analysis_id, analysis.amount_paid_cents, user_email or "unknown",
    )

    # C — transactional email: payment confirmed (always, no marketing consent needed)
    if user_email:
        await send_payment_confirmed(user_email, analysis_id)

    # D — n8n marketing sequence (only if user opted in)
    if user_email and analysis.marketing_consent:
        await trigger_n8n_marketing_sequence(
            email=user_email,
            analysis_id=analysis_id,
            created_at_iso=analysis.created_at.isoformat(),
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


async def _handle_upsell_completed(event, db: AsyncSession) -> None:
    from app.api.routes.analysis import _generate_upsell_content

    session = event["data"]["object"]
    metadata = session.get("metadata", {})
    analysis_id = metadata.get("analysis_id")
    upsell_type = metadata.get("upsell_type")

    if not analysis_id or not upsell_type:
        return

    stmt = select(Analysis).where(Analysis.id == analysis_id)
    analysis = (await db.execute(stmt)).scalar_one_or_none()
    if not analysis:
        logger.error("Analysis %s not found for upsell webhook", analysis_id)
        return

    if upsell_type == "seasonal":
        analysis.includes_seasonal = True
    else:
        _generate_upsell_content(analysis, upsell_type)
    await db.commit()
    logger.info("Upsell %s processed for analysis %s", upsell_type, analysis_id)


async def _update_analysis_status(analysis_id: str, new_status: str, db: AsyncSession) -> None:
    stmt = select(Analysis).where(Analysis.id == analysis_id)
    analysis = (await db.execute(stmt)).scalar_one_or_none()
    if analysis:
        analysis.status = new_status
