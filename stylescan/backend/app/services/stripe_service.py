"""
StyleScan — Stripe Payment Service

Handles:
- One-time payment checkout sessions (base + upsells)
- Barber affiliate promotion codes (unique per barber, €1 discount)
- Commission tracking via webhook events
- Monthly payout calculation

Architecture:
- Coupons + PromotionCodes (not plain coupons) for per-barber tracking
- Manual commission DB tracking (no Stripe Connect for MVP)
- Stripe Radar metadata for fraud prevention
"""

import logging
from datetime import datetime, timezone, timedelta

import stripe

from app.core.config import settings

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


# ---------------------------------------------------------------------------
# Checkout session creation
# ---------------------------------------------------------------------------
def create_checkout_session(
    analysis_id: str,
    success_url: str,
    cancel_url: str,
    promo_code: str | None = None,
    include_colorimetry: bool = False,
    include_products_guide: bool = False,
) -> stripe.checkout.Session:
    """
    Create a Stripe Checkout Session for the analysis purchase.
    Applies barber promo code if provided.
    """
    line_items = [
        {
            "price_data": {
                "currency": "eur",
                "product_data": {
                    "name": "StyleScan — Análisis de imagen personalizado",
                    "description": (
                        "Análisis facial completo con IA: forma de cráneo, proporciones, "
                        "asimetría y 3 cortes de pelo recomendados con instrucciones para tu barbero."
                    ),
                    "images": [],
                },
                "unit_amount": settings.PRICE_BASE_ANALYSIS,
            },
            "quantity": 1,
        }
    ]

    # Upsells
    if include_colorimetry and include_products_guide:
        line_items.append({
            "price_data": {
                "currency": "eur",
                "product_data": {"name": "Pack Completo — Colorimetría + Guía de productos"},
                "unit_amount": settings.PRICE_PACK_COMPLETE,
            },
            "quantity": 1,
        })
    elif include_colorimetry:
        line_items.append({
            "price_data": {
                "currency": "eur",
                "product_data": {"name": "Colorimetría personalizada"},
                "unit_amount": settings.PRICE_COLORIMETRY,
            },
            "quantity": 1,
        })
    elif include_products_guide:
        line_items.append({
            "price_data": {
                "currency": "eur",
                "product_data": {"name": "Guía de productos personalizada"},
                "unit_amount": settings.PRICE_PRODUCTS_GUIDE,
            },
            "quantity": 1,
        })

    session_params: dict = {
        "payment_method_types": ["card"],
        "line_items": line_items,
        "mode": "payment",
        "success_url": f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": cancel_url,
        "metadata": {
            "analysis_id": analysis_id,
            "include_colorimetry": str(include_colorimetry),
            "include_products_guide": str(include_products_guide),
            "promo_code": promo_code or "",
        },
        "payment_intent_data": {
            "metadata": {
                "analysis_id": analysis_id,
                "promo_code": promo_code or "",
            }
        },
    }

    # Apply promo code discount
    if promo_code:
        session_params["discounts"] = [{"promotion_code": promo_code}]
    else:
        # Allow customer to enter a code themselves
        session_params["allow_promotion_codes"] = True

    return stripe.checkout.Session.create(**session_params)


# ---------------------------------------------------------------------------
# Barber promotion code management
# ---------------------------------------------------------------------------
def get_or_create_base_coupon() -> str:
    """
    Get or create the base €1 off coupon that all barber promo codes reference.
    Returns the coupon ID. Should be called once at setup.
    """
    if settings.STRIPE_BASE_COUPON_ID:
        return settings.STRIPE_BASE_COUPON_ID

    coupon = stripe.Coupon.create(
        amount_off=100,
        currency="eur",
        duration="once",
        name="Descuento colaborador barbería StyleScan (-€1)",
        metadata={"program": "barbershop_affiliate"},
    )
    logger.info("Created base coupon: %s", coupon.id)
    return coupon.id


def create_barber_promo_code(
    barber_id: str,
    barber_name: str,
    barbershop_name: str,
    max_uses: int = 500,
) -> tuple[str, str]:
    """
    Create a unique Stripe PromotionCode for a barber partner.
    Returns (promotion_code_string, stripe_promo_code_id).

    Code format: STYLESCAN-{NAME}-{ID_SHORT}
    Example: STYLESCAN-CARLOS-A1B2
    """
    coupon_id = get_or_create_base_coupon()

    # Code must be uppercase alphanumeric + hyphens
    clean_name = "".join(c for c in barber_name.upper() if c.isalnum())[:12]
    id_suffix = barber_id[-4:].upper()
    code = f"STYLESCAN-{clean_name}-{id_suffix}"

    expires_at = int((datetime.now(timezone.utc) + timedelta(days=365)).timestamp())

    promo = stripe.PromotionCode.create(
        coupon=coupon_id,
        code=code,
        max_redemptions=max_uses,
        expires_at=expires_at,
        metadata={
            "barber_id": barber_id,
            "barber_name": barber_name,
            "barbershop_name": barbershop_name,
            "program": "barbershop_affiliate",
        },
    )

    logger.info("Created promo code %s for barber %s (%s)", code, barber_id, barber_name)
    return code, promo.id


def deactivate_barber_promo_code(stripe_promo_code_id: str) -> None:
    """Deactivate a barber's promo code (e.g., when they leave the program)."""
    stripe.PromotionCode.modify(stripe_promo_code_id, active=False)
    logger.info("Deactivated promo code: %s", stripe_promo_code_id)


# ---------------------------------------------------------------------------
# Webhook handling
# ---------------------------------------------------------------------------
def verify_webhook(payload: bytes, sig_header: str) -> stripe.Event:
    """Verify Stripe webhook signature. Raises ValueError if invalid."""
    try:
        return stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError as e:
        raise ValueError(f"Invalid webhook signature: {e}")


def extract_commission_data(event: stripe.Event) -> dict | None:
    """
    Extract commission-relevant data from a checkout.session.completed event.
    Returns dict with barber_id, analysis_id, amount_cents if a barber code was used.
    Returns None if no barber code was involved.
    """
    if event["type"] != "checkout.session.completed":
        return None

    session = event["data"]["object"]
    metadata = session.get("metadata", {})

    promo_code = metadata.get("promo_code", "")
    analysis_id = metadata.get("analysis_id", "")

    if not promo_code or not analysis_id:
        return None

    # Look up the promotion code in Stripe to find the barber
    try:
        promos = stripe.PromotionCode.list(code=promo_code, limit=1)
        if not promos.data:
            return None

        promo = promos.data[0]
        barber_id = promo.metadata.get("barber_id")

        if not barber_id:
            return None

        return {
            "barber_id": barber_id,
            "analysis_id": analysis_id,
            "stripe_charge_id": session.get("payment_intent", ""),
            "amount_cents": settings.BARBER_COMMISSION_CENTS,
            "promo_code": promo_code,
        }

    except stripe.error.StripeError as e:
        logger.error("Stripe error extracting commission data: %s", e)
        return None


# ---------------------------------------------------------------------------
# Commission payout calculation (called monthly by admin)
# ---------------------------------------------------------------------------
def calculate_monthly_payout_summary(commissions: list[dict]) -> dict:
    """
    Aggregate commission records by barber for monthly payout report.
    Input: list of dicts with barber_id, amount_cents, created_at.
    Returns: dict of barber_id -> total_eur
    """
    totals: dict[str, int] = {}
    for c in commissions:
        bid = c["barber_id"]
        totals[bid] = totals.get(bid, 0) + c["amount_cents"]

    return {bid: round(cents / 100, 2) for bid, cents in totals.items()}
