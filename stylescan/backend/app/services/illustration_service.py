"""
StyleScan — Illustration Service

Maps (face_shape + cranial_proportion) → archetype → static illustration URLs.

12 realistic archetypes combining face silhouette with cranial volume.
Files live in knowledge_base/haircut_illustrations/ and are served at /illustrations/*.

Naming convention: {archetype}_{cut_id}_{view}.png
  archetype: oval_balanced, oval_elongated, oval_wide,
             round_balanced, round_wide,
             square_balanced, square_wide,
             oblong_balanced, oblong_elongated,
             heart_balanced, diamond_balanced, triangle_balanced
  views: front, side, back

Rare or contradictory combinations (e.g. round_elongated, oblong_wide) are mapped
to the nearest realistic archetype — see _ARCHETYPE_MAP below.

If an illustration file doesn't exist yet (Lucas is still making them), returns None
for that view so the frontend can show a placeholder instead of a broken image.
"""

from pathlib import Path
from typing import Optional

from app.services.haircut_reference_service import get_cut_id

_ILLUST_DIR = Path(__file__).parent.parent.parent / "knowledge_base" / "haircut_illustrations"

_VIEWS = ("front", "side", "back")

# ─── 12 realistic archetypes ─────────────────────────────────────────────────
ARCHETYPES: list[str] = [
    "oval_balanced",
    "oval_elongated",
    "oval_wide",
    "round_balanced",
    "round_wide",
    "square_balanced",
    "square_wide",
    "oblong_balanced",
    "oblong_elongated",
    "heart_balanced",
    "diamond_balanced",
    "triangle_balanced",
]

# (face_shape, cranial_proportion) → archetype_id
# Contradictory or very rare combos map to the nearest realistic archetype.
_ARCHETYPE_MAP: dict[tuple[str, str], str] = {
    # oval — all three proportions exist
    ("oval",     "balanced"):  "oval_balanced",
    ("oval",     "elongated"): "oval_elongated",
    ("oval",     "wide"):      "oval_wide",
    # round — wide is the archetypal "round" head; elongated is extremely rare
    ("round",    "wide"):      "round_wide",
    ("round",    "balanced"):  "round_balanced",
    ("round",    "elongated"): "round_balanced",   # rare → round_balanced
    # square — wide is the strong-jaw variant; elongated contradicts the silhouette
    ("square",   "balanced"):  "square_balanced",
    ("square",   "wide"):      "square_wide",
    ("square",   "elongated"): "square_balanced",  # rare → square_balanced
    # oblong — already long, so elongated is the natural extreme; wide contradicts it
    ("oblong",   "elongated"): "oblong_elongated",
    ("oblong",   "balanced"):  "oblong_balanced",
    ("oblong",   "wide"):      "oblong_balanced",  # contradictory → oblong_balanced
    # heart — proportions don't change the visual enough to warrant separate archetypes
    ("heart",    "balanced"):  "heart_balanced",
    ("heart",    "elongated"): "heart_balanced",
    ("heart",    "wide"):      "heart_balanced",
    # diamond — narrow at top and bottom; proportion variants are subtle
    ("diamond",  "balanced"):  "diamond_balanced",
    ("diamond",  "elongated"): "diamond_balanced",
    ("diamond",  "wide"):      "diamond_balanced",
    # triangle — wide jaw; proportion variants are subtle
    ("triangle", "balanced"):  "triangle_balanced",
    ("triangle", "wide"):      "triangle_balanced",
    ("triangle", "elongated"): "triangle_balanced",
}

_FALLBACK_ARCHETYPE = "oval_balanced"


def get_archetype(face_shape: str, cranial_proportion: str) -> str:
    """Return the archetype id for a face_shape + cranial_proportion combination."""
    key = (face_shape.lower(), cranial_proportion.lower())
    return _ARCHETYPE_MAP.get(key, _FALLBACK_ARCHETYPE)


def get_illustration_urls(face_shape: str, cranial_proportion: str, cut_id: str) -> dict[str, Optional[str]]:
    """
    Return {front, side, back} illustration paths (relative to API root) for
    a specific archetype + catalog cut.

    Returns None per view if the file hasn't been created yet.
    """
    archetype = get_archetype(face_shape, cranial_proportion)
    result: dict[str, Optional[str]] = {}
    for view in _VIEWS:
        filename = f"{archetype}_{cut_id}_{view}.png"
        result[view] = f"/illustrations/{filename}" if (_ILLUST_DIR / filename).exists() else None
    return result


def enrich_cuts_with_illustrations(
    cuts: list[dict],
    face_shape: str,
    cranial_proportion: str,
) -> list[dict]:
    """
    For each cut in cortes_recomendados, add illustration_urls and archetype_id.
    Matches cut name → catalog cut_id using the haircut_reference_service matcher.
    Returns a new list (does not mutate the original).
    """
    archetype = get_archetype(face_shape, cranial_proportion)
    enriched = []
    for cut in cuts:
        cut_copy = dict(cut)
        nombre = cut_copy.get("nombre", "")
        cut_id = get_cut_id(nombre) if nombre else None
        cut_copy["archetype_id"] = archetype
        if cut_id:
            cut_copy["catalog_cut_id"] = cut_id
            cut_copy["illustration_urls"] = get_illustration_urls(face_shape, cranial_proportion, cut_id)
        else:
            cut_copy["catalog_cut_id"] = None
            cut_copy["illustration_urls"] = {"front": None, "side": None, "back": None}
        enriched.append(cut_copy)
    return enriched


def illustrations_ready_for(face_shape: str, cranial_proportion: str) -> bool:
    """True if at least one front illustration exists for this archetype."""
    archetype = get_archetype(face_shape, cranial_proportion)
    return any(_ILLUST_DIR.glob(f"{archetype}_*_front.png"))
