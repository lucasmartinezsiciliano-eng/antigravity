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

logger = logging.getLogger(__name__)

_IMAGE_PROMPTS_PATH = Path(__file__).parent.parent.parent / "knowledge_base" / "image_prompts.json"

# Flux Pro Fill — masked inpainting endpoint on fal.ai
_INPAINT_MODEL = "fal-ai/flux-pro/v1/fill"

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
) -> str:
    """
    Build the Flux Fill inpainting prompt.

    With masked inpainting the face is locked at the pixel level, so the
    prompt can focus entirely on WHAT HAIR to generate — no identity
    preservation instructions needed (the mask handles that).

    Priority chain for geometry description:
      1. haircut_geometry dict → serialized (most precise, structured)
      2. visual_desc string   → from DeepSeek free-text field (legacy)
      3. KB lookup by name    → from image_prompts.json
      4. technique[:250]      → barbershop text (last resort)
    """
    # Geometry source
    if haircut_geometry and isinstance(haircut_geometry, dict):
        geom_text = _serialize_geometry(haircut_geometry)
    elif visual_desc:
        geom_text = visual_desc
    else:
        geom_text = _lookup_image_desc(nombre_en) or technique[:250]

    # Hair properties clause (from analysis — keeps color/texture coherent)
    if hair_attrs:
        h_type    = hair_attrs.get("type",    "natural")
        h_color   = hair_attrs.get("color",   "natural").replace("_", " ")
        h_density = hair_attrs.get("density", "medium")
        prop_clause = f"{h_color} {h_type} hair, {h_density} density. "
    else:
        prop_clause = "Natural hair color and texture. "

    prompt = (
        f"{prop_clause}"
        f"Haircut: {nombre_en}. "
        f"{geom_text}. "
        f"{angle_note} "
        "Barbershop professional photography, 50mm portrait lens, "
        "sharp focus on the haircut detail, clean neutral background."
    )
    return prompt


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
) -> AngleImage:
    """
    Call fal-ai/flux-pro/v1/fill for one angle.

    image_url = client photo (data URI)
    mask_url  = hair-region mask (white = inpaint, black = preserve face)
    prompt    = haircut description focused entirely on target style
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
    )

    try:
        result = await asyncio.to_thread(
            fal_client.run,
            _INPAINT_MODEL,
            arguments={
                "image_url": image_data_uri,
                "mask_url": mask_data_uri,
                "prompt": prompt,
                "num_inference_steps": 28,
                "guidance_scale": 10,
                "num_images": 1,
                "output_format": "jpeg",
                "safety_tolerance": "4",
            },
        )
        url = result["images"][0]["url"]
        logger.info("  → angle %s: OK [flux-fill]", angle["id"])
        return AngleImage(angle_id=angle["id"], label=angle["label"], url=url)

    except Exception as e:
        logger.error("  → angle %s FAILED [flux-fill]: %s", angle["id"], e)
        return AngleImage(angle_id=angle["id"], label=angle["label"], url="", error=str(e))


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
) -> HaircutVisual:
    """
    Generate 2 angle images for one recommended cut.

    Frontal: frontal client photo + frontal hair-cap mask → Flux Fill
    Lateral: profile client photo (if provided) + profile-side mask → Flux Fill
    """
    logger.info("Generating cut %d: %s", cut_index, nombre_en)

    # Pre-build masks (CPU work, done before launching async tasks)
    frontal_bytes = photos_bytes[0]
    frontal_b64   = photos_b64[0]
    frontal_mask  = _build_frontal_mask(frontal_bytes)

    if len(photos_bytes) > 1:
        profile_bytes = photos_bytes[1]
        profile_b64   = photos_b64[1]
        profile_mask  = _build_profile_mask(profile_bytes)
    else:
        # No profile photo: reuse frontal photo for the lateral angle
        # Flux will still generate a reasonable lateral from the prompt + mask
        profile_bytes = frontal_bytes
        profile_b64   = frontal_b64
        profile_mask  = frontal_mask

    angle_tasks = []
    for angle in _ANGLES:
        if angle["mask_type"] == "frontal_cap":
            p64, mask = frontal_b64, frontal_mask
        else:
            p64, mask = profile_b64, profile_mask

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
) -> list[HaircutVisual]:
    """
    Generate 2 angle images (frontal + lateral) for each of the 3 recommended cuts.
    All 6 images are generated in parallel via asyncio.gather.

    hair_attrs: {type, color, density, hairline} from DeepSeek analysis.
                Used to anchor hair properties in the inpainting prompt so
                the generated hair matches the client's natural color/texture.

    The hair GEOMETRY per cut comes from:
      cut["haircut_geometry"]          → structured dict (preferred)
      cut["descripcion_visual_imagen"] → free-text English (legacy fallback)
      KB lookup by nombre_en           → image_prompts.json
      cut["como_pedirlo_al_barbero"]   → barbershop text (last resort)
    """
    from app.services.trend_service import get_reference_images_for_cut

    photos_b64 = [base64.b64encode(b).decode() for b in photos_bytes]

    cut_tasks = []
    for i, cut in enumerate(cuts[:3]):
        nombre_en       = cut.get("nombre_tecnico") or cut.get("nombre_en", f"Cut {i+1}")
        technique       = cut.get("como_pedirlo_al_barbero", "")
        haircut_geometry = cut.get("haircut_geometry")           # structured dict (new)
        visual_desc     = cut.get("descripcion_visual_imagen")   # free text (legacy)

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
