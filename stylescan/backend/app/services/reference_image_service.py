"""
StyleScan — Haircut Reference Image Service

Fetches a real barbershop photo for each haircut style via Pexels API.
The reference image is passed alongside the user's photo to FLUX Kontext Multi,
dramatically improving virtual try-on quality over text-only prompts.

Flow:
  1. Normalize cut name → search query
  2. Check local disk cache (knowledge_base/barber_references/reference_cache.json)
  3. If miss → search Pexels API (free: 200 req/hour, 20K/month)
  4. Return stable CDN URL or None (triggers graceful text-only fallback)

Cache is stored as JSON so it survives restarts and Railway deploys.
"""

import json
import logging
from pathlib import Path
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

KB_DIR = Path(__file__).parent.parent.parent / "knowledge_base"
CACHE_FILE = KB_DIR / "barber_references" / "reference_cache.json"

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"

# Pexels search overrides for cuts with poor generic search results
_QUERY_OVERRIDES: dict[str, str] = {
    "high fade": "high skin fade men barbershop",
    "mid fade": "mid fade men barbershop haircut",
    "low fade": "low fade taper men barbershop",
    "skin fade": "skin fade men barbershop 2024",
    "taper fade": "taper fade men haircut barbershop",
    "undercut": "undercut men haircut barbershop",
    "pompadour": "pompadour men haircut barbershop",
    "quiff": "quiff men haircut barbershop",
    "textured crop": "textured crop men haircut fade",
    "buzz cut": "buzz cut men barbershop",
    "french crop": "french crop fade men barbershop",
    "curtain bangs": "curtain bangs men haircut 2024",
    "mullet": "modern mullet men haircut barbershop",
    "wolf cut": "wolf cut men haircut 2024",
    "slick back": "slick back undercut men barbershop",
}


def _load_cache() -> dict[str, str]:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_cache(cache: dict[str, str]) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def _build_query(cut_name: str) -> str:
    """Build an effective Pexels search query for a haircut style."""
    name_lower = cut_name.lower().strip()
    for key, override in _QUERY_OVERRIDES.items():
        if key in name_lower:
            return override
    return f"{cut_name} men haircut barbershop"


def _fuzzy_cache_lookup(cut_name: str, cache: dict[str, str]) -> Optional[str]:
    """
    Find a cached reference by approximate token overlap on the cut name.
    Returns the URL if a good-enough match is found, else None.
    Covers cases where the LLM names don't exactly match cached keys.
    """
    name_tokens = set(cut_name.lower().split())
    name_tokens.discard("with")
    name_tokens.discard("and")
    name_tokens.discard("the")

    best_score, best_url = 0.0, None
    for key, url in cache.items():
        if not url:
            continue
        key_clean = key.replace("raw::", "")
        key_tokens = set(key_clean.lower().split())
        key_tokens.discard("with")
        key_tokens.discard("and")
        if not key_tokens:
            continue
        overlap = len(name_tokens & key_tokens) / max(len(key_tokens), len(name_tokens))
        if overlap > best_score:
            best_score = overlap
            best_url = url

    if best_score >= 0.5:
        logger.debug("Fuzzy cache hit (score=%.2f) for '%s'", best_score, cut_name)
        return best_url
    return None


def get_reference_image_url(cut_name: str, pexels_api_key: str) -> Optional[str]:
    """
    Returns a direct CDN image URL of a reference haircut photo, or None.
    Caches results to disk so each unique cut is fetched only once.
    Cache is checked FIRST (no API key required for cache hits).
    """
    cache_key = cut_name.lower().strip()
    cache = _load_cache()

    # 1. Exact cache hit (no API key needed)
    if cache_key in cache:
        logger.debug("Reference cache hit: %s", cache_key)
        return cache[cache_key] or None  # empty string means "no result" (don't retry)

    # 2. Try raw:: prefix (cached by haircut_reference_service with no catalog match)
    raw_key = f"raw::{cache_key}"
    if raw_key in cache and cache[raw_key]:
        logger.debug("Reference raw cache hit: %s", raw_key)
        return cache[raw_key]

    # 3. Fuzzy token-overlap match against all cache keys (no API key needed)
    fuzzy_url = _fuzzy_cache_lookup(cut_name, cache)
    if fuzzy_url:
        return fuzzy_url

    # 4. Live Pexels search (requires API key)
    if not pexels_api_key:
        return None

    query = _build_query(cut_name)
    logger.info("Fetching Pexels reference for: %s (query: %s)", cut_name, query)

    try:
        resp = httpx.get(
            PEXELS_SEARCH_URL,
            headers={"Authorization": pexels_api_key},
            params={
                "query": query,
                "per_page": 5,
                "orientation": "portrait",
            },
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        photos = data.get("photos", [])

        if not photos:
            logger.debug("No Pexels results for: %s", query)
            cache[cache_key] = ""  # negative cache — skip on next request
            _save_cache(cache)
            return None

        # Pick the photo with highest resolution as reference
        # Use "large" (1280×960) — good balance of quality vs download speed
        url = photos[0]["src"]["large"]
        logger.info("Reference found for '%s': %s", cut_name, url)

        cache[cache_key] = url
        _save_cache(cache)
        return url

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            logger.warning("Pexels rate limit hit — falling back to text-only generation")
        else:
            logger.warning("Pexels API error %d for '%s'", e.response.status_code, query)
        return None
    except Exception as e:
        logger.warning("Pexels search failed for '%s': %s", query, e)
        return None
