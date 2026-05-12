"""
StyleScan — Virtual Try-On Image Generation

For each of the 3 recommended cuts, generates 2 images using
fal-ai/nano-banana-pro/edit (Google Nano Banana Pro via fal.ai):

  Angle 0 — Frontal: client's face with new hairstyle (face LOCKED)
  Angle 1 — Lateral: left-profile view showing fade/taper graduation

= 6 images total (3 cuts × 2 angles), all generated in parallel.

Reference strategy (improvement #1 — multi-angle KB):
  Each angle requests a KB reference whose photo_angle matches:
    frontal  → prefers photo_angle="front"
    lateral  → prefers photo_angle="side_left"
  When both client photo + reference are available, the model receives
  [client_photo, reference_photo] via image_urls — no competing face
  as reference because we filter for shots without visible face (is_nuca_shot)
  or use side/front shots from the curated index.

Cost: ~$0.039–$0.15 per edit at 1K resolution via fal.ai.
  At 6 images/analysis × $0.039 = ~$0.23 variable cost per user.

GDPR: uploaded photo is never stored. fal.ai processes in-memory.
Generated image URLs are CDN links valid ~24 h.
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

# Model — Nano Banana Pro Edit on fal.ai
# Accepts image_urls (list): first = client identity anchor, second (optional) = style reference
_MODEL = "fal-ai/nano-banana-pro/edit"

# 2 angles per cut.
# photo_index: which client capture photo to use as identity anchor
# prefer_angle: KB lookup preference — find references shot from this angle
_ANGLES = [
    {
        "id": "frontal",
        "label": "Frontal",
        "photo_index": 0,
        "prefer_angle": "front",
        "instruction_suffix": (
            "Keep the EXACT same frontal camera angle. Subject looks directly at the camera. "
            "Show the full top of the head: length on top, parting, and fringe/quiff/pompadour if present. "
            "Professional barbershop portrait, clean neutral dark background."
        ),
    },
    {
        "id": "lateral",
        "label": "Lateral",
        "photo_index": 1,
        "prefer_angle": "side_left",
        "instruction_suffix": (
            "This is the left profile / side view of the same person. "
            "Show the left side of the head clearly: left temple, ear, and the fade or taper on the side. "
            "The hair length on top, the fade transition, and the sideburn line must all be clearly visible. "
            "Keep all facial features consistent with the input photo. "
            "Professional barbershop portfolio lighting, clean neutral background."
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
    Compares normalized key tokens against the cut name. Returns "" if no match.
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


def _resolve_kb_reference(
    nombre_en: str,
    face_shape: str,
    age_group: Optional[str],
    prefer_angle: Optional[str],
    skin_tone: Optional[str] = None,
) -> Optional[str]:
    """
    Look up a reference image from the barber Instagram KB (SQLite).
    Returns a file:// URL (curated local image) or an Instagram CDN URL,
    or None if nothing useful is found.

    Prefers references whose photo_angle matches prefer_angle and skin_tone matches
    the client's detected skin tone (critical for Nano Banana Pro blending quality).
    """
    try:
        from scripts.barber_instagram_agent import find_references, CURATED_DIR
    except Exception:
        return None

    refs = find_references(
        face_shape=face_shape,
        cut_name=nombre_en,
        limit=5,
        require_image=False,  # also consider CDN-only refs
        age_group=age_group,
        trending_only=False,
        prefer_angle=prefer_angle,
        skin_tone=skin_tone,
    )

    if not refs:
        return None

    # Prefer refs with a local curated file (better quality, always available)
    for ref in refs:
        curated = ref.get("curated_file")
        if curated:
            curated_path = CURATED_DIR / curated
            if curated_path.exists():
                return curated_path.as_uri()  # file:// URI

    # Fall back to image_file in images/
    for ref in refs:
        img_file = ref.get("image_file")
        if img_file:
            from scripts.barber_instagram_agent import IMG_DIR
            img_path = IMG_DIR / img_file
            if img_path.exists():
                return img_path.as_uri()

    # Fall back to Instagram CDN URL (may expire in ~24 h but usable now)
    for ref in refs:
        cdn = ref.get("instagram_cdn_url")
        if cdn and cdn.startswith(("http://", "https://")):
            return cdn

    return None


def _ref_url_to_fal_input(reference_url: str) -> str:
    """
    Normalize a reference URL into something fal.ai can consume.
    - http(s):// → pass through.
    - file://    → read and inline as data URI (base64).
    """
    if reference_url.startswith(("http://", "https://", "data:")):
        return reference_url
    if reference_url.startswith("file://"):
        from urllib.parse import urlparse, unquote
        parsed = urlparse(reference_url)
        local_path = unquote(parsed.path)
        if os.name == "nt" and local_path.startswith("/"):
            local_path = local_path[1:]
        with open(local_path, "rb") as f:
            payload = f.read()
        ext = Path(local_path).suffix.lower().lstrip(".") or "jpeg"
        if ext == "jpg":
            ext = "jpeg"
        return f"data:image/{ext};base64,{base64.b64encode(payload).decode()}"
    return reference_url


def _build_prompt(
    nombre_en: str,
    technique: str,
    angle_suffix: str,
    has_reference: bool,
) -> str:
    """
    Build the edit prompt for Nano Banana Pro.
    When has_reference=True, the model receives [client_photo, reference_photo]
    so we direct it to take hair style from image 2 only.
    When has_reference=False, single photo mode with explicit text description.
    """
    image_desc = _lookup_image_desc(nombre_en)
    haircut_detail = image_desc if image_desc else technique[:300]

    if has_reference:
        prompt = (
            f"HAIR-ONLY EDIT using two reference images. "
            f"Image 1 is the CLIENT — their face, skin tone, eyes, nose, mouth, jaw, beard, "
            f"and all facial features are the IDENTITY ANCHOR and must NOT change at all. "
            f"Image 2 is the HAIRCUT REFERENCE — use ONLY the hair style, length, texture, and fade "
            f"shown in image 2. Do NOT copy any facial features from image 2. "
            f"Apply the {nombre_en} hairstyle from image 2 to the person from image 1, "
            f"keeping the client's face PIXEL-IDENTICAL to image 1. "
            f"Clothing and background must also remain as in image 1. "
            f"Result must look like a professional barbershop portfolio photo. "
            f"{angle_suffix}"
        )
    else:
        prompt = (
            f"HAIR-ONLY EDIT. "
            f"IDENTITY LOCK — do NOT modify under any circumstances: "
            f"the person's face (every feature, wrinkle, pore, shadow), eye shape and color, "
            f"eyebrow shape, nose shape, mouth and lips, chin, jaw line, skin tone, "
            f"facial hair or beard stubble, ears, neck, clothing, and background. "
            f"These elements must remain PIXEL-IDENTICAL to the input image. "
            f"ONLY CHANGE: the hair on top of the head, on the sides, and on the back of the head. "
            f"New hairstyle: {nombre_en}. "
            f"Haircut detail: {haircut_detail}. "
            f"The result must look like a photo taken in a professional barbershop for their portfolio. "
            f"{angle_suffix}"
        )
    return prompt


async def _generate_one_angle(
    photo_b64: str,
    nombre_en: str,
    technique: str,
    angle: dict,
    fal_key: str,
    reference_url: Optional[str] = None,
) -> AngleImage:
    import fal_client  # type: ignore

    os.environ["FAL_KEY"] = fal_key

    client_data_uri = f"data:image/jpeg;base64,{photo_b64}"
    angle_suffix = angle["instruction_suffix"]
    has_ref = reference_url is not None

    # Build image_urls list: client always first, reference second if available
    image_urls = [client_data_uri]
    if has_ref:
        try:
            ref_input = _ref_url_to_fal_input(reference_url)
            image_urls.append(ref_input)
        except Exception as e:
            logger.warning("  → angle %s: reference load failed (%s), using text-only", angle["id"], e)
            has_ref = False
            image_urls = [client_data_uri]

    prompt = _build_prompt(nombre_en, technique, angle_suffix, has_ref)

    try:
        result = await asyncio.to_thread(
            fal_client.run,
            _MODEL,
            arguments={
                "prompt": prompt,
                "image_urls": image_urls,
                "num_images": 1,
                "output_format": "jpeg",
                "resolution": "1K",      # cheapest tier — sufficient for mobile display
                "safety_tolerance": "4",
            },
        )

        url = result["images"][0]["url"]
        ref_mode = "ref+text" if has_ref else "text-only"
        logger.info("  → angle %s: OK [%s]", angle["id"], ref_mode)
        return AngleImage(angle_id=angle["id"], label=angle["label"], url=url)

    except Exception as e:
        logger.error("  → angle %s FAILED: %s", angle["id"], e)
        return AngleImage(angle_id=angle["id"], label=angle["label"], url="", error=str(e))


async def _generate_cut(
    photos_b64: list[str],
    cut_index: int,
    nombre_en: str,
    technique: str,
    fal_key: str,
    face_shape: str = "oval",
    age_group: Optional[str] = None,
    skin_tone: Optional[str] = None,
) -> HaircutVisual:
    """
    Generate 2 angle images for one cut (frontal + lateral).

    Improvement #1 (multi-angle KB):
    Each angle independently resolves its own reference from the KB,
    preferring a photo shot from the matching angle:
      frontal  → prefer_angle="front"
      lateral  → prefer_angle="side_left"

    This means FLUX (now Nano Banana Pro) receives angle-appropriate references
    instead of a generic one — maximizing style consistency across both angles.
    """
    logger.info("Generating cut %d: %s", cut_index, nombre_en)

    angle_tasks = []
    for angle in _ANGLES:
        # Resolve reference for THIS angle's preferred viewpoint
        ref_url = _resolve_kb_reference(
            nombre_en=nombre_en,
            face_shape=face_shape,
            age_group=age_group,
            prefer_angle=angle["prefer_angle"],
            skin_tone=skin_tone,
        )
        if ref_url:
            logger.info(
                "  cut %d angle '%s' — KB reference found (angle_pref=%s)",
                cut_index, angle["id"], angle["prefer_angle"],
            )
        else:
            logger.info(
                "  cut %d angle '%s' — no KB reference, text-only mode",
                cut_index, angle["id"],
            )

        photo_b64 = photos_b64[min(angle["photo_index"], len(photos_b64) - 1)]
        angle_tasks.append(
            _generate_one_angle(photo_b64, nombre_en, technique, angle, fal_key, ref_url)
        )

    angle_images = await asyncio.gather(*angle_tasks, return_exceptions=False)
    return HaircutVisual(
        cut_index=cut_index,
        nombre_en=nombre_en,
        angles=list(angle_images),
    )


async def generate_visuals(
    photos_bytes: list[bytes],
    cuts: list[dict],
    face_shape: str,
    fal_key: str,
    age_group: Optional[str] = None,
    skin_tone: Optional[str] = None,
) -> list[HaircutVisual]:
    """
    Generate 2 angle images (frontal + lateral) for each of the 3 recommended cuts.
    All 6 images generated in parallel via asyncio.gather.

    skin_tone (e.g. "medio", "claro") filters KB references to match the client's
    detected skin tone — critical for Nano Banana Pro blending quality.

    Returns list of HaircutVisual sorted by cut_index.
    """
    from app.services.trend_service import get_reference_images_for_cut

    photos_b64 = [base64.b64encode(b).decode() for b in photos_bytes]

    cut_tasks = []
    for i, cut in enumerate(cuts[:3]):
        nombre_en = cut.get("nombre_tecnico") or cut.get("nombre_en", f"Cut {i+1}")
        technique = cut.get("como_pedirlo_al_barbero", "")
        cut_tasks.append(
            _generate_cut(
                photos_b64=photos_b64,
                cut_index=i,
                nombre_en=nombre_en,
                technique=technique,
                fal_key=fal_key,
                face_shape=face_shape,
                age_group=age_group,
                skin_tone=skin_tone,
            )
        )

    visuals = await asyncio.gather(*cut_tasks, return_exceptions=False)

    # Attach reference search queries for the frontend display
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
