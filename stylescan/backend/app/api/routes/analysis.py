"""
Analysis routes — core user flow.

POST /analysis/initiate      — Create analysis record + return checkout URL
POST /analysis/{id}/photos   — Upload exactly 5 photos for analysis (after payment confirmed)
GET  /analysis/{id}          — Get analysis result
POST /analysis/{id}/consent  — Record RGPD consent (required before photo upload)
DELETE /analysis/{id}        — Right to erasure (Art. 17 RGPD)
"""

import asyncio
import hashlib
import logging
import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.models.analysis import Analysis
from app.models.barber import BarberPartner
from app.models.consent import ConsentLog
from app.services import face_analysis, claude_service, photo_service, stripe_service, image_gen_service, illustration_service
from app.schemas.analysis import (
    AnalysisInitiateRequest,
    AnalysisInitiateResponse,
    ConsentRequest,
    AnalysisResult,
    UpsellRequest,
    UpsellResponse,
)

router = APIRouter(prefix="/analysis", tags=["analysis"])
logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)


# ---------------------------------------------------------------------------
# Initiate analysis + create checkout
# ---------------------------------------------------------------------------
@router.post("/initiate", response_model=AnalysisInitiateResponse, status_code=201)
@limiter.limit("10/hour")
async def initiate_analysis(
    request: Request,
    body: AnalysisInitiateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Step 1: Create an analysis record and return a Stripe checkout URL.
    Payment must be completed before photo upload is allowed.
    """
    # Validate barber code if provided
    barber_partner_id = None
    promo_code_stripe = None

    # Internal test code — skips Stripe, price €0, no DB lookup required
    # Only active when DEV_SKIP_PAYMENT=True (enforced off in production by config validator)
    if settings.DEV_SKIP_PAYMENT and body.barber_code and body.barber_code.upper() == "LUKILUU":
        analysis_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.METRICS_RETENTION_DAYS)
        analysis = Analysis(
            id=analysis_id,
            expires_at=expires_at,
            barber_code_used=body.barber_code,
            quiz_answers=body.quiz_answers or {},
            status="paid",
            paid_at=datetime.now(timezone.utc),
            amount_paid_cents=0,
        )
        db.add(analysis)
        await db.flush()
        logger.info("Test code LUKILUU — analysis %s skipped payment (€0)", analysis_id)
        return AnalysisInitiateResponse(
            analysis_id=analysis_id,
            checkout_url=f"{settings.FRONTEND_URL}/pending?id={analysis_id}",
            amount_euros=0.0,
            discount_applied=True,
        )

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

    # Idempotency: reuse existing pending analysis if created in the last 10 min from the same phone.
    # Frontend stores the Stripe checkout URL in localStorage, so returning the analysis_id is enough.
    if phone_hash:
        cutoff_idem = datetime.now(timezone.utc) - timedelta(minutes=10)
        stmt_idem = select(Analysis).where(
            Analysis.phone_hash == phone_hash,
            Analysis.status == "pending",
            Analysis.created_at >= cutoff_idem,
        ).order_by(Analysis.created_at.desc()).limit(1)
        existing = (await db.execute(stmt_idem)).scalar_one_or_none()
        if existing:
            logger.info("Returning existing pending analysis %s (idempotency)", existing.id)
            return AnalysisInitiateResponse(
                analysis_id=existing.id,
                checkout_url=f"{settings.FRONTEND_URL}/pending?id={existing.id}",
                amount_euros=settings.PRICE_BASE_ANALYSIS / 100,
                discount_applied=False,
            )

    analysis_id = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.METRICS_RETENTION_DAYS)

    # Dev bypass: skip Stripe, mark as paid immediately
    if settings.DEV_SKIP_PAYMENT:
        analysis = Analysis(
            id=analysis_id,
            expires_at=expires_at,
            barber_partner_id=barber_partner_id,
            barber_code_used=body.barber_code,
            phone_hash=phone_hash,
            quiz_answers=body.quiz_answers or {},
            status="paid",
            paid_at=datetime.now(timezone.utc),
            amount_paid_cents=settings.PRICE_BASE_ANALYSIS,
        )
        db.add(analysis)
        await db.flush()
        logger.warning("DEV_SKIP_PAYMENT active — analysis %s marked as paid without Stripe", analysis_id)
        return AnalysisInitiateResponse(
            analysis_id=analysis_id,
            checkout_url=f"{settings.FRONTEND_URL}/pending?id={analysis_id}",
            amount_euros=0.0,
            discount_applied=False,
        )

    analysis = Analysis(
        id=analysis_id,
        expires_at=expires_at,
        barber_partner_id=barber_partner_id,
        barber_code_used=body.barber_code,
        phone_hash=phone_hash,
        quiz_answers=body.quiz_answers or {},
        marketing_consent=body.marketing_consent,
        marketing_consent_at=datetime.now(timezone.utc) if body.marketing_consent else None,
        status="pending",
    )
    db.add(analysis)
    await db.flush()

    # Create Stripe checkout — success/cancel redirect to the frontend, not the backend
    session = stripe_service.create_checkout_session(
        analysis_id=analysis_id,
        success_url=f"{settings.FRONTEND_URL}/pending?id={analysis_id}",
        cancel_url=f"{settings.FRONTEND_URL}/checkout",
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
@limiter.limit("10/hour")
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

    # Idempotent: if consent already recorded, return success without duplicating
    existing = (await db.execute(
        select(ConsentLog).where(ConsentLog.analysis_id == analysis_id)
    )).scalar_one_or_none()
    if existing:
        return {"message": "Consentimiento ya registrado.", "analysis_id": analysis_id}

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
# CRM notification
# ---------------------------------------------------------------------------
async def _notify_crm(analysis: "Analysis", report: dict) -> None:
    """Fire-and-forget: POST analysis data to n8n CRM webhook."""
    import httpx
    n8n_url = getattr(settings, "N8N_CRM_WEBHOOK_URL", "")
    if not n8n_url:
        return
    cortes = [c.get("nombre", "") for c in report.get("cortes_recomendados", [])]
    payload = {
        "email": analysis.user_email or "",
        "analysis_id": analysis.id,
        "cortes": cortes,
        "barber_code": analysis.barber_code or "",
        "importe": float(analysis.amount_paid or 0),
        "marketing_consent": bool(analysis.marketing_consent),
        "result_url": f"https://visaiapp.com/result/{analysis.id}",
        "created_at": analysis.created_at.isoformat() if analysis.created_at else "",
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(n8n_url, json=payload)
    except Exception as exc:
        logger.warning("CRM webhook failed for %s: %s", analysis.id, exc)


# ---------------------------------------------------------------------------
# Photo upload + analysis execution
# ---------------------------------------------------------------------------
async def _auto_generate_visuals(
    analysis_id: str,
    photos_bytes: list[bytes],
    cuts: list[dict],
    face_shape: str,
    hair_attrs: dict | None = None,
):
    """Background task: generate visuals using the matching photo per angle."""
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import select as sa_select

    async with AsyncSessionLocal() as db:
        try:
            visuals = await image_gen_service.generate_visuals(
                photos_bytes=photos_bytes,
                cuts=cuts,
                face_shape=face_shape,
                fal_key=settings.FAL_KEY,
                hair_attrs=hair_attrs,
            )
            visuals_dict = image_gen_service.visuals_to_dict(visuals)
            stmt = sa_select(Analysis).where(Analysis.id == analysis_id)
            analysis = (await db.execute(stmt)).scalar_one_or_none()
            if analysis:
                has_errors = all(v.get("error") for v in visuals_dict)
                analysis.generated_visuals = visuals_dict
                analysis.visuals_status = "failed" if has_errors else "ready"
                await db.commit()
        except Exception as e:
            logger.error("Auto visual generation failed for %s: %s", analysis_id, e)
            stmt = sa_select(Analysis).where(Analysis.id == analysis_id)
            analysis = (await db.execute(stmt)).scalar_one_or_none()
            if analysis:
                analysis.visuals_status = "failed"
                await db.commit()
        finally:
            del photos_bytes


async def _generate_extra_with_retry(fn, label: str, timeout_s: float = 90.0, max_attempts: int = 2):
    """LLM extra generation with timeout + one retry. Returns None if all attempts fail."""
    for attempt in range(1, max_attempts + 1):
        try:
            return await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, fn),
                timeout=timeout_s,
            )
        except asyncio.TimeoutError:
            logger.warning("%s attempt %d/%d timed out after %.0fs", label, attempt, max_attempts, timeout_s)
        except Exception as exc:
            logger.warning("%s attempt %d/%d failed: %s", label, attempt, max_attempts, exc)
    logger.error("%s failed after %d attempts — extra will be missing", label, max_attempts)
    return None


async def _run_analysis_background(
    analysis_id: str,
    valid_photo_bytes: list[bytes],
    photos_for_visuals: list[bytes] | None,
    quiz: dict,
    includes_seasonal: bool,
    includes_colorimetry: bool,
    includes_products_guide: bool,
    user_email: str | None,
) -> None:
    """Run MediaPipe + LLM in background so the HTTP response is immediate."""
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import select as sa_select

    async def _mark_failed(db, reason: str, error_message: str | None = None):
        """Update status to 'failed' so the frontend stops polling on 202."""
        stmt = sa_select(Analysis).where(Analysis.id == analysis_id)
        a = (await db.execute(stmt)).scalar_one_or_none()
        if a and a.status in ("processing", "paid"):
            a.status = "failed"
            # Persist error context inside the JSON report (no schema migration needed)
            existing = dict(a.report or {})
            existing["error"] = {
                "reason": reason,
                "message": (error_message or "")[:500],
            }
            a.report = existing
            await db.commit()

    async with AsyncSessionLocal() as db:
        try:
            # --- MediaPipe face analysis (CPU-bound, run in thread)
            try:
                metrics = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: face_analysis.analyze_photos(valid_photo_bytes)
                )
            finally:
                del valid_photo_bytes

            if not metrics:
                await _mark_failed(db, reason="no_face_detected")
                if photos_for_visuals:
                    del photos_for_visuals
                logger.warning("Background analysis %s: no face detected", analysis_id)
                return

            # --- LLM report generation
            try:
                report = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, lambda: claude_service.generate_report(metrics, quiz, include_seasonal=includes_seasonal)
                    ),
                    timeout=120.0,
                )
            except (asyncio.TimeoutError, Exception) as exc:
                logger.error("Background LLM failed for %s: %s", analysis_id, exc, exc_info=True)
                await _mark_failed(db, reason="llm_failed", error_message=str(exc))
                if photos_for_visuals:
                    del photos_for_visuals
                return

            cuts = report.get("cortes_recomendados", [])

            # --- Optional add-ons
            colorimetry_report = None
            if includes_colorimetry:
                colorimetry_report = await _generate_extra_with_retry(
                    lambda: claude_service.generate_colorimetry_report(metrics, quiz),
                    label=f"colorimetry [{analysis_id}]",
                )

            products_guide = None
            if includes_products_guide:
                products_guide = await _generate_extra_with_retry(
                    lambda: claude_service.generate_products_guide(metrics, quiz, cuts),
                    label=f"products_guide [{analysis_id}]",
                )

            # --- Persist
            stmt = sa_select(Analysis).where(Analysis.id == analysis_id)
            analysis = (await db.execute(stmt)).scalar_one_or_none()
            if not analysis:
                return

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
            analysis.photos_deleted_at = datetime.now(timezone.utc)
            if colorimetry_report:
                analysis.colorimetry_report = colorimetry_report
            if products_guide:
                analysis.products_guide = products_guide
            if photos_for_visuals and cuts:
                analysis.visuals_status = "processing"

            await db.commit()

            logger.info(
                "Background analysis %s completed: shape=%s confidence=%.0f%% photos=%d",
                analysis_id, metrics.face_shape, metrics.confidence * 100, metrics.photos_used,
            )

            # --- Kick off visuals, email, CRM (fire-and-forget)
            # These tasks are not awaited; if the worker dies they are lost.
            # Each wrapper catches every exception so a crash never leaves
            # the analysis dangling in 'processing' / 'processing' visuals.
            if photos_for_visuals and cuts:
                async def _safe_visuals(aid, p, c, fs, ha):
                    try:
                        await _auto_generate_visuals(aid, p, c, fs, ha)
                    except Exception as exc:  # noqa: BLE001
                        logger.error("Fire-and-forget visuals crashed for %s: %s", aid, exc, exc_info=True)
                        # _auto_generate_visuals already flips visuals_status on error,
                        # but if it crashed before reaching that handler we do it here.
                        try:
                            from app.core.database import AsyncSessionLocal
                            from sqlalchemy import select as sa_select
                            async with AsyncSessionLocal() as db2:
                                row = (await db2.execute(sa_select(Analysis).where(Analysis.id == aid))).scalar_one_or_none()
                                if row and row.visuals_status == "processing":
                                    row.visuals_status = "failed"
                                    await db2.commit()
                        except Exception:
                            logger.exception("Failed to mark visuals_status=failed for %s", aid)

                asyncio.create_task(_safe_visuals(
                    analysis_id, photos_for_visuals, cuts,
                    metrics.face_shape, report.get("hair_attributes"),
                ))
            elif photos_for_visuals:
                del photos_for_visuals

            if user_email:
                from app.services.email_service import send_analysis_ready

                async def _safe_email(email, aid):
                    try:
                        await send_analysis_ready(email, aid)
                    except Exception as exc:  # noqa: BLE001
                        logger.error("Fire-and-forget email crashed for %s: %s", aid, exc, exc_info=True)

                asyncio.create_task(_safe_email(user_email, analysis_id))

            async def _safe_crm(a, r):
                try:
                    await _notify_crm(a, r)
                except Exception as exc:  # noqa: BLE001
                    logger.error("Fire-and-forget CRM crashed for %s: %s", a.id, exc, exc_info=True)

            asyncio.create_task(_safe_crm(analysis, report))

        except Exception as exc:
            logger.error("Background analysis crashed for %s: %s", analysis_id, exc, exc_info=True)
            try:
                await _mark_failed(db, reason="background_crashed", error_message=str(exc))
            except Exception:
                pass


@router.post("/{analysis_id}/photos", status_code=202)
@limiter.limit("5/hour")
async def upload_photos_and_analyze(
    request: Request,
    analysis_id: str,
    background_tasks: BackgroundTasks,
    photos: list[UploadFile] = File(..., description="3 fotos del rostro: (1) frontal 0°, (2) perfil izquierdo 90°, (3) perfil derecho 90°"),
    db: AsyncSession = Depends(get_db),
):
    """
    Step 3: Upload photos. Validates immediately, runs face analysis + LLM in background.
    Returns 202 in <1s so Cloudflare never times out. Client polls GET /analysis/{id}.
    """
    analysis = await _get_analysis_or_404(analysis_id, db)

    if analysis.deleted_at:
        raise HTTPException(410, "Este análisis ha sido eliminado.")

    # Reject re-uploads on analyses already in-flight or finished — prevents
    # double-charging Fal.ai + OpenRouter if the user navigates back.
    if analysis.status == "completed":
        logger.info("Rejected re-upload on completed analysis %s", analysis_id)
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Este análisis ya está completado. Mira tus resultados en /result."
        )

    if analysis.status == "processing":
        logger.info("Rejected re-upload on in-progress analysis %s", analysis_id)
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "El análisis ya está en progreso. Espera a que termine."
        )

    # 'failed' is allowed (user may retry). Only 'paid' is the green-light state.
    if analysis.status not in ("paid", "failed"):
        raise HTTPException(
            400,
            "El pago debe completarse antes de subir las fotos. "
            "Completa el pago y vuelve a intentarlo."
        )

    stmt = select(ConsentLog).where(ConsentLog.analysis_id == analysis_id)
    consent_log = (await db.execute(stmt)).scalar_one_or_none()
    if not consent_log:
        raise HTTPException(
            400,
            "Debes aceptar el tratamiento de datos biométricos antes de subir las fotos."
        )

    if len(photos) < 3:
        raise HTTPException(
            400,
            f"Se requieren al menos 3 fotos del rostro (recibidas: {len(photos)}): "
            "frontal, perfil izquierdo y perfil derecho."
        )

    if len(photos) > 5:
        raise HTTPException(400, "Máximo 5 fotos permitidas.")

    # --- Validate photos (fast — in-memory only)
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
        del raw_bytes

    if not valid_photo_bytes:
        errors_str = " | ".join(validation_errors) if validation_errors else "Calidad insuficiente."
        raise HTTPException(
            422,
            f"Ninguna foto pasó la validación. {errors_str} "
            "Intenta con mejor iluminación y la cara bien encuadrada."
        )

    photos_for_visuals: list[bytes] | None = valid_photo_bytes[:2] if settings.FAL_KEY else None

    # Capture analysis attrs before the DB session closes with the response
    quiz = analysis.quiz_answers or {}
    includes_seasonal = analysis.includes_seasonal
    includes_colorimetry = analysis.includes_colorimetry
    includes_products_guide = analysis.includes_products_guide
    user_email = analysis.user_email

    # Mark processing and commit so GET /analysis/{id} returns 202 while background runs
    analysis.status = "processing"
    await db.commit()

    # Heavy work (MediaPipe + LLM) runs after response is sent
    background_tasks.add_task(
        _run_analysis_background,
        analysis_id,
        valid_photo_bytes,
        photos_for_visuals,
        quiz,
        includes_seasonal,
        includes_colorimetry,
        includes_products_guide,
        user_email,
    )

    return {"message": "Fotos recibidas. El análisis está en progreso.", "analysis_id": analysis_id}


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

    # Enrich cuts with illustration URLs (computed at serve time, not stored in DB)
    report = dict(analysis.report or {})
    face_shape = analysis.face_shape or "oval"
    cranial = analysis.cranial_proportion or "balanced"
    cuts = report.get("cortes_recomendados", [])
    if cuts:
        report["cortes_recomendados"] = illustration_service.enrich_cuts_with_illustrations(
            cuts, face_shape, cranial
        )

    return AnalysisResult(
        analysis_id=analysis.id,
        face_shape=analysis.face_shape,
        cranial_proportion=analysis.cranial_proportion,
        asymmetry_score=analysis.asymmetry_score,
        confidence=analysis.analysis_confidence,
        photos_analyzed=analysis.photos_analyzed,
        report=report,
        includes_colorimetry=analysis.includes_colorimetry,
        colorimetry_report=analysis.colorimetry_report,
        includes_products_guide=analysis.includes_products_guide,
        products_guide=analysis.products_guide,
        includes_seasonal=analysis.includes_seasonal or False,
        seasonal_report=analysis.report.get("analisis_temporal") if analysis.includes_seasonal and analysis.report else None,
        created_at=analysis.created_at,
        expires_at=analysis.expires_at,
    )


# ---------------------------------------------------------------------------
# Right to Erasure (RGPD Art. 17)
# ---------------------------------------------------------------------------
@router.delete("/{analysis_id}", status_code=200)
@limiter.limit("20/hour")
async def delete_analysis(
    analysis_id: str,
    request: Request,  # required by slowapi rate limiter
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
    analysis.user_email = None
    analysis.generated_visuals = None
    analysis.colorimetry_report = None
    analysis.products_guide = None

    logger.info("Analysis %s deleted by user request (RGPD Art. 17)", analysis_id)

    return {
        "message": "Todos los datos del análisis han sido eliminados.",
        "deleted_at": now.isoformat(),
        "note": "El registro de consentimiento se conserva 5 años por obligación legal (RGPD Art. 30).",
    }


# ---------------------------------------------------------------------------
# Upsell purchase (post-analysis: colorimetry / products guide)
# ---------------------------------------------------------------------------
@router.post("/{analysis_id}/upsell", response_model=UpsellResponse, status_code=201)
async def create_upsell(
    analysis_id: str,
    body: UpsellRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Step after results: purchase colorimetry or products guide add-on.
    Creates a new Stripe checkout session for the upsell item only.
    """
    if body.upsell_type not in ("colorimetry", "products", "pack", "seasonal"):
        raise HTTPException(400, "upsell_type must be: colorimetry | products | pack | seasonal")

    analysis = await _get_analysis_or_404(analysis_id, db)

    # seasonal OTO is offered pre-capture (status=paid), others require completed
    if body.upsell_type == "seasonal":
        if analysis.status not in ("paid", "processing", "completed"):
            raise HTTPException(400, "Pago no confirmado.")
        if analysis.includes_seasonal:
            raise HTTPException(409, "Ya tienes el análisis de temporada incluido.")
    else:
        if analysis.status != "completed":
            raise HTTPException(400, "El análisis debe estar completado para añadir extras.")
    if analysis.deleted_at:
        raise HTTPException(410, "Este análisis ha sido eliminado.")

    # Check if already purchased (non-seasonal)
    if body.upsell_type != "seasonal":
        already_has = {
            "colorimetry": analysis.includes_colorimetry,
            "products":    analysis.includes_products_guide,
            "pack":        analysis.includes_colorimetry and analysis.includes_products_guide,
        }
        if already_has.get(body.upsell_type):
            raise HTTPException(409, "Ya tienes este extra incluido en tu análisis.")

    price_map = {
        "colorimetry": settings.PRICE_COLORIMETRY,
        "products":    settings.PRICE_PRODUCTS_GUIDE,
        "pack":        settings.PRICE_PACK_COMPLETE,
        "seasonal":    settings.PRICE_SEASONAL,
    }

    if settings.DEV_SKIP_PAYMENT:
        if body.upsell_type == "seasonal":
            analysis.includes_seasonal = True
        else:
            _generate_upsell_content(analysis, body.upsell_type)
        await db.commit()
        success_url = (
            f"{settings.FRONTEND_URL}/capture/{analysis_id}"
            if body.upsell_type == "seasonal"
            else f"{settings.FRONTEND_URL}/result/{analysis_id}"
        )
        return UpsellResponse(
            checkout_url=f"{success_url}?seasonal_added=1",
            analysis_id=analysis_id,
            upsell_type=body.upsell_type,
            amount_euros=price_map[body.upsell_type] / 100,
        )

    success_url = (
        f"{settings.FRONTEND_URL}/capture/{analysis_id}?seasonal_added=1"
        if body.upsell_type == "seasonal"
        else f"{settings.FRONTEND_URL}/result/{analysis_id}"
    )
    cancel_url = (
        f"{settings.FRONTEND_URL}/capture/{analysis_id}"
        if body.upsell_type == "seasonal"
        else f"{settings.FRONTEND_URL}/result/{analysis_id}"
    )

    session = stripe_service.create_upsell_checkout_session(
        analysis_id=analysis_id,
        upsell_type=body.upsell_type,
        success_url=success_url,
        cancel_url=cancel_url,
    )

    return UpsellResponse(
        checkout_url=session.url,
        analysis_id=analysis_id,
        upsell_type=body.upsell_type,
        amount_euros=price_map[body.upsell_type] / 100,
    )


def _generate_upsell_content(analysis, upsell_type: str) -> None:
    """Synchronously generate and attach upsell report content to the analysis object."""
    from app.services.face_analysis import FaceMetrics

    lwr = analysis.length_width_ratio or 1.5
    fwr = analysis.forehead_width_ratio or 1.0
    jwr = analysis.jaw_width_ratio or 0.9
    # Reconstruct approximate raw dimensions from stored ratios (face_width = 1.0 base unit)
    face_width = 1.0
    face_length = lwr
    forehead_width = fwr * face_width
    jaw_width = jwr * face_width

    metrics = FaceMetrics(
        face_shape=analysis.face_shape or "oval",
        cranial_proportion=analysis.cranial_proportion or "balanced",
        face_length=face_length,
        face_width=face_width,
        forehead_width=forehead_width,
        jaw_width=jaw_width,
        length_width_ratio=lwr,
        forehead_to_face_ratio=fwr,
        jaw_to_face_ratio=jwr,
        asymmetry_score=analysis.asymmetry_score or 0.0,
        asymmetry_description="minimal" if (analysis.asymmetry_score or 0) < 0.1 else "notable",
        photos_used=analysis.photos_analyzed or 1,
        confidence=analysis.analysis_confidence or 0.9,
        analysis_notes=[],
    )
    quiz = analysis.quiz_answers or {}
    report = analysis.report or {}
    cuts = report.get("cortes_recomendados", [])

    if upsell_type in ("colorimetry", "pack"):
        try:
            analysis.colorimetry_report = claude_service.generate_colorimetry_report(metrics, quiz)
            analysis.includes_colorimetry = True
        except Exception as e:
            logger.error("Colorimetry generation failed: %s", e)

    if upsell_type in ("products", "pack"):
        try:
            analysis.products_guide = claude_service.generate_products_guide(metrics, quiz, cuts)
            analysis.includes_products_guide = True
        except Exception as e:
            logger.error("Products guide generation failed: %s", e)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _get_analysis_or_404(analysis_id: str, db: AsyncSession) -> Analysis:
    stmt = select(Analysis).where(Analysis.id == analysis_id)
    analysis = (await db.execute(stmt)).scalar_one_or_none()
    if not analysis:
        raise HTTPException(404, "Análisis no encontrado.")
    return analysis


# ---------------------------------------------------------------------------
# Unsubscribe from marketing emails (RGPD Art. 21)
# ---------------------------------------------------------------------------
@router.post("/{analysis_id}/unsubscribe", status_code=200)
async def unsubscribe_marketing(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Revoke marketing consent. Always returns 200 to prevent enumeration."""
    stmt = select(Analysis).where(Analysis.id == analysis_id)
    analysis = (await db.execute(stmt)).scalar_one_or_none()
    if analysis and analysis.marketing_consent:
        analysis.marketing_consent = False
        analysis.marketing_consent_at = None
        await db.commit()
        logger.info("Marketing consent revoked for analysis %s", analysis_id)
    return {"unsubscribed": True}
