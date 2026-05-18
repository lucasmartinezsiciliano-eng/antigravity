"""
Visuals route — Virtual try-on image generation.

POST /analysis/{id}/generate-visuals
    Accepts a fresh photo from the user (not stored — used only for image gen).
    Triggers async generation of 3 virtual try-on images (one per recommended cut).
    Returns immediately with visuals_status="processing".

GET  /analysis/{id}/visuals
    Poll for generation status.
    Returns visuals_status + generated image URLs when ready.
"""

import logging
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.models.analysis import Analysis
from app.services import photo_service, image_gen_service

router = APIRouter(prefix="/analysis", tags=["visuals"])
logger = logging.getLogger(__name__)


async def _run_generation(
    analysis_id: str,
    photos_bytes: list[bytes],
    cuts: list[dict],
    face_shape: str,
    hair_attrs: dict | None = None,
):
    """Background task: generate images and update DB."""
    from app.core.database import AsyncSessionLocal

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

            stmt = select(Analysis).where(Analysis.id == analysis_id)
            analysis = (await db.execute(stmt)).scalar_one_or_none()
            if analysis:
                has_errors = all(v.get("error") for v in visuals_dict)
                analysis.generated_visuals = visuals_dict
                analysis.visuals_status = "failed" if has_errors else "ready"
                await db.commit()
                logger.info("Visuals %s for analysis %s", analysis.visuals_status, analysis_id)
        except Exception as e:
            logger.error("Visual generation background task failed: %s", e)
            stmt = select(Analysis).where(Analysis.id == analysis_id)
            analysis = (await db.execute(stmt)).scalar_one_or_none()
            if analysis:
                analysis.visuals_status = "failed"
                await db.commit()
        finally:
            del photos_bytes


@router.post("/{analysis_id}/generate-visuals", status_code=202)
async def generate_visuals(
    analysis_id: str,
    background_tasks: BackgroundTasks,
    photo: UploadFile = File(..., description="Foto frontal del usuario"),
    profile_photo: UploadFile = File(None, description="Foto de perfil izquierdo (opcional — mejora el ángulo lateral)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger virtual try-on generation.
    - photo: frontal (required) → used for the frontal angle image
    - profile_photo: left profile from capture (optional) → used for the lateral angle image
      If absent, FLUX generates the lateral from the frontal with a text instruction.
    Photos are never stored. Returns immediately — poll /visuals.
    """
    if not settings.FAL_KEY:
        raise HTTPException(503, "Servicio de visualización no configurado.")

    stmt = select(Analysis).where(Analysis.id == analysis_id)
    analysis = (await db.execute(stmt)).scalar_one_or_none()
    if not analysis:
        raise HTTPException(404, "Análisis no encontrado.")
    if analysis.status != "completed":
        raise HTTPException(400, "El análisis debe estar completado para generar visualizaciones.")
    if analysis.deleted_at:
        raise HTTPException(410, "Este análisis ha sido eliminado.")
    if analysis.visuals_status == "processing":
        raise HTTPException(409, "Generación ya en progreso. Espera o consulta /visuals.")

    # Validate + prepare frontal
    raw = await photo.read()
    val_result, prepared_frontal = photo_service.validate_and_prepare_photo(
        raw, photo.filename or "photo.jpg"
    )
    del raw
    if not val_result.valid or not prepared_frontal:
        raise HTTPException(422, f"Foto frontal no válida: {val_result.error}")

    # Validate + prepare profile (optional)
    photos_bytes = [prepared_frontal]
    if profile_photo:
        raw_p = await profile_photo.read()
        val_p, prepared_profile = photo_service.validate_and_prepare_photo(
            raw_p, profile_photo.filename or "profile.jpg"
        )
        del raw_p
        if val_p.valid and prepared_profile:
            photos_bytes.append(prepared_profile)
            logger.info("Profile photo accepted — lateral angle will use real profile shot")
        else:
            logger.info("Profile photo invalid (%s) — lateral will use text-only", val_p.error)

    # Extract cuts from the stored report
    report = analysis.report or {}
    cuts = report.get("cortes_recomendados", [])
    if not cuts:
        raise HTTPException(400, "No hay cortes recomendados en el informe.")

    face_shape = analysis.face_shape or "oval"
    hair_attrs = report.get("hair_attributes")

    # Mark as processing
    analysis.visuals_status = "processing"
    await db.commit()

    background_tasks.add_task(_run_generation, analysis_id, photos_bytes, cuts, face_shape, hair_attrs)

    return {
        "message": "Generación iniciada. Consulta GET /analysis/{id}/visuals en ~30 segundos.",
        "analysis_id": analysis_id,
        "visuals_status": "processing",
        "has_profile_photo": len(photos_bytes) == 2,
    }


@router.get("/{analysis_id}/visuals")
async def get_visuals(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Poll for visual generation status and retrieve image URLs."""
    stmt = select(Analysis).where(Analysis.id == analysis_id)
    analysis = (await db.execute(stmt)).scalar_one_or_none()
    if not analysis:
        raise HTTPException(404, "Análisis no encontrado.")
    if analysis.deleted_at:
        raise HTTPException(410, "Este análisis ha sido eliminado.")

    status = analysis.visuals_status
    if status is None:
        return {"visuals_status": "not_started", "visuals": []}
    if status == "processing":
        return {"visuals_status": "processing", "visuals": []}
    if status == "failed":
        return {"visuals_status": "failed", "visuals": analysis.generated_visuals or []}

    # Ready
    return {
        "visuals_status": "ready",
        "visuals": analysis.generated_visuals or [],
    }
