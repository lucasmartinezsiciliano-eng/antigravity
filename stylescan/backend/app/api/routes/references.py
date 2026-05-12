"""
References route — Real barber photos matched to client face shape + cut.

GET /analysis/{id}/references
    Returns real Instagram barber photos matching the client's face shape
    and recommended cuts. Requires the barber index to have been built
    by running: python -m scripts.barber_instagram_agent --save-images

Each cut in the response gets up to 5 reference photos showing real clients
with the same face shape who got that cut at a Spanish barbershop.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.analysis import Analysis

router = APIRouter(prefix="/analysis", tags=["references"])
logger = logging.getLogger(__name__)


def _find_refs_for_cut(face_shape: str, cut_name_en: str, limit: int = 5) -> list[dict]:
    """
    Search the barber index for photos matching face_shape + cut.
    Returns list of dicts with image_url, account, post_url, technique.
    """
    try:
        from scripts.barber_instagram_agent import find_references
        refs = find_references(face_shape, cut_name_en, limit=limit, require_image=True)
        # If not enough results, relax the face shape and try again
        if len(refs) < 2:
            refs_any = find_references("any", cut_name_en, limit=limit - len(refs), require_image=True)
            refs = refs + refs_any
    except Exception as e:
        logger.warning("find_references failed: %s", e)
        return []

    results = []
    for ref in refs:
        image_file = ref.get("image_file")
        if image_file:
            image_url = f"/barber-refs/{image_file}"
        else:
            image_url = ref.get("instagram_cdn_url")  # fallback: Railway ephemeral / fresh scrape
        results.append({
            "image_url": image_url,
            "account": ref.get("account", ""),
            "post_url": ref.get("post_url", ""),
            "face_shape": ref.get("face_shape", ""),
            "cut_name_es": ref.get("cut_name_es", ""),
            "why_this_works": ref.get("why_this_works", ""),
            "photo_quality": ref.get("photo_quality", 0),
        })
    return results


@router.get("/{analysis_id}/references")
async def get_references(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Return real barber reference photos per recommended cut,
    matched to the client's face shape.
    """
    stmt = select(Analysis).where(Analysis.id == analysis_id)
    analysis = (await db.execute(stmt)).scalar_one_or_none()
    if not analysis:
        raise HTTPException(404, "Análisis no encontrado.")
    if analysis.deleted_at:
        raise HTTPException(410, "Este análisis ha sido eliminado.")
    if analysis.status != "completed":
        raise HTTPException(400, "El análisis no está completado.")

    face_shape = analysis.face_shape or "oval"
    report = analysis.report or {}
    cuts: list[dict] = report.get("cortes_recomendados", [])

    response_cuts = []
    for cut in cuts[:3]:
        cut_name_en = cut.get("nombre_tecnico") or cut.get("nombre_en", "")
        cut_name_es = cut.get("nombre") or cut.get("nombre_es", "")
        refs = _find_refs_for_cut(face_shape, cut_name_en, limit=5)
        response_cuts.append({
            "cut_name_en": cut_name_en,
            "cut_name_es": cut_name_es,
            "references": refs,
        })

    return {
        "analysis_id": analysis_id,
        "face_shape": face_shape,
        "cuts": response_cuts,
        "total_refs": sum(len(c["references"]) for c in response_cuts),
    }
