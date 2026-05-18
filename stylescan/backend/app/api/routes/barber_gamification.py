"""
Barber gamification features:
- Reference photo upload & validation
- Leaderboard ranking
- Parental consent for minors
- Telegram notifications integration

GET  /leaderboard               — Get top 50 barbers (all-time)
GET  /leaderboard/weekly        — Top 50 for this week
GET  /leaderboard/stats/{id}    — Individual barber stats

POST /barbers/{id}/reference-photos      — Upload reference photo
GET  /barbers/{id}/reference-photos      — List barber's reference photos
GET  /barbers/{id}/reference-photos/{id} — Get photo details
DELETE /barbers/{id}/reference-photos/{id} — Delete photo

POST /parental-consent/request      — Send consent request to parent
GET  /parental-consent/authorize    — Parent authorization link (email token)
GET  /parental-consent/{token}/status — Check token status

POST /telegram/webhook              — Telegram bot webhook
POST /barbers/{id}/telegram/connect — Connect Telegram account
PUT  /barbers/{id}/telegram/preferences — Update notification prefs
"""

import logging
import uuid
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, ConfigDict, EmailStr

from app.core.config import settings
from app.core.database import get_db
from app.models import (
    BarberPartner,
    BarberReferencePhoto,
    HaircutType,
    PhotoAngle,
    PhotoValidationStatus,
    BarberLeaderboardStats as LeaderboardStatsORM,
    ParentalConsentRequest,
    ConsentStatus,
    BarberTelegramAccount,
)

router = APIRouter(prefix="", tags=["gamification"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================

class ReferencePhotoUploadRequest(BaseModel):
    haircut_type: HaircutType
    photo_angle: PhotoAngle


class ReferencePhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    haircut_type: str
    photo_angle: str
    cloudinary_url: str
    validation_status: str
    quality_score: Optional[float]
    created_at: str


class LeaderboardEntry(BaseModel):
    rank: int
    barber_id: str
    barber_name: str
    barbershop_name: str
    city: str
    clients_this_period: int
    clients_all_time: int
    current_tier: str
    instagram_handle: Optional[str]


class BarberLeaderboardStats(BaseModel):
    barber_id: str
    name: str
    city: str
    clients_all_time: int
    clients_this_week: int
    clients_this_month: int
    all_time_ranking_position: Optional[int]
    week_ranking_position: Optional[int]
    current_tier: str
    reference_photos_count: int
    reference_photos_validated: int


class ParentalConsentRequestSchema(BaseModel):
    analysis_id: str
    child_age: int
    parent_email: EmailStr


class ParentalConsentResponse(BaseModel):
    request_id: str
    status: str
    token_expires_at: str
    authorization_url: str


class TelegramConnectRequest(BaseModel):
    telegram_user_id: int
    telegram_chat_id: int
    telegram_username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class TelegramPreferencesRequest(BaseModel):
    notifications_enabled: bool = True
    notify_on_new_analysis: bool = True
    notify_on_ranking_change: bool = True
    notify_on_weekly_summary: bool = True
    language_code: str = "es"


# =============================================================================
# LEADERBOARD
# =============================================================================

@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard(
    period: str = Query("all_time", pattern="^(week|month|all_time)$"),
    city_filter: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Get leaderboard of top barbers by client usage count.
    Period: 'week' (this week), 'month' (this month), 'all_time'.
    Returns rank, barber info, client count, tier.
    """
    # Select appropriate ranking column
    _PERIOD_RANK_COL = {
        "week": LeaderboardStatsORM.week_ranking_position,
        "month": LeaderboardStatsORM.month_ranking_position,
        "all_time": LeaderboardStatsORM.all_time_ranking_position,
    }
    _PERIOD_CLIENT_FIELD = {
        "week": "clients_this_week",
        "month": "clients_this_month",
        "all_time": "clients_all_time",
    }
    rank_col = _PERIOD_RANK_COL[period]

    # Join with BarberPartner to get names
    stmt = (
        select(
            LeaderboardStatsORM,
            BarberPartner.name,
            BarberPartner.barbershop_name,
            BarberPartner.city,
            BarberPartner.instagram_handle,
        )
        .join(BarberPartner, LeaderboardStatsORM.barber_partner_id == BarberPartner.id)
        .where(BarberPartner.is_active == True)
    )

    # Optional city filter
    if city_filter:
        stmt = stmt.where(func.lower(BarberPartner.city) == func.lower(city_filter))

    # Order by rank column (null last)
    stmt = stmt.order_by(rank_col.nulls_last()).limit(limit).offset(offset)

    results = (await db.execute(stmt)).fetchall()

    leaderboard = []
    for rank, (stats, name, barbershop, city, insta) in enumerate(results, start=offset + 1):
        period_clients = getattr(stats, _PERIOD_CLIENT_FIELD[period])
        leaderboard.append(
            LeaderboardEntry(
                rank=rank,
                barber_id=stats.barber_partner_id,
                barber_name=name,
                barbershop_name=barbershop,
                city=city,
                clients_this_period=period_clients,
                clients_all_time=stats.clients_all_time,
                current_tier=stats.current_tier,
                instagram_handle=insta,
            )
        )

    return leaderboard


@router.get("/leaderboard/stats/{barber_id}", response_model=BarberLeaderboardStats)
async def get_barber_leaderboard_stats(
    barber_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get detailed leaderboard stats for a specific barber."""
    partner = await _get_barber_or_404(barber_id, db)

    # Get leaderboard stats
    stmt = select(LeaderboardStatsORM).where(
        LeaderboardStatsORM.barber_partner_id == barber_id
    )
    stats = (await db.execute(stmt)).scalar_one_or_none()
    if not stats:
        raise HTTPException(404, "Stats de ranking no encontrados.")

    # Count reference photos
    stmt_photos = select(func.count(BarberReferencePhoto.id)).where(
        BarberReferencePhoto.barber_partner_id == barber_id,
        BarberReferencePhoto.is_active == True,
    )
    photo_count = (await db.execute(stmt_photos)).scalar() or 0

    stmt_validated = select(func.count(BarberReferencePhoto.id)).where(
        BarberReferencePhoto.barber_partner_id == barber_id,
        BarberReferencePhoto.is_active == True,
        BarberReferencePhoto.validation_status == PhotoValidationStatus.APPROVED,
    )
    validated_count = (await db.execute(stmt_validated)).scalar() or 0

    return BarberLeaderboardStats(
        barber_id=partner.id,
        name=partner.name,
        city=partner.city,
        clients_all_time=stats.clients_all_time,
        clients_this_week=stats.clients_this_week,
        clients_this_month=stats.clients_this_month,
        all_time_ranking_position=stats.all_time_ranking_position,
        week_ranking_position=stats.week_ranking_position,
        current_tier=stats.current_tier,
        reference_photos_count=photo_count,
        reference_photos_validated=validated_count,
    )


# =============================================================================
# REFERENCE PHOTOS
# =============================================================================

@router.post("/barbers/{barber_id}/reference-photos", response_model=dict)
async def upload_reference_photo(
    barber_id: str,
    haircut_type: HaircutType = Query(...),
    photo_angle: PhotoAngle = Query(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a reference photo (frontal or lateral) for a haircut type.
    File is uploaded to Cloudinary and analyzed with MediaPipe.
    Photo validation is manual (Week 1-2) then automatic (>80% confidence).
    """
    await _get_barber_or_404(barber_id, db)

    # Check photo hasn't already been uploaded for this combo
    stmt = select(BarberReferencePhoto).where(
        and_(
            BarberReferencePhoto.barber_partner_id == barber_id,
            BarberReferencePhoto.haircut_type == haircut_type,
            BarberReferencePhoto.photo_angle == photo_angle,
            BarberReferencePhoto.is_active == True,
        )
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            400,
            f"Ya existe una foto {photo_angle} para el corte {haircut_type}. Reemplázala o elimina la anterior.",
        )

    # Validate file
    if file.size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(400, "Foto demasiado grande (máx 10MB).")

    # Upload to Cloudinary and analyze with MediaPipe
    from app.services.reference_photo_upload_service import upload_reference_photo as svc_upload

    try:
        upload_result = await svc_upload(
            file=file,
            barber_id=barber_id,
            haircut_type=haircut_type.value,
            photo_angle=photo_angle.value,
        )
    except Exception as e:
        logger.error("Reference photo upload failed: %s", e)
        raise HTTPException(500, "Error al subir la foto. Intenta de nuevo.")

    photo_id = str(uuid.uuid4())

    photo = BarberReferencePhoto(
        id=photo_id,
        barber_partner_id=barber_id,
        haircut_type=haircut_type.value,
        photo_angle=photo_angle.value,
        cloudinary_url=upload_result["cloudinary_url"],
        cloudinary_public_id=upload_result["cloudinary_public_id"],
        extracted_parameters=upload_result.get("extracted_parameters"),
        face_shape_in_photo=upload_result.get("face_shape"),
        cephalic_type_in_photo=upload_result.get("cephalic_type"),
        quality_score=upload_result.get("quality_score"),
        validation_status=PhotoValidationStatus.PENDING,
    )
    db.add(photo)
    await db.flush()

    logger.info(
        "Reference photo uploaded: barber=%s haircut=%s angle=%s photo_id=%s quality=%.2f",
        barber_id, haircut_type, photo_angle, photo_id,
        upload_result.get("quality_score") or 0,
    )

    return {
        "photo_id": photo_id,
        "status": "pending_validation",
        "quality_score": upload_result.get("quality_score"),
        "message": "Foto subida. Será validada en las próximas 24h.",
    }


@router.get("/barbers/{barber_id}/reference-photos", response_model=list[ReferencePhotoResponse])
async def list_barber_reference_photos(
    barber_id: str,
    haircut_type: Optional[HaircutType] = None,
    validation_status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List reference photos uploaded by a barber."""
    await _get_barber_or_404(barber_id, db)

    stmt = select(BarberReferencePhoto).where(
        BarberReferencePhoto.barber_partner_id == barber_id,
        BarberReferencePhoto.is_active == True,
    )

    if haircut_type:
        stmt = stmt.where(BarberReferencePhoto.haircut_type == haircut_type.value)

    if validation_status:
        stmt = stmt.where(BarberReferencePhoto.validation_status == validation_status)

    stmt = stmt.order_by(BarberReferencePhoto.created_at.desc())
    photos = (await db.execute(stmt)).scalars().all()

    return [
        ReferencePhotoResponse(
            id=p.id,
            haircut_type=p.haircut_type,
            photo_angle=p.photo_angle,
            cloudinary_url=p.cloudinary_url,
            validation_status=p.validation_status,
            quality_score=p.quality_score,
            created_at=p.created_at.isoformat(),
        )
        for p in photos
    ]


@router.delete("/barbers/{barber_id}/reference-photos/{photo_id}")
async def delete_reference_photo(
    barber_id: str,
    photo_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a reference photo (set is_active=False)."""
    await _get_barber_or_404(barber_id, db)

    stmt = select(BarberReferencePhoto).where(
        and_(
            BarberReferencePhoto.id == photo_id,
            BarberReferencePhoto.barber_partner_id == barber_id,
        )
    )
    photo = (await db.execute(stmt)).scalar_one_or_none()
    if not photo:
        raise HTTPException(404, "Foto no encontrada.")

    photo.is_active = False
    await db.flush()

    logger.info("Reference photo deleted: barber=%s photo=%s", barber_id, photo_id)

    return {"message": "Foto eliminada."}


# =============================================================================
# PARENTAL CONSENT
# =============================================================================

@router.post("/parental-consent/request", response_model=ParentalConsentResponse)
async def request_parental_consent(
    body: ParentalConsentRequestSchema,
    db: AsyncSession = Depends(get_db),
):
    """
    Send parental consent request email to parent.
    Parent clicks link with token to authorize child's analysis.
    Token expires in 72 hours.
    """
    # Validate child age (should be detected by analysis, but allow override)
    if body.child_age < 12 or body.child_age >= 18:
        raise HTTPException(
            400,
            "Consentimiento parental solo requerido para menores 12-17 años.",
        )

    # Create consent request
    request_id = str(uuid.uuid4())
    auth_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=72)

    consent_req = ParentalConsentRequest(
        id=request_id,
        analysis_id=body.analysis_id,
        child_age=body.child_age,
        parent_email=body.parent_email,
        authorization_token=auth_token,
        token_expires_at=expires_at,
        consent_status=ConsentStatus.PENDING,
        email_sent_at=datetime.now(timezone.utc),
    )
    db.add(consent_req)
    await db.flush()

    # Send email via Resend with authorization link
    from app.services.parental_consent_service import send_parental_consent_email

    await send_parental_consent_email(
        parent_email=body.parent_email,
        child_age=body.child_age,
        authorization_token=auth_token,
        expires_at_iso=expires_at.isoformat(),
    )

    auth_url = f"{settings.FRONTEND_URL}/parental-consent/authorize?token={auth_token}"

    logger.info(
        "Parental consent request created: request_id=%s parent_email=%s child_age=%d expires_in_72h",
        request_id, body.parent_email, body.child_age,
    )

    return ParentalConsentResponse(
        request_id=request_id,
        status="pending",
        token_expires_at=expires_at.isoformat(),
        authorization_url=auth_url,
    )


@router.get("/parental-consent/authorize")
async def authorize_parental_consent(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Parent authorization endpoint (clicked from email link).
    Verifies token, updates consent status, marks email_clicked_at.
    Returns HTML confirmation page.
    """
    stmt = select(ParentalConsentRequest).where(
        ParentalConsentRequest.authorization_token == token
    )
    consent_req = (await db.execute(stmt)).scalar_one_or_none()
    if not consent_req:
        raise HTTPException(404, "Token no válido o expirado.")

    # Check expiry
    if datetime.now(timezone.utc) > consent_req.token_expires_at:
        consent_req.consent_status = ConsentStatus.EXPIRED
        await db.flush()
        raise HTTPException(
            400,
            "Token expirado. Por favor, solicita un nuevo enlace de autorización.",
        )

    # Mark as authorized
    consent_req.consent_status = ConsentStatus.AUTHORIZED
    consent_req.is_authorized = True
    consent_req.authorized_at = datetime.now(timezone.utc)
    consent_req.email_clicked_at = datetime.now(timezone.utc)
    await db.flush()

    logger.info(
        "Parental consent authorized: request_id=%s parent_email=%s",
        consent_req.id, consent_req.parent_email,
    )

    # Return HTML confirmation
    return {
        "status": "authorized",
        "message": "¡Gracias! El análisis facial de tu hijo ha sido autorizado.",
        "request_id": consent_req.id,
    }


@router.get("/parental-consent/{token}/status")
async def get_parental_consent_status(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Check authorization status of a parental consent request."""
    stmt = select(ParentalConsentRequest).where(
        ParentalConsentRequest.authorization_token == token
    )
    consent_req = (await db.execute(stmt)).scalar_one_or_none()
    if not consent_req:
        raise HTTPException(404, "Token no encontrado.")

    return {
        "request_id": consent_req.id,
        "status": consent_req.consent_status,
        "is_authorized": consent_req.is_authorized,
        "token_expires_at": consent_req.token_expires_at.isoformat(),
    }


# =============================================================================
# TELEGRAM INTEGRATION
# =============================================================================

@router.post("/barbers/{barber_id}/telegram/connect")
async def connect_telegram(
    barber_id: str,
    body: TelegramConnectRequest,
    db: AsyncSession = Depends(get_db),
):
    """Connect barber's Telegram account for notifications."""
    await _get_barber_or_404(barber_id, db)

    # Check if already connected
    stmt = select(BarberTelegramAccount).where(
        BarberTelegramAccount.barber_partner_id == barber_id
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(400, "Ya tienes una cuenta Telegram conectada.")

    telegram_acc = BarberTelegramAccount(
        id=str(uuid.uuid4()),
        barber_partner_id=barber_id,
        telegram_user_id=body.telegram_user_id,
        telegram_chat_id=body.telegram_chat_id,
        telegram_username=body.telegram_username,
        first_name=body.first_name,
        last_name=body.last_name,
        is_connected=True,
    )
    db.add(telegram_acc)
    await db.flush()

    logger.info(
        "Telegram account connected: barber=%s telegram_user_id=%d",
        barber_id, body.telegram_user_id,
    )

    return {
        "status": "connected",
        "message": f"¡Hola {body.first_name}! Recibirás notificaciones en tiempo real sobre tus análisis.",
    }


@router.put("/barbers/{barber_id}/telegram/preferences")
async def update_telegram_preferences(
    barber_id: str,
    body: TelegramPreferencesRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update Telegram notification preferences."""
    await _get_barber_or_404(barber_id, db)

    stmt = select(BarberTelegramAccount).where(
        BarberTelegramAccount.barber_partner_id == barber_id
    )
    telegram_acc = (await db.execute(stmt)).scalar_one_or_none()
    if not telegram_acc:
        raise HTTPException(404, "Cuenta Telegram no conectada.")

    telegram_acc.notifications_enabled = body.notifications_enabled
    telegram_acc.notify_on_new_analysis = body.notify_on_new_analysis
    telegram_acc.notify_on_ranking_change = body.notify_on_ranking_change
    telegram_acc.notify_on_weekly_summary = body.notify_on_weekly_summary
    telegram_acc.language_code = body.language_code
    await db.flush()

    logger.info(
        "Telegram preferences updated: barber=%s notifications_enabled=%s",
        barber_id, body.notifications_enabled,
    )

    return {"status": "updated", "message": "Preferencias actualizadas."}


@router.post("/telegram/webhook")
async def telegram_webhook(body: dict):
    """
    Telegram bot webhook handler.
    Handles: /start, /help, /status commands, and inline buttons.
    """
    from app.services.telegram_service import parse_webhook

    result = await parse_webhook(body)
    return result or {"ok": True}


# =============================================================================
# HELPERS
# =============================================================================

async def _get_barber_or_404(barber_id: str, db: AsyncSession) -> BarberPartner:
    stmt = select(BarberPartner).where(BarberPartner.id == barber_id)
    partner = (await db.execute(stmt)).scalar_one_or_none()
    if not partner:
        raise HTTPException(404, "Barbero no encontrado.")
    return partner
