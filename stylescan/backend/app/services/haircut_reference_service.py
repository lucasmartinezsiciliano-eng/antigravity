"""
StyleScan — Haircut Reference Service

Unified resolver: given any haircut name returned by the LLM (e.g.
"Degradado Bajo con Flequillo Diagonal", "Mid Fade with Textured Top",
"french crop"), returns a usable reference image URL/path that fal.ai
FLUX Kontext Multi can consume alongside the user's photo.

Resolution order (fastest → slowest):
  1. In-memory async cache (process lifetime)
  2. Disk cache (knowledge_base/barber_references/reference_cache.json)
  3. Curated local image (knowledge_base/barber_references/curated/<id>.jpg)
  4. Pexels API search (using haircut_aliases.json query overrides)
  5. None — caller falls back to text-only generation

Matching strategy (LLM cut name → catalog entry):
  - Normalize both sides (lowercase, strip punctuation)
  - Score against canonical_en / canonical_es / aliases
  - Token-overlap scoring: best match wins if score >= 0.5
  - On miss, fall back to generic_terms map for partial hits
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ─── Paths ────────────────────────────────────────────────────────────
KB_DIR = Path(__file__).parent.parent.parent / "knowledge_base"
ALIASES_FILE = KB_DIR / "haircut_aliases.json"
CURATED_DIR = KB_DIR / "barber_references" / "curated"
CACHE_FILE = KB_DIR / "barber_references" / "reference_cache.json"

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"

# ─── Module state ─────────────────────────────────────────────────────
_aliases_data: Optional[dict] = None
_aliases_lock = threading.Lock()
_memory_cache: dict[str, Optional[str]] = {}
_cache_lock = threading.Lock()


# ─── Aliases catalog ─────────────────────────────────────────────────
def _load_aliases() -> dict:
    """Lazy-load haircut_aliases.json (cached for the lifetime of the process)."""
    global _aliases_data
    if _aliases_data is not None:
        return _aliases_data
    with _aliases_lock:
        if _aliases_data is not None:
            return _aliases_data
        try:
            _aliases_data = json.loads(ALIASES_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("haircut_aliases.json load failed: %s — running without curated mapping", e)
            _aliases_data = {"cuts": {}, "generic_terms": {}}
        return _aliases_data


@dataclass
class CutMatch:
    cut_id: str
    score: float
    pexels_query: str
    local_image: Optional[Path]
    canonical_en: str


# Tokens that appear across many cuts and shouldn't drive matching by themselves.
# A score gets weighted: distinctive tokens (skin, mullet, quiff, pompadour…)
# count fully (1.0); generic tokens count as 0.25.
_GENERIC_TOKENS = {
    "men", "man", "male", "with", "and", "the", "haircut", "hair", "cut",
    "style", "hairstyle", "barbershop", "barber", "modern", "classic",
    "natural", "soft", "low", "mid", "high", "short", "long", "medium",
    "top", "side", "back", "para", "con", "de", "el", "la", "los", "las",
}


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", text.lower()).strip()


def _tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"\s+", _normalize(text)) if t and len(t) > 1]


def _token_weight(tok: str) -> float:
    return 0.25 if tok in _GENERIC_TOKENS else 1.0


def _weighted_overlap(query_tokens: list[str], target_tokens: list[str]) -> float:
    """
    Weighted token-overlap of `query_tokens` against `target_tokens`.
    Distinctive tokens (cut-defining words like 'mullet', 'pompadour') count
    far more than fillers like 'men', 'haircut', 'low', 'classic'.
    Returns the fraction of `query_tokens`' total weight covered by hits.
    """
    if not query_tokens:
        return 0.0
    total_weight = sum(_token_weight(t) for t in query_tokens) or 1.0
    target_set = set(target_tokens)
    hit_weight = sum(_token_weight(t) for t in query_tokens if t in target_set)
    return hit_weight / total_weight


def _match_cut(cut_name: str) -> Optional[CutMatch]:
    """
    Find the best catalog match for a free-form LLM cut name.
    Returns None if no entry scores >= 0.6 weighted overlap.
    """
    data = _load_aliases()
    cuts: dict = data.get("cuts", {})
    if not cuts:
        return None

    name_tokens = _tokenize(cut_name)
    if not name_tokens:
        return None

    best: Optional[CutMatch] = None
    best_score = 0.0

    for cut_id, entry in cuts.items():
        candidates = [
            entry.get("canonical_en", ""),
            entry.get("canonical_es", ""),
            *entry.get("aliases", []),
        ]
        for candidate in candidates:
            cand_tokens = _tokenize(candidate)
            if not cand_tokens:
                continue
            # Symmetric weighted score combining both directions:
            #   precision = how much of the LLM name is in the alias
            #   recall    = how much of the alias is in the LLM name
            # We use the harmonic mean (F1). This avoids the failure mode where
            # a short alias like "classic taper" 100%-matches every LLM name
            # that happens to contain those two tokens — both directions must
            # agree for a high score.
            p = _weighted_overlap(name_tokens, cand_tokens)
            r = _weighted_overlap(cand_tokens, name_tokens)
            score = (2 * p * r / (p + r)) if (p + r) > 0 else 0.0
            if score > best_score:
                best_score = score
                local = entry.get("local_image")
                local_path = CURATED_DIR / local if local else None
                best = CutMatch(
                    cut_id=cut_id,
                    score=score,
                    pexels_query=entry.get("pexels_query", f"{candidate} men barbershop"),
                    local_image=local_path,
                    canonical_en=entry.get("canonical_en", cut_id),
                )

    if best and best_score >= 0.5:
        return best
    return None


def _generic_query_fallback(cut_name: str) -> str:
    """When no catalog entry matches well, build a query from generic terms."""
    data = _load_aliases()
    name_lower = cut_name.lower()
    for term, query in data.get("generic_terms", {}).items():
        if term in name_lower:
            return query
    return f"{cut_name} men haircut barbershop"


# ─── Disk cache ──────────────────────────────────────────────────────
def _load_disk_cache() -> dict[str, str]:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_disk_cache(cache: dict[str, str]) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def _cache_key(cut_name: str, match: Optional[CutMatch]) -> str:
    """Use catalog id when matched (stable across LLM phrasings); raw name otherwise."""
    return match.cut_id if match else f"raw::{_normalize(cut_name)}"


# ─── Pexels search ───────────────────────────────────────────────────
def _pexels_search(query: str, api_key: str) -> Optional[str]:
    try:
        resp = httpx.get(
            PEXELS_SEARCH_URL,
            headers={"Authorization": api_key},
            params={"query": query, "per_page": 5, "orientation": "portrait"},
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        photos = data.get("photos", [])
        if not photos:
            return None
        return photos[0]["src"]["large"]
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            logger.warning("Pexels rate limit hit — falling back to text-only")
        else:
            logger.warning("Pexels API error %d for '%s'", e.response.status_code, query)
        return None
    except Exception as e:
        logger.warning("Pexels search failed for '%s': %s", query, e)
        return None


# ─── Public API ──────────────────────────────────────────────────────
def resolve_reference_sync(cut_name: str, pexels_api_key: str) -> Optional[str]:
    """
    Sync resolver — returns a public URL or a `file://` path to a curated image.

    Returns None if no reference can be obtained (caller falls back to text-only).
    """
    if not cut_name:
        return None

    match = _match_cut(cut_name)
    key = _cache_key(cut_name, match)

    # 1. In-memory cache
    with _cache_lock:
        if key in _memory_cache:
            cached = _memory_cache[key]
            return cached if cached else None

    # 2. Curated local image (highest quality — manually selected)
    if match and match.local_image and match.local_image.exists():
        url = match.local_image.resolve().as_uri()  # file:///...
        logger.info("Reference (curated) for '%s' → %s [score=%.2f]", cut_name, match.cut_id, match.score)
        with _cache_lock:
            _memory_cache[key] = url
        return url

    # 3. Disk cache (Pexels results from previous runs)
    disk_cache = _load_disk_cache()
    if key in disk_cache:
        cached = disk_cache[key]
        with _cache_lock:
            _memory_cache[key] = cached or None
        return cached or None

    # 4. Pexels live search
    if not pexels_api_key:
        with _cache_lock:
            _memory_cache[key] = None
        return None

    query = match.pexels_query if match else _generic_query_fallback(cut_name)
    logger.info("Reference (Pexels) lookup for '%s' (key=%s, query=%r)", cut_name, key, query)
    url = _pexels_search(query, pexels_api_key)

    # Persist (negative cache stored as empty string so we don't retry on every request)
    disk_cache[key] = url or ""
    _save_disk_cache(disk_cache)
    with _cache_lock:
        _memory_cache[key] = url or None

    if url:
        logger.info("Reference (Pexels) for '%s' → %s", cut_name, url)
    else:
        logger.info("Reference (Pexels) MISS for '%s' (cached negative)", cut_name)
    return url


async def resolve_reference(cut_name: str, pexels_api_key: str) -> Optional[str]:
    """Async wrapper — runs the (network-bound) sync resolver in the default executor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, resolve_reference_sync, cut_name, pexels_api_key)


async def resolve_many(cut_names: list[str], pexels_api_key: str) -> list[Optional[str]]:
    """Resolve N references in parallel. Used by image_gen_service."""
    if not cut_names:
        return []
    return await asyncio.gather(*[resolve_reference(n, pexels_api_key) for n in cut_names])


def debug_match(cut_name: str) -> dict:
    """Diagnostic helper — returns what would be matched, without doing any I/O."""
    match = _match_cut(cut_name)
    return {
        "input": cut_name,
        "matched": bool(match),
        "cut_id": match.cut_id if match else None,
        "score": match.score if match else 0.0,
        "pexels_query": match.pexels_query if match else _generic_query_fallback(cut_name),
        "has_local_image": bool(match and match.local_image and match.local_image.exists()),
    }
