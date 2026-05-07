"""
StyleScan — Virtual Try-On Image Generation

For each of the 3 recommended cuts, generates 3 images of the client
from different angles using fal.ai FLUX Kontext:

  Angle 0 — Frontal (vista de frente)
  Angle 1 — 3/4 izquierda (45°, el ángulo más favorecedor)
  Angle 2 — 3/4 derecha (45° al otro lado, muestra el fade lateral)

= 9 images total (3 cuts × 3 angles), all generated in parallel.

When PEXELS_API_KEY is configured:
  Uses fal-ai/flux-pro/kontext/multi — user photo + reference haircut photo.
  The visual reference dramatically improves output quality vs text-only.

When PEXELS_API_KEY is absent:
  Falls back to fal-ai/flux-pro/kontext (single image + text description).

GDPR: uploaded photo is never stored. fal.ai processes in-memory.
Generated image URLs are CDN links valid ~24h.
"""

import asyncio
import base64
import json
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_IMAGE_PROMPTS_PATH = Path(__file__).parent.parent.parent / "knowledge_base" / "image_prompts.json"

# Angle descriptors for FLUX Kontext (calibrated for barbershop editorial quality)
_ANGLES = [
    {
        "id": "frontal",
        "label": "Frontal",
        "instruction_suffix": (
            "Camera angle: straight-on frontal view, subject looking directly at camera. "
            "Passport-style portrait lighting. Clean neutral background."
        ),
    },
    {
        "id": "three_quarter_left",
        "label": "3/4 izquierda",
        "instruction_suffix": (
            "Camera angle: 3/4 profile from the subject's left side, approximately 45 degrees. "
            "Left side of face and temple fade clearly visible. "
            "Professional barbershop editorial angle. Natural side lighting."
        ),
    },
    {
        "id": "three_quarter_right",
        "label": "3/4 derecha",
        "instruction_suffix": (
            "Camera angle: 3/4 profile from the subject's right side, approximately 45 degrees. "
            "Right side fade/taper clearly visible. Shows back hairline and neckline transition. "
            "Warm barbershop lighting."
        ),
    },
]


def _load_haircut_descriptions() -> dict[str, str]:
    """Load image-generation descriptions from the KB. Returns {} on failure."""
    try:
        with open(_IMAGE_PROMPTS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        descs = data.get("text_to_image_prompts", {}).get("haircut_descriptions", {})
        return {k: v for k, v in descs.items() if not k.startswith("_")}
    except Exception as e:
        logger.warning("image_prompts.json load failed: %s", e)
        return {}


_HAIRCUT_DESCRIPTIONS: dict[str, str] = _load_haircut_descriptions()


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _lookup_image_desc(nombre_en: str) -> str:
    """
    Try to find a matching haircut description from image_prompts.json.
    Compares normalized key tokens against the cut name. Returns empty string if no match.
    """
    name_norm = _normalize(nombre_en)
    best_key, best_score = "", 0
    for key in _HAIRCUT_DESCRIPTIONS:
        tokens = [t for t in re.split(r"[^a-z0-9]", key.lower()) if t]
        hits = sum(1 for t in tokens if t in name_norm)
        score = hits / len(tokens) if tokens else 0
        if score > best_score:
            best_score = score
            best_key = key
    if best_score >= 0.5:
        return _HAIRCUT_DESCRIPTIONS[best_key]
    return ""


@dataclass
class AngleImage:
    angle_id: str
    label: str
    url: str
    error: Optional[str] = None


@dataclass
class HaircutVisual:
    cut_index: int
    nombre_en: str
    angles: list[AngleImage] = field(default_factory=list)
    references: list[dict] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def has_any_image(self) -> bool:
        return any(a.url for a in self.angles)


def _load_barber_reference_context(nombre_en: str, face_shape: str) -> str:
    """Pull real barbershop technique insights from the barber Instagram index."""
    try:
        from scripts.barber_instagram_agent import build_reference_context
        return build_reference_context(face_shape, nombre_en)
    except Exception:
        return ""


def _build_instruction_text_only(nombre_en: str, technique: str, angle_suffix: str, face_shape: str = "") -> str:
    """Text-only instruction for fal-ai/flux-pro/kontext (single image)."""
    image_desc = _lookup_image_desc(nombre_en)
    haircut_desc = image_desc if image_desc else technique[:250]
    barber_ctx = _load_barber_reference_context(nombre_en, face_shape) if face_shape else ""

    parts = [
        "Keep the person's face, skin tone, eyes, and facial structure exactly identical.",
        f"Change ONLY the hairstyle to: {nombre_en}.",
        f"Barbershop technique: {haircut_desc}.",
    ]
    if barber_ctx:
        parts.append(barber_ctx)
    parts += [
        "Result must look like a professional barbershop portfolio photo.",
        "Do not change clothing, facial hair, or background.",
        angle_suffix,
    ]
    return " ".join(parts)


def _build_instruction_with_reference(nombre_en: str, angle_suffix: str) -> str:
    """
    Instruction for fal-ai/flux-pro/kontext/multi (user photo + reference photo).
    Shorter: the visual reference replaces the need for verbose text description.
    """
    parts = [
        "Image 1 is the person. Image 2 is a reference haircut photo.",
        f"Apply the {nombre_en} hairstyle shown in image 2 to the person in image 1.",
        "Keep the person's face, skin tone, eyes, facial structure, clothing, and background exactly identical.",
        "Match the hair length, texture, fade level, and styling shown in image 2 precisely.",
        "Result must look like a professional barbershop portfolio photo.",
        angle_suffix,
    ]
    return " ".join(parts)


async def _generate_one_angle(
    photo_b64: str,
    nombre_en: str,
    technique: str,
    angle: dict,
    fal_key: str,
    face_shape: str = "",
    reference_url: Optional[str] = None,
) -> AngleImage:
    import fal_client  # type: ignore

    os.environ["FAL_KEY"] = fal_key  # fal_client reads from env only

    data_uri = f"data:image/jpeg;base64,{photo_b64}"
    angle_suffix = angle["instruction_suffix"]

    try:
        loop = asyncio.get_event_loop()

        if reference_url:
            # FLUX Kontext Multi: user photo + reference haircut image
            instruction = _build_instruction_with_reference(nombre_en, angle_suffix)
            result = await loop.run_in_executor(
                None,
                lambda: fal_client.run(
                    "fal-ai/flux-pro/kontext/multi",
                    arguments={
                        "prompt": instruction,
                        "image_urls": [data_uri, reference_url],
                        "num_images": 1,
                        "guidance_scale": 3.5,
                        "num_inference_steps": 28,
                    },
                ),
            )
        else:
            # Fallback: single image + detailed text description
            instruction = _build_instruction_text_only(nombre_en, technique, angle_suffix, face_shape)
            result = await loop.run_in_executor(
                None,
                lambda: fal_client.run(
                    "fal-ai/flux-pro/kontext",
                    arguments={
                        "prompt": instruction,
                        "image_url": data_uri,
                        "num_images": 1,
                        "guidance_scale": 3.5,
                        "num_inference_steps": 28,
                    },
                ),
            )

        url = result["images"][0]["url"]
        logger.info("  → angle %s: OK (ref=%s)", angle["id"], "visual" if reference_url else "text")
        return AngleImage(angle_id=angle["id"], label=angle["label"], url=url)
    except Exception as e:
        logger.error("  → angle %s FAILED: %s", angle["id"], e)
        return AngleImage(angle_id=angle["id"], label=angle["label"], url="", error=str(e))


async def _generate_cut(
    photo_b64: str,
    cut_index: int,
    nombre_en: str,
    technique: str,
    fal_key: str,
    face_shape: str = "",
    reference_url: Optional[str] = None,
) -> HaircutVisual:
    """Generate all 3 angle images for one cut, in parallel."""
    mode = "multi+visual" if reference_url else "single+text"
    logger.info("Generating cut %d: %s (3 angles, mode=%s)", cut_index, nombre_en, mode)
    angle_tasks = [
        _generate_one_angle(photo_b64, nombre_en, technique, angle, fal_key, face_shape, reference_url)
        for angle in _ANGLES
    ]
    angle_images = await asyncio.gather(*angle_tasks, return_exceptions=False)
    return HaircutVisual(
        cut_index=cut_index,
        nombre_en=nombre_en,
        angles=list(angle_images),
    )


async def generate_visuals(
    photo_bytes: bytes,
    cuts: list[dict],
    face_shape: str,
    fal_key: str,
) -> list[HaircutVisual]:
    """
    Generate 3 angle images for each of the 3 recommended cuts.
    All 9 images generated in parallel via asyncio.gather.

    When PEXELS_API_KEY is set, fetches a reference image per cut and uses
    fal-ai/flux-pro/kontext/multi for dramatically better results.

    Returns list of HaircutVisual sorted by cut_index.
    """
    from app.services.trend_service import get_reference_images_for_cut
    from app.services.reference_image_service import get_reference_image_url
    from app.core.config import settings

    photo_b64 = base64.b64encode(photo_bytes).decode()

    # Fetch reference images per cut (up to 3, in parallel)
    ref_tasks = []
    cut_names = []
    for i, cut in enumerate(cuts[:3]):
        nombre_en = cut.get("nombre_tecnico") or cut.get("nombre_en", f"Cut {i+1}")
        cut_names.append(nombre_en)
        ref_tasks.append(
            asyncio.get_event_loop().run_in_executor(
                None,
                lambda n=nombre_en: get_reference_image_url(n, settings.PEXELS_API_KEY),
            )
        )

    reference_urls: list[Optional[str]] = await asyncio.gather(*ref_tasks, return_exceptions=False)
    for i, ref_url in enumerate(reference_urls):
        if ref_url:
            logger.info("Cut %d '%s' — visual reference found", i, cut_names[i])
        else:
            logger.info("Cut %d '%s' — no reference, using text-only", i, cut_names[i])

    cut_tasks = []
    for i, cut in enumerate(cuts[:3]):
        nombre_en = cut_names[i]
        technique = cut.get("como_pedirlo_al_barbero", "")
        cut_tasks.append(
            _generate_cut(
                photo_b64, i, nombre_en, technique, fal_key, face_shape,
                reference_url=reference_urls[i],
            )
        )

    visuals = await asyncio.gather(*cut_tasks, return_exceptions=False)

    # Attach reference search queries for the frontend
    for visual in visuals:
        if isinstance(visual, HaircutVisual):
            visual.references = get_reference_images_for_cut(
                visual.nombre_en, face_shape, limit=3
            )

    return sorted(
        [v for v in visuals if isinstance(v, HaircutVisual)],
        key=lambda v: v.cut_index,
    )


def visuals_to_dict(visuals: list[HaircutVisual]) -> list[dict]:
    """Serialize to JSON-safe dict for DB storage and API response."""
    return [
        {
            "cut_index": v.cut_index,
            "nombre_en": v.nombre_en,
            "angles": [
                {"angle_id": a.angle_id, "label": a.label, "url": a.url, "error": a.error}
                for a in v.angles
            ],
            "references": v.references,
            "error": v.error,
            "has_any_image": v.has_any_image,
        }
        for v in visuals
    ]
