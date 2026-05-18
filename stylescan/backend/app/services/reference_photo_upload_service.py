"""
Reference Photo Upload & Analysis Service

Handles:
1. Upload to Cloudinary
2. MediaPipe analysis to extract haircut parameters
3. Quality scoring and validation

- upload_reference_photo(file_bytes, barber_id, haircut_type, photo_angle)
  → Returns: cloudinary_url, extracted_parameters, quality_score
"""

import logging
import json
from typing import Optional, Dict, Any
import httpx
from fastapi import UploadFile

from app.core.config import settings
from app.services.face_analysis import FaceAnalyzer

logger = logging.getLogger(__name__)


async def upload_reference_photo(
    file: UploadFile,
    barber_id: str,
    haircut_type: str,
    photo_angle: str,
) -> Dict[str, Any]:
    """
    Upload reference photo to Cloudinary and analyze with MediaPipe.

    Returns:
    {
        "cloudinary_url": "https://res.cloudinary.com/...",
        "cloudinary_public_id": "barber_references/...",
        "extracted_parameters": {
            "transition_line_mm": 12,
            "blend_angle_degrees": 45,
            ...
        },
        "face_shape": "oval",
        "cephalic_type": "mesocéfalo",
        "quality_score": 0.95,
    }
    """
    # Read file bytes
    file_bytes = await file.read()

    # Upload to Cloudinary
    cloudinary_public_id = f"barber_references/{barber_id}/{haircut_type}_{photo_angle}"
    cloudinary_url = await _upload_to_cloudinary(
        file_bytes=file_bytes,
        public_id=cloudinary_public_id,
        resource_type="image",
    )

    if not cloudinary_url:
        raise Exception("Cloudinary upload failed")

    # Analyze with MediaPipe
    face_analyzer = FaceAnalyzer()
    try:
        metrics = await face_analyzer.analyze_photos(
            photos=[file_bytes],  # Single reference photo
            photo_angles=[photo_angle],
        )
    except Exception as e:
        logger.error("MediaPipe analysis failed for barber=%s: %s", barber_id, e)
        metrics = None

    extracted_params = None
    face_shape = None
    cephalic_type = None
    quality_score = None

    if metrics:
        # Extract parameters from MediaPipe metrics
        if photo_angle == "frontal":
            face_shape = metrics.face_shape

        if photo_angle == "lateral":
            cephalic_type = metrics.cephalic_type

        # Build parameter dict
        extracted_params = {
            "transition_line_mm": 12,  # Placeholder — would be extracted from MediaPipe
            "blend_angle_degrees": 45,  # Placeholder
            "top_length_mm": 35,  # Placeholder
            "side_length_mm": 5,  # Placeholder
            "volume_percentage": 60,  # Placeholder
            "line_sharpness": "sharp",  # Placeholder
            "weight_distribution": "balanced",  # Placeholder
        }

        # Quality score (0-1) based on MediaPipe confidence
        quality_score = 0.85  # Placeholder

    logger.info(
        "Reference photo analyzed: barber=%s haircut=%s angle=%s quality=%.2f",
        barber_id, haircut_type, photo_angle, quality_score or 0,
    )

    return {
        "cloudinary_url": cloudinary_url,
        "cloudinary_public_id": cloudinary_public_id,
        "extracted_parameters": json.dumps(extracted_params) if extracted_params else None,
        "face_shape": face_shape,
        "cephalic_type": cephalic_type,
        "quality_score": quality_score,
    }


async def _upload_to_cloudinary(
    file_bytes: bytes,
    public_id: str,
    resource_type: str = "image",
) -> Optional[str]:
    """
    Upload file to Cloudinary using unsigned upload (uses UNSIGNED_UPLOAD_PRESET).
    Returns: https://res.cloudinary.com/[cloud]/image/upload/c_fill,w_1920,h_1080/[public_id]
    """
    if not settings.CLOUDINARY_NAME or not settings.CLOUDINARY_UPLOAD_PRESET:
        logger.warning("Cloudinary not configured — skipping upload")
        return None

    try:
        # Prepare upload form
        files = {
            "file": ("photo.jpg", file_bytes, "image/jpeg"),
            "public_id": (None, public_id),
            "upload_preset": (None, settings.CLOUDINARY_UPLOAD_PRESET),
            "overwrite": (None, "true"),
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"https://api.cloudinary.com/v1_1/{settings.CLOUDINARY_NAME}/{resource_type}/upload",
                files=files,
            )

        if resp.status_code != 200:
            logger.error("Cloudinary upload failed: %d %s", resp.status_code, resp.text[:200])
            return None

        data = resp.json()
        url = data.get("secure_url")

        # Enhance URL with transformations
        if url:
            # Add transformations: fill 1920x1080, auto quality
            url = url.replace(
                "/upload/",
                "/upload/c_fill,w_1920,h_1080,q_auto/",
            )

        logger.info("Cloudinary upload succeeded: %s", public_id)
        return url

    except Exception as e:
        logger.error("Cloudinary upload error: %s", e)
        return None


async def validate_reference_photo_quality(
    extracted_parameters: Optional[Dict],
    quality_score: Optional[float],
    photo_angle: str,
) -> tuple[bool, Optional[str]]:
    """
    Validate reference photo quality.

    Returns: (is_valid, rejection_reason)
    """
    if not quality_score:
        return False, "No se pudo extraer parámetros de la foto"

    if quality_score < 0.70:
        return False, "Calidad de foto insuficiente (lighting, angle, or sharpness)"

    if not extracted_parameters:
        return False, "No se detectó el corte correctamente"

    # Additional checks could go here
    return True, None
