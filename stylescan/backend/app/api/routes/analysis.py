"""
Analysis routes — core user flow.

POST /analysis/initiate      — Create analysis record + return checkout URL
POST /analysis/{id}/photos   — Upload 1-5 photos for analysis (after payment confirmed)
GET  /analysis/{id}          — Get analysis result
POST /analysis/{id}/consent  — Record RGPD consent (required before photo upload)
DELETE /analysis/{id}        — Right to erasure (Art. 17 RGPD)
"""

import hashlib
import logging
import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.models.analysis import Analysis
from app.models.barber import BarberPartner
from app.models.consent import ConsentLog
from app.services import face_analysis, claude_service, photo_service, stripe_service
from app.schemas.analysis import (
    AnalysisInitiateRequest,
    AnalysisInitiateResponse,
    ConsentRequest,
    AnalysisResult,
)

router = APIRouter(prefix="/analysis", tags=["analysis"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Initiate analysis + create checkout
# ---------------------------------------------------------------------------
@router.post("/initiate", response_model=AnalysisInitiateResponse, status_code=201)
async def initiate_analysis(
    body: AnalysisInitiateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Step 1: Create an analysis record and return a Stripe checkout URL.
    Payment must be completed before photo upload is allowed.
    """
    # Validate barber code if provided
    barber_partner_id = None
    promo_code_stripe = None

    if body.barber_code:
        stmt = select(BarberPartner).where(
            BarberPartner.promo_code == body.barber_code.upper(),
            BarberPartner.is_active == True,  # noqa: E712
        )
        partner = (await db.execute(stmt)).scalar_one_or_none()

        if not partner:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código de barbería no válido o inactivo.",
            )
        barber_partner_id = partner.id
        promo_code_stripe = partner.stripe_promo_code_id

    # Anti-fraud: limit analyses per phone (if provided)
    phone_hash = None
    if body.phone_hash:
        phone_hash = body.phone_hash
        # Check recent analyses from this phone
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        stmt = select(Analysis).where(
            Analysis.phone_hash == phone_hash,
            Analysis.created_at >= cutoff,
            Analysis.status == "completed",
        )
        recent = (await db.execute(stmt)).scalars().all()
        if len(recent) >= settings.MAX_ANALYSES_PER_PHONE_30D:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Máximo {settings.MAX_ANALYSES_PER_PHONE_30D} análisis por número en 30 días.",
            )

    analysis_id = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.METRICS_RETENTION_DAYS)

    analysis = Analysis(
        id=analysis_id,
        expires_at=expires_at,
        barber_partner_id=barber_partner_id,
        barber_code_used=body.barber_code,
        phone_hash=phone_hash,
        quiz_answers=body.quiz_answers or {},
        status="pending",
    )
    db.add(analysis)
    await db.flush()

    # Create Stripe checkout
    base_url = str(request.base_url).rstrip("/")
    session = stripe_service.create_checkout_session(
        analysis_id=analysis_id,
        success_url=f"{base_url}/api/v1/analysis/{analysis_id}/payment-success",
        cancel_url=f"{base_url}/api/v1/analysis/{analysis_id}/payment-cancel",
        promo_code=promo_code_stripe,
        include_colorimetry=body.include_colorimetry,
        include_products_guide=body.include_products_guide,
    )

    analysis.stripe_session_id = session.id
    await db.flush()

    return AnalysisInitiateResponse(
        analysis_id=analysis_id,
        checkout_url=session.url,
        amount_euros=settings.PRICE_BASE_ANALYSIS / 100,
        discount_applied=body.barber_code is not None,
    )


# ---------------------------------------------------------------------------
# RGPD Consent (required before photo upload)
# ---------------------------------------------------------------------------
@router.post("/{analysis_id}/consent", status_code=201)
async def record_consent(
    analysis_id: str,
    body: ConsentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Step 2: Record explicit RGPD consent for biometric data processing.
    All 5 affirmations must be True. Required before photo upload.
    """
    analysis = await _get_analysis_or_404(analysis_id, db)

    if analysis.status not in ("pending", "paid"):
        raise HTTPException(400, "El análisis no está en estado correcto para registrar consentimiento.")

    if not all([
        body.consented_biometric_processing,
        body.consented_special_category_data,
        body.consented_retention_90_days,
        body.consented_immediate_photo_deletion,
        body.consented_age_verification,
    ]):
        raise HTTPException(
            400,
            "Todos los consentimientos son obligatorios para proceder con el análisis biométrico."
        )

    # Hash identifying info for audit (never store plaintext)
    ip = request.client.host if request.client else "unknown"
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()

    consent = ConsentLog(
        id=str(uuid.uuid4()),
        analysis_id=analysis_id,
        consent_version="1.0",
        privacy_policy_version="1.0",
        consent_text_hash=body.consent_text_hash,
        consented_biometric_processing=body.consented_biometric_processing,
        consented_special_category_data=body.consented_special_category_data,
        consented_retention_90_days=body.consented_retention_90_days,
        consented_immediate_photo_deletion=body.consented_immediate_photo_deletion,
        consented_age_verification=body.consented_age_verification,
        ip_address_hash=ip_hash,
        device_fingerprint_hash=body.device_fingerprint_hash,
        user_agent=request.headers.get("user-agent", "")[:500],
        consent_timestamp_utc=datetime.now(timezone.utc),
    )
    db.add(consent)

    return {"message": "Consentimiento registrado correctamente.", "analysis_id": analysis_id}


# ---------------------------------------------------------------------------
# Photo upload + analysis execution
# ---------------------------------------------------------------------------
@router.post("/{analysis_id}/photos", status_code=202)
async def upload_photos_and_analyze(
    analysis_id: str,
    photos: list[UploadFile] = File(..., description="1 a 5 fotos del rostro"),
    db: AsyncSession = Depends(get_db),
):
    """
    Step 3: Upload 1-5 photos. Triggers face analysis + Claude report generation.
    Photos are processed in memory and NEVER stored to disk.
    """
    analysis = await _get_analysis_or_404(analysis_id, db)

    # Must be paid
    if analysis.status not in ("paid",):
        raise HTTPException(
            400,
            "El pago debe completarse antes de subir las fotos. "
            "Completa el pago y vuelve a intentarlo."
        )

    # Must have consent
    stmt = select(ConsentLog).where(ConsentLog.analysis_id == analysis_id)
    consent_log = (await db.execute(stmt)).scalar_one_or_none()
    if not consent_log:
        raise HTTPException(
            400,
            "Debes aceptar el tratamiento de datos biométricos antes de subir las fotos."
        )

    if len(photos) < 1 or len(photos) > 5:
        raise HTTPException(400, "Sube entre 1 y 5 fotos.")

    analysis.status = "processing"
    await db.flush()

    # --- Validate and prepare photos (all in memory, never to disk)
    valid_photo_bytes: list[bytes] = []
    validation_errors: list[str] = []

    for i, photo in enumerate(photos, 1):
        raw_bytes = await photo.read()
        val_result, prepared = photo_service.validate_and_prepare_photo(
            raw_bytes, photo.filename or f"photo_{i}"
        )
        if val_result.valid and prepared:
            valid_photo_bytes.append(prepared)
        else:
            validation_errors.append(f"Foto {i}: {val_result.error}")

        # Explicitly clear raw bytes (RGPD)
        del raw_bytes

    if not valid_photo_bytes:
        analysis.status = "paid"  # Reset so user can retry
        await db.flush()
        raise HTTPException(
            422,
            {
                "message": "Ninguna foto cumplió los requisitos de calidad.",
                "errors": validation_errors,
            },
        )

    # --- Face analysis (MediaPipe)
    try:
        metrics = face_analysis.analyze_photos(valid_photo_bytes)
    finally:
        # RGPD: delete photo bytes immediately after analysis
        del valid_photo_bytes

    if not metrics:
        analysis.status = "paid"
        await db.flush()
        raise HTTPException(
            422,
            "No se detectó ningún rostro en las fotos. "
            "Asegúrate de que la cara está visible y bien iluminada.",
        )

    # --- Claude report generation
    try:
        report = claude_service.generate_report(metrics, analysis.quiz_answers or {})
    except Exception as e:
        logger.error("Claude report generation failed for %s: %s", analysis_id, e)
        analysis.status = "paid"
        await db.flush()
        raise HTTPException(500, "Error al generar el informe. Inténtalo de nuevo.")

    # --- Persist metrics + report (no photos, never)
    analysis.face_shape = metrics.face_shape
    analysis.length_width_ratio = metrics.length_width_ratio
    analysis.forehead_width_ratio = metrics.forehead_to_face_ratio
    analysis.jaw_width_ratio = metrics.jaw_to_face_ratio
    analysis.asymmetry_score = metrics.asymmetry_score
    analysis.cranial_proportion = metrics.cranial_proportion
    analysis.analysis_confidence = metrics.confidence
    analysis.photos_analyzed = metrics.photos_used
    analysis.report = report
    analysis.status = "completed"
    analysis.photos_deleted_at = datetime.now(timezone.utc)  # Already deleted above

    logger.info(
        "Analysis %s completed: shape=%s confidence=%.0f%% photos=%d",
        analysis_id, metrics.face_shape, metrics.confidence * 100, metrics.photos_used
    )

    return {"message": "Análisis completado.", "analysis_id": analysis_id}


# ---------------------------------------------------------------------------
# Get result
# ---------------------------------------------------------------------------
@router.get("/{analysis_id}", response_model=AnalysisResult)
async def get_analysis(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the completed analysis result."""
    analysis = await _get_analysis_or_404(analysis_id, db)

    if analysis.status == "pending":
        raise HTTPException(402, "El pago está pendiente.")
    if analysis.status == "paid":
        raise HTTPException(202, "Las fotos están siendo procesadas.")
    if analysis.status == "processing":
        raise HTTPException(202, "El análisis está en progreso.")
    if analysis.deleted_at:
        raise HTTPException(410, "Este análisis ha sido eliminado a petición del usuario.")

    if analysis.status != "completed":
        raise HTTPException(400, f"Estado inesperado: {analysis.status}")

    return AnalysisResult(
        analysis_id=analysis.id,
        face_shape=analysis.face_shape,
        cranial_proportion=analysis.cranial_proportion,
        asymmetry_score=analysis.asymmetry_score,
        confidence=analysis.analysis_confidence,
        photos_analyzed=analysis.photos_analyzed,
        report=analysis.report,
        includes_colorimetry=analysis.includes_colorimetry,
        colorimetry_report=analysis.colorimetry_report,
        includes_products_guide=analysis.includes_products_guide,
        products_guide=analysis.products_guide,
        created_at=analysis.created_at,
        expires_at=analysis.expires_at,
    )


# ---------------------------------------------------------------------------
# Right to Erasure (RGPD Art. 17)
# ---------------------------------------------------------------------------
@router.delete("/{analysis_id}", status_code=200)
async def delete_analysis(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    RGPD Art. 17 — Right to erasure.
    Permanently deletes all analysis data.
    ConsentLog is retained for 5 years (legal obligation, Art. 30).
    """
    analysis = await _get_analysis_or_404(analysis_id, db)

    if analysis.deleted_at:
        return {"message": "El análisis ya había sido eliminado."}

    now = datetime.now(timezone.utc)
    analysis.deleted_at = now
    analysis.report = {}
    analysis.quiz_answers = {}
    analysis.face_shape = "deleted"
    analysis.cranial_proportion = "deleted"
    analysis.phone_hash = None
    analysis.colorimetry_report = None
    analysis.products_guide = None

    logger.info("Analysis %s deleted by user request (RGPD Art. 17)", analysis_id)

    return {
        "message": "Todos los datos del análisis han sido eliminados.",
        "deleted_at": now.isoformat(),
        "note": "El registro de consentimiento se conserva 5 años por obligación legal (RGPD Art. 30).",
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _get_analysis_or_404(analysis_id: str, db: AsyncSession) -> Analysis:
    stmt = select(Analysis).where(Analysis.id == analysis_id)
    analysis = (await db.execute(stmt)).scalar_one_or_none()
    if not analysis:
        raise HTTPException(404, "Análisis no encontrado.")
    return analysis
