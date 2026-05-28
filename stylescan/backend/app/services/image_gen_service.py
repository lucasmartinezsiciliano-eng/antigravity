"""
VISAI — Virtual Try-On Image Generation  (v2 — Masked Inpainting)

Architecture pivot from Nano Banana full-image edit to Flux Pro Fill inpainting.

WHY:
  Nano Banana edits the entire image, so the model must "guess" what to preserve.
  This produces 20-30% identity drift (mandible changes, eyes reinterpreted, etc.)

  Flux Pro Fill + hair mask = the face is MATHEMATICALLY LOCKED.
  Pixels outside the white mask region are copied from the original unchanged.
  The model only generates inside the mask (the hair/scalp cap).
  Identity preservation is exact, not neural-network-dependent.

FLOW PER CUT:
  1. photo_service.extract_hair_mask(frontal_bytes) → binary PNG mask
     WHITE = hair cap (scalp above hairline + sides to ears)
     BLACK = face, background, beard, clothing → never touched
  2. Build inpainting prompt from:
       hair_attrs   → type/color/density/hairline (preserved properties)
       haircut_geometry → target geometry (from DeepSeek structured JSON)
       haircut_detail → visual description from KB or fallback
  3. POST to fal-ai/flux-pro/v1/fill:
       image_url = client frontal photo
       mask_url  = hair mask
       prompt    = target haircut description
  4. Lateral angle: uses profile photo + profile-side mask (right-cap approach)

COST: ~$0.05 per image × 6 images = ~$0.30 per analysis (same ballpark as before).
GDPR: no photo stored. fal.ai processes in-memory. URLs expire in 24h.
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

from sqlalchemy import select

logger = logging.getLogger(__name__)

_IMAGE_PROMPTS_PATH = Path(__file__).parent.parent.parent / "knowledge_base" / "image_prompts.json"

# Primary: Flux Kontext LoRA Inpaint — mask + reference image + prompt in one call
# When a barber reference photo is available, the reference_image_url makes the
# generated hair match a REAL haircut photo instead of relying on text alone.
_KONTEXT_INPAINT_MODEL = "fal-ai/flux-kontext-lora/inpaint"

# Fallback: Flux Pro Fill — masked inpainting (text-only, no reference image)
# Used when NO barber reference photo matches the recommended cut.
_FILL_MODEL = "fal-ai/flux-pro/v1/fill"

# Post-processing: background removal via BiRefNet v2 → white background.
# ~$0.01 per image, ~2-4s. Total added cost: ~$0.06 per analysis (6 images).
_BIREFNET_MODEL = "fal-ai/birefnet/v2"

# Angles: frontal uses the face-cap mask; lateral uses a profile-side mask.
# photo_index: which client photo to use as base
# mask_type:   "frontal_cap" | "profile_right"
_ANGLES = [
    {
        "id": "frontal",
        "label": "Frontal",
        "photo_index": 0,
        "mask_type": "frontal_cap",
        "angle_note": (
            "Frontal view, subject looks directly at camera. "
            "Show the full top of the head: parting, length on top, "
            "any quiff or fringe if present."
        ),
    },
    {
        "id": "lateral",
        "label": "Lateral",
        "photo_index": 1,
        "mask_type": "profile_right",
        "angle_note": (
            "Strict 90-degree left profile. Only the left ear visible. "
            "Show the complete fade or taper graduation on the side, "
            "sideburn, and the hair length on top from this angle."
        ),
    },
]


# ---------------------------------------------------------------------------
# KB haircut descriptions (fallback when DeepSeek geometry is missing)
# ---------------------------------------------------------------------------

def _load_haircut_descriptions() -> dict[str, str]:
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


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Mask generation helpers
# ---------------------------------------------------------------------------

def _build_frontal_mask(photo_bytes: bytes) -> str:
    """Return a base64-encoded PNG mask for a frontal photo (data URI)."""
    from app.services.photo_service import extract_hair_mask
    mask_png = extract_hair_mask(photo_bytes)
    return "data:image/png;base64," + base64.b64encode(mask_png).decode()


def _build_profile_mask(photo_bytes: bytes) -> str:
    """
    Simple geometric mask for a left-profile photo.
    Hair in a profile shot covers the top and back-right of the frame.
    We use a conservative cap: top 50% + right 35%, minus a small face oval
    on the left-centre (where the face appears in profile).
    """
    import cv2
    import numpy as np
    from PIL import Image
    import io as _io

    pil = Image.open(_io.BytesIO(photo_bytes)).convert("RGB")
    w, h = pil.size
    mask = np.zeros((h, w), dtype=np.uint8)

    # Top cap (crown of head)
    mask[:int(h * 0.50), :] = 255
    # Back-of-head strip (right side in a left-profile photo)
    mask[:, int(w * 0.65):] = 255
    # Carve out approximate face area: oval on left-centre
    face_cx, face_cy = int(w * 0.30), int(h * 0.45)
    cv2.ellipse(mask, (face_cx, face_cy), (int(w * 0.18), int(h * 0.28)), 0, 0, 360, 0, -1)
    # Soft edges
    mask = cv2.GaussianBlur(mask, (25, 25), 9)

    buf = _io.BytesIO()
    Image.fromarray(mask, mode="L").save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


# ---------------------------------------------------------------------------
# Barber reference photo lookup
# ---------------------------------------------------------------------------

async def resolve_barber_references(
    cuts: list[dict],
) -> dict[int, dict[str, Optional[str]]]:
    """
    Pre-resolve barber reference photos for each recommended cut.

    Called once during analysis (after LLM returns cuts), NOT during
    image generation. Results are stored in the analysis report so they're
    available instantly when visuals are generated later.

    Returns:
        {
            0: {"frontal": "https://cloudinary/...", "lateral": "https://cloudinary/..."},
            1: {"frontal": None, "lateral": "https://cloudinary/..."},
            2: {"frontal": "https://cloudinary/...", "lateral": None},
        }
    """
    from app.core.database import AsyncSessionLocal
    from app.models.barber_reference_photos import BarberReferencePhoto, PhotoValidationStatus

    result: dict[int, dict[str, Optional[str]]] = {}

    try:
        async with AsyncSessionLocal() as db:
            # Load all active barber reference photos in one query
            stmt = (
                select(BarberReferencePhoto)
                .where(
                    BarberReferencePhoto.is_active == True,
                    BarberReferencePhoto.validation_status.in_([
                        PhotoValidationStatus.APPROVED,
                        PhotoValidationStatus.PENDING,
                    ]),
                )
                .order_by(BarberReferencePhoto.quality_score.desc().nullslast())
            )
            all_photos = (await db.execute(stmt)).scalars().all()

            if not all_photos:
                return {i: {"frontal": None, "lateral": None} for i in range(len(cuts))}

            for i, cut in enumerate(cuts[:3]):
                nombre_en = cut.get("nombre_tecnico") or cut.get("nombre_en", "")
                name_lower = nombre_en.lower().replace("-", " ").replace("_", " ")
                name_tokens = set(name_lower.split())

                refs: dict[str, Optional[str]] = {"frontal": None, "lateral": None}

                for angle_key in ("frontal", "lateral"):
                    best_url = None
                    best_score = 0.0

                    for photo in all_photos:
                        pa = photo.photo_angle
                        pa_value = pa.value if hasattr(pa, 'value') else str(pa)
                        if pa_value != angle_key:
                            continue

                        ht = photo.haircut_type
                        ht_value = ht.value if hasattr(ht, 'value') else str(ht)
                        ht_tokens = set(ht_value.lower().replace("_", " ").split())
                        overlap = len(ht_tokens & name_tokens)
                        score = overlap / max(len(ht_tokens), 1)
                        score += (photo.quality_score or 0.5) * 0.1

                        if score > best_score:
                            best_score = score
                            best_url = photo.cloudinary_url

                    if best_score >= 0.3:
                        refs[angle_key] = best_url

                result[i] = refs
                if refs["frontal"] or refs["lateral"]:
                    logger.info(
                        "  → cut %d '%s' refs: frontal=%s lateral=%s",
                        i, nombre_en[:40],
                        bool(refs["frontal"]), bool(refs["lateral"]),
                    )

    except Exception as e:
        logger.warning("Barber reference resolution failed: %s", e)
        return {i: {"frontal": None, "lateral": None} for i in range(len(cuts))}

    return result


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def _serialize_geometry(geom: dict) -> str:
    """
    Convert a haircut_geometry dict (from DeepSeek) into a compact English
    description that Flux Fill can follow inside the inpainted region.
    """
    parts = []
    side_mm = geom.get("sides_length_mm")
    top_mm  = geom.get("top_length_mm")
    fade    = geom.get("fade_type", "")
    fade_h  = geom.get("fade_start_height", "")
    texture = geom.get("top_texture", "")
    neckline= geom.get("neckline", "")
    parting = geom.get("parting", "none")
    direction = geom.get("top_direction", "")

    if fade:
        fade_desc = f"{fade} fade"
        if fade_h:
            fade_desc += f" starting at {fade_h.replace('_', ' ')}"
        parts.append(fade_desc)
    if side_mm:
        parts.append(f"sides {side_mm}mm length")
    if top_mm:
        parts.append(f"top {top_mm}mm length")
    if texture:
        parts.append(f"{texture} texture on top")
    if direction and direction != "up":
        parts.append(f"swept {direction.replace('_', ' ')}")
    if parting and parting != "none":
        parts.append(f"{parting.replace('_', ' ')} parting")
    if neckline:
        parts.append(f"{neckline} neckline")

    return ", ".join(parts) if parts else ""


def _build_inpaint_prompt(
    nombre_en: str,
    technique: str,
    angle_note: str,
    hair_attrs: Optional[dict] = None,
    haircut_geometry: Optional[dict] = None,
    visual_desc: Optional[str] = None,
    barber_ref_url: Optional[str] = None,
) -> str:
    """
    Build the inpainting prompt.

    TWO MODES:
      WITH reference image (Kontext):
        Keep it SHORT (~120-180 chars). Kontext already conditions heavily on the
        reference image — a long competing prompt fights the visual conditioning
        and produces blurry or incoherent results.

      WITHOUT reference image (Flux Fill, text-only):
        Use the full geometry description so the model has maximum detail
        to work from. This is the fallback when no barber photo matches.
    """
    # Hair properties clause (shared by both modes)
    if hair_attrs:
        h_type    = hair_attrs.get("type",    "natural")
        h_color   = hair_attrs.get("color",   "natural").replace("_", " ")
        h_density = hair_attrs.get("density", "medium")
        prop_clause = f"{h_color} {h_type} hair, {h_density} density. "
    else:
        prop_clause = "Natural hair color and texture. "

    # SHORT prompt when reference image is provided — let the visual do the work.
    # CRITICAL: explicitly instruct the model to preserve the subject's identity
    # and apply ONLY the hair style from the reference. This prevents Kontext from
    # blending the reference person's facial features into the output.
    if barber_ref_url:
        return (
            f"{prop_clause}"
            f"Apply only the {nombre_en} hair style from the reference photo to the masked region. "
            "Preserve the subject's face, skin tone, and all facial features identically — "
            "do NOT alter the face. Only the hair inside the mask changes. "
            f"{angle_note} "
            "Sharp focus, professional barbershop photography."
        )

    # FULL prompt for text-only fallback (no reference image)
    # Priority: structured geometry > free-text > KB > barbershop instructions
    if haircut_geometry and isinstance(haircut_geometry, dict):
        geom_text = _serialize_geometry(haircut_geometry)
    elif visual_desc:
        geom_text = visual_desc
    else:
        geom_text = _lookup_image_desc(nombre_en) or technique[:250]

    return (
        f"{prop_clause}"
        f"Haircut: {nombre_en}. "
        f"{geom_text}. "
        f"{angle_note} "
        "Barbershop professional photography, 50mm portrait lens, "
        "sharp focus on the haircut detail, clean neutral background."
    )


# ---------------------------------------------------------------------------
# Post-processing: white background
# ---------------------------------------------------------------------------

async def _postprocess_white_bg(image_url: str, fal_key: str) -> str:
    """
    Remove background via BiRefNet and composite onto pure white.

    Flow:
      1. fal-ai/birefnet/v2 → transparent PNG (foreground only)
      2. PIL: composite onto white canvas
      3. fal_client.upload → CDN URL (jpeg)

    Cost:  ~$0.01 per image (6 images = ~$0.06 per analysis)
    Time:  ~2-4s per image (runs in parallel with other angles)
    """
    import fal_client  # type: ignore
    import httpx
    from PIL import Image
    import io as _io

    os.environ["FAL_KEY"] = fal_key

    # 1. Foreground segmentation → transparent PNG
    result = await asyncio.to_thread(
        fal_client.run,
        _BIREFNET_MODEL,
        arguments={
            "image_url": image_url,
            "model": "General Use (Heavy)",
            "operating_resolution": "1024x1024",
            "output_format": "png",
        },
    )
    fg_url = result["image"]["url"]

    # 2. Download transparent PNG and composite onto white
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(fg_url)
        resp.raise_for_status()

    fg = Image.open(_io.BytesIO(resp.content)).convert("RGBA")
    white = Image.new("RGBA", fg.size, (255, 255, 255, 255))
    composite = Image.alpha_composite(white, fg)
    final = composite.convert("RGB")

    # 3. Encode and upload to fal CDN
    buf = _io.BytesIO()
    final.save(buf, format="JPEG", quality=92)
    upload_url = await asyncio.to_thread(
        fal_client.upload, buf.getvalue(), "image/jpeg",
    )
    logger.debug("  → white bg: %s → %s", image_url[:60], upload_url[:60])
    return upload_url


# ---------------------------------------------------------------------------
# Single-angle generation
# ---------------------------------------------------------------------------

async def _generate_one_angle(
    photo_b64: str,
    mask_data_uri: str,
    nombre_en: str,
    technique: str,
    angle: dict,
    fal_key: str,
    hair_attrs: Optional[dict] = None,
    haircut_geometry: Optional[dict] = None,
    visual_desc: Optional[str] = None,
    barber_ref_url: Optional[str] = None,
    kontext_strength: float = 0.88,
) -> AngleImage:
    """
    Generate one angle of a haircut try-on image.

    Two modes:
      WITH barber reference → Flux Kontext LoRA Inpaint (mask + reference image)
        The AI sees the REAL haircut from the barber's photo and replicates it
        on the client's head. Face is still locked by the mask.
      WITHOUT barber reference → Flux Pro Fill (mask + text-only)
        Fallback to text-only prompt when no barber reference photo matches.

    Legal note: barber reference photos are never exposed to the client.
    They are processed in-memory by Fal.ai and only the generated output
    (client's face + new hair) is returned.
    """
    from app.core.config import settings
    import fal_client  # type: ignore

    os.environ["FAL_KEY"] = fal_key

    image_data_uri = f"data:image/jpeg;base64,{photo_b64}"

    prompt = _build_inpaint_prompt(
        nombre_en=nombre_en,
        technique=technique,
        angle_note=angle["angle_note"],
        hair_attrs=hair_attrs,
        haircut_geometry=haircut_geometry,
        visual_desc=visual_desc,
        barber_ref_url=barber_ref_url,
    )

    use_kontext = barber_ref_url is not None
    model = _KONTEXT_INPAINT_MODEL if use_kontext else _FILL_MODEL
    model_tag = "kontext-inpaint" if use_kontext else "flux-fill"

    if use_kontext:
        # Kontext LoRA Inpaint: mask + reference image + prompt
        # guidance_scale 3.2 balances reference adherence vs. identity preservation.
        # strength is per-cut (0.93 for high-transform fades, 0.85 for natural cuts).
        arguments = {
            "image_url": image_data_uri,
            "mask_url": mask_data_uri,
            "reference_image_url": barber_ref_url,
            "prompt": prompt,
            "num_inference_steps": 30,
            "guidance_scale": 3.2,
            "strength": kontext_strength,
            "num_images": 1,
            "output_format": "jpeg",
        }
    else:
        # Flux Pro Fill: mask + text-only (no reference image)
        arguments = {
            "image_url": image_data_uri,
            "mask_url": mask_data_uri,
            "prompt": prompt,
            "num_inference_steps": 32,
            "guidance_scale": 4,
            "num_images": 1,
            "output_format": "jpeg",
            "safety_tolerance": "4",
        }

    # Retry loop: up to 3 total attempts with backoff before falling back
    max_retries = 2
    last_error: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(fal_client.run, model, arguments=arguments),
                timeout=90.0,
            )
            url = result["images"][0]["url"]
            logger.info("  → angle %s: OK [%s] ref=%s", angle["id"], model_tag, bool(barber_ref_url))

            # Post-process: remove background → white
            try:
                url = await _postprocess_white_bg(url, fal_key)
                logger.info("  → angle %s: white bg OK", angle["id"])
            except Exception as pp_err:
                logger.warning("  → angle %s: white bg failed, keeping original: %s", angle["id"], pp_err)

            return AngleImage(angle_id=angle["id"], label=angle["label"], url=url)

        except (asyncio.TimeoutError, Exception) as e:
            last_error = e
            if attempt < max_retries:
                delay = 2 if attempt == 0 else 4
                logger.warning(
                    "fal.ai retry %d/%d for %s: %s",
                    attempt + 1, max_retries, angle["id"], e,
                )
                await asyncio.sleep(delay)
            else:
                logger.error("  → angle %s FAILED [%s] after %d attempts: %s", angle["id"], model_tag, attempt + 1, e)

    # All retries exhausted — try Kontext→Fill fallback as last resort
    if use_kontext:
        logger.info("  → retrying angle %s with flux-fill fallback", angle["id"])
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    fal_client.run,
                    _FILL_MODEL,
                    arguments={
                        "image_url": image_data_uri,
                        "mask_url": mask_data_uri,
                        "prompt": prompt,
                        "num_inference_steps": 32,
                        "guidance_scale": 4,
                        "num_images": 1,
                        "output_format": "jpeg",
                        "safety_tolerance": "4",
                    },
                ),
                timeout=90.0,
            )
            url = result["images"][0]["url"]
            logger.info("  → angle %s: OK [flux-fill fallback]", angle["id"])

            # Post-process: remove background → white
            try:
                url = await _postprocess_white_bg(url, fal_key)
                logger.info("  → angle %s: white bg OK [fallback]", angle["id"])
            except Exception as pp_err:
                logger.warning("  → angle %s: white bg failed in fallback: %s", angle["id"], pp_err)

            return AngleImage(angle_id=angle["id"], label=angle["label"], url=url)
        except Exception as e2:
            logger.error("  → angle %s FAILED [flux-fill fallback]: %s", angle["id"], e2)
            return AngleImage(angle_id=angle["id"], label=angle["label"], url="", error=str(e2))
    return AngleImage(angle_id=angle["id"], label=angle["label"], url="", error=str(last_error))


# ---------------------------------------------------------------------------
# Per-cut strength helper
# ---------------------------------------------------------------------------

# Cuts with high structural transformation need a higher denoising strength
# so Kontext commits to the new shape rather than blending with the original.
_HIGH_TRANSFORM_CUTS = {
    "skin fade", "low fade", "mid fade", "high fade", "drop fade", "burst fade",
    "undercut", "mohawk", "buzz cut",
}


def _kontext_strength_for(nombre_en: str) -> float:
    name_lower = nombre_en.lower().replace("-", " ").replace("_", " ")
    for cut in _HIGH_TRANSFORM_CUTS:
        if cut in name_lower:
            return 0.93
    return 0.85


# ---------------------------------------------------------------------------
# Per-cut generation (2 angles in parallel)
# ---------------------------------------------------------------------------

async def _generate_cut(
    photos_bytes: list[bytes],
    photos_b64: list[str],
    cut_index: int,
    nombre_en: str,
    technique: str,
    fal_key: str,
    hair_attrs: Optional[dict] = None,
    haircut_geometry: Optional[dict] = None,
    visual_desc: Optional[str] = None,
    barber_refs: Optional[dict[str, Optional[str]]] = None,
) -> HaircutVisual:
    """
    Generate 2 angle images for one recommended cut.

    barber_refs: Pre-resolved barber reference URLs per angle, e.g.
                 {"frontal": "https://cloudinary/...", "lateral": None}
                 Resolved during analysis, NOT looked up here.
    """
    refs = barber_refs or {}
    strength = _kontext_strength_for(nombre_en)
    logger.info(
        "Generating cut %d: %s (refs: frontal=%s lateral=%s strength=%.2f)",
        cut_index, nombre_en, bool(refs.get("frontal")), bool(refs.get("lateral")), strength,
    )

    # Pre-build masks (CPU work, done before launching async tasks)
    frontal_bytes = photos_bytes[0]
    frontal_b64   = photos_b64[0]
    frontal_mask  = _build_frontal_mask(frontal_bytes)

    if len(photos_bytes) > 1:
        profile_bytes = photos_bytes[1]
        profile_b64   = photos_b64[1]
        profile_mask  = _build_profile_mask(profile_bytes)
    else:
        profile_bytes = frontal_bytes
        profile_b64   = frontal_b64
        profile_mask  = frontal_mask

    angle_tasks = []
    for angle in _ANGLES:
        if angle["mask_type"] == "frontal_cap":
            p64, mask = frontal_b64, frontal_mask
        else:
            p64, mask = profile_b64, profile_mask

        # Map generation angle to barber reference angle (same angle, no cross-fallback):
        #   frontal generation ← frontal reference
        #   lateral generation ← lateral reference
        # NO cross-type fallback: never use a different haircut's reference.
        if angle["id"] == "frontal":
            ref_url = refs.get("frontal")
        else:
            ref_url = refs.get("lateral")

        angle_tasks.append(
            _generate_one_angle(
                photo_b64=p64,
                mask_data_uri=mask,
                nombre_en=nombre_en,
                technique=technique,
                angle=angle,
                fal_key=fal_key,
                hair_attrs=hair_attrs,
                haircut_geometry=haircut_geometry,
                visual_desc=visual_desc,
                barber_ref_url=ref_url,
                kontext_strength=strength,
            )
        )

    angle_images = await asyncio.gather(*angle_tasks, return_exceptions=False)
    return HaircutVisual(
        cut_index=cut_index,
        nombre_en=nombre_en,
        angles=list(angle_images),
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def generate_visuals(
    photos_bytes: list[bytes],
    cuts: list[dict],
    face_shape: str,
    fal_key: str,
    hair_attrs: Optional[dict] = None,
    barber_refs: Optional[dict[int, dict[str, Optional[str]]]] = None,
) -> list[HaircutVisual]:
    """
    Generate 2 angle images (frontal + lateral) for each of the 3 recommended cuts.
    All 6 images are generated in parallel via asyncio.gather.

    barber_refs: Pre-resolved barber reference photos per cut index.
                 Resolved during analysis time via resolve_barber_references().
                 When a reference exists, Kontext LoRA Inpaint is used (mask + reference);
                 otherwise Flux Pro Fill is used (mask + text-only).
    """
    from app.services.trend_service import get_reference_images_for_cut

    photos_b64 = [base64.b64encode(b).decode() for b in photos_bytes]

    # If no pre-resolved refs, try resolving now (backward compat for manual trigger)
    if barber_refs is None:
        try:
            barber_refs = await resolve_barber_references(cuts)
        except Exception:
            barber_refs = {}

    cut_tasks = []
    for i, cut in enumerate(cuts[:3]):
        nombre_en       = cut.get("nombre_tecnico") or cut.get("nombre_en", f"Cut {i+1}")
        technique       = cut.get("como_pedirlo_al_barbero", "")
        haircut_geometry = cut.get("haircut_geometry")
        visual_desc     = cut.get("descripcion_visual_imagen")

        cut_tasks.append(
            _generate_cut(
                photos_bytes=photos_bytes,
                photos_b64=photos_b64,
                cut_index=i,
                nombre_en=nombre_en,
                technique=technique,
                fal_key=fal_key,
                hair_attrs=hair_attrs,
                haircut_geometry=haircut_geometry,
                visual_desc=visual_desc,
                barber_refs=barber_refs.get(i, {}),
            )
        )

    visuals = await asyncio.gather(*cut_tasks, return_exceptions=False)

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
