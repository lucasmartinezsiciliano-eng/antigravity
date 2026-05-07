"""
StyleScan — Autonomous Trend Research Agent

Runs weekly (via trend_worker.py or APScheduler) to discover trending
men's haircut styles from the internet. Uses DuckDuckGo image+text search
plus Claude to classify and score each trend.

Results are stored in:
  knowledge_base/trending/{YYYY-MM}.json  — full monthly snapshot
  knowledge_base/trending_index.json      — current index (read by kb_service)

Flow per run:
  1. For each face shape, run 2-3 targeted search queries
  2. Collect top results (title, URL, thumbnail)
  3. Claude classifies each batch: nombre_en, tags, trend_score, why_trending
  4. Persist to trending index
  5. Also search global trending (not shape-specific) for overall trends
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import anthropic
import httpx

logger = logging.getLogger(__name__)

KB_DIR = Path(__file__).parent.parent.parent / "knowledge_base"
TRENDING_DIR = KB_DIR / "trending"

FACE_SHAPES = ["oval", "round", "square", "oblong", "heart", "diamond", "triangle"]

# Search queries per face shape — designed to hit TikTok, Pinterest, Reddit
_SHAPE_QUERIES: dict[str, list[str]] = {
    "oval": [
        "men haircut oval face 2025 trending",
        "best men hairstyle oval face modern",
    ],
    "round": [
        "men haircut round face slim 2025 trending",
        "fade haircut round face men tiktok",
    ],
    "square": [
        "men haircut square jaw 2025 trending",
        "square face men taper fade trending",
    ],
    "oblong": [
        "men haircut long face 2025 trending",
        "oblong face men hairstyle fringe modern",
    ],
    "heart": [
        "men haircut heart face 2025 trending",
        "narrow chin men haircut balance",
    ],
    "diamond": [
        "men haircut diamond face 2025 trending",
        "diamond face men style narrow forehead",
    ],
    "triangle": [
        "men haircut wide jaw 2025 trending",
        "triangle face men volume top haircut",
    ],
}

_GLOBAL_QUERIES = [
    "men haircut trending 2025 tiktok viral",
    "men hairstyle trend 2025 barbershop",
    "top men haircuts 2025 pinterest",
    "men mullet wolf cut trending 2025",
    "men curtain bang haircut 2025",
]

_CLASSIFY_PROMPT = """Eres un experto en tendencias de cortes de pelo masculino.
Analiza los siguientes resultados de búsqueda y extrae los cortes de pelo que aparecen,
clasificándolos en el siguiente formato JSON.

Resultados de búsqueda:
{results_text}

Forma facial objetivo: {face_shape} (o "global" si no es específica)

Devuelve SOLO un array JSON con este formato (máximo 6 entradas, sin duplicados):
[
  {{
    "nombre_en": "Mid Fade with Textured Top",
    "nombre_es": "Degradado Medio con Textura",
    "tags": ["fade", "mid", "textured", "modern"],
    "trend_score": 0.88,
    "trend_context": "Muy visto en TikTok barbershop 2025, especialmente en cara redonda",
    "why_trending": "El contraste fade + textura desordenada da look moderno sin mucho mantenimiento",
    "reference_search": "mid fade textured top men 2025"
  }}
]

Solo incluye cortes que aparecen claramente en los resultados. Trend score 0.0-1.0 según frecuencia de aparición."""


def _ddg_text_search(query: str, max_results: int = 10) -> list[dict]:
    """DuckDuckGo text search via their unofficial search endpoint."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return [{"title": r.get("title", ""), "body": r.get("body", ""), "href": r.get("href", "")} for r in results]
    except ImportError:
        logger.warning("duckduckgo-search not installed — using httpx fallback")
        return _ddg_html_fallback(query, max_results)
    except Exception as e:
        logger.error("DDG search failed for '%s': %s", query, e)
        return []


def _ddg_html_fallback(query: str, max_results: int = 10) -> list[dict]:
    """Fallback: scrape DuckDuckGo HTML search."""
    try:
        url = "https://html.duckduckgo.com/html/"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; StyleScan/1.0)"}
        resp = httpx.post(url, data={"q": query}, headers=headers, timeout=15)
        resp.raise_for_status()
        # Basic extraction — titles and snippets from HTML
        import re
        titles = re.findall(r'class="result__title"[^>]*>.*?<a[^>]*>([^<]+)</a>', resp.text)
        snippets = re.findall(r'class="result__snippet"[^>]*>([^<]+)', resp.text)
        results = []
        for title, body in zip(titles[:max_results], snippets[:max_results]):
            results.append({"title": title.strip(), "body": body.strip(), "href": ""})
        return results
    except Exception as e:
        logger.error("DDG HTML fallback failed: %s", e)
        return []


def _classify_with_claude(
    results: list[dict],
    face_shape: str,
    client: anthropic.Anthropic,
) -> list[dict]:
    """Claude classifies search results into structured trend entries."""
    if not results:
        return []

    results_text = "\n".join(
        f"- {r['title']}: {r['body'][:200]}" for r in results if r.get("title")
    )

    prompt = _CLASSIFY_PROMPT.format(
        results_text=results_text[:3000],
        face_shape=face_shape,
    )

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        # Strip markdown fences
        import re
        raw = re.sub(r"^```(?:json)?\s*", "", raw).strip()
        raw = re.sub(r"\s*```$", "", raw).strip()
        return json.loads(raw)
    except Exception as e:
        logger.error("Claude classification failed: %s", e)
        return []


def _merge_dedup(existing: list[dict], new_items: list[dict]) -> list[dict]:
    """Merge new trends into existing list, deduplicating by nombre_en."""
    existing_names = {t.get("nombre_en", "").lower() for t in existing}
    merged = list(existing)
    for item in new_items:
        name = item.get("nombre_en", "").lower()
        if name and name not in existing_names:
            merged.append(item)
            existing_names.add(name)
    # Sort by trend_score descending
    merged.sort(key=lambda t: t.get("trend_score", 0), reverse=True)
    return merged[:15]  # Cap at 15 per shape


def run_trend_research(anthropic_api_key: str) -> dict:
    """
    Main entry point. Research all face shapes + global trends.
    Returns the updated trending index dict.
    """
    TRENDING_DIR.mkdir(parents=True, exist_ok=True)
    client = anthropic.Anthropic(api_key=anthropic_api_key)

    month = datetime.now().strftime("%Y-%m")
    month_file = TRENDING_DIR / f"{month}.json"
    index_file = KB_DIR / "trending_index.json"

    # Load or init monthly snapshot
    if month_file.exists():
        with open(month_file, "r", encoding="utf-8") as f:
            monthly_data: dict = json.load(f)
    else:
        monthly_data = {"month": month, "by_face_shape": {s: [] for s in FACE_SHAPES}, "global_trends": []}

    logger.info("Starting trend research for %s", month)

    # ── Per-shape research ──────────────────────────────────────────────
    for shape in FACE_SHAPES:
        logger.info("Researching trends for: %s", shape)
        shape_results: list[dict] = []

        for query in _SHAPE_QUERIES.get(shape, []):
            results = _ddg_text_search(query, max_results=8)
            shape_results.extend(results)
            time.sleep(1.5)  # Polite delay

        if shape_results:
            classified = _classify_with_claude(shape_results, shape, client)
            current = monthly_data["by_face_shape"].get(shape, [])
            monthly_data["by_face_shape"][shape] = _merge_dedup(current, classified)
            logger.info("  → %d trends for %s", len(monthly_data["by_face_shape"][shape]), shape)

        time.sleep(2)

    # ── Global trends ──────────────────────────────────────────────────
    logger.info("Researching global trends")
    global_results: list[dict] = []
    for query in _GLOBAL_QUERIES:
        results = _ddg_text_search(query, max_results=8)
        global_results.extend(results)
        time.sleep(1.5)

    if global_results:
        classified = _classify_with_claude(global_results, "global", client)
        current_global = monthly_data.get("global_trends", [])
        monthly_data["global_trends"] = _merge_dedup(current_global, classified)
        logger.info("  → %d global trends", len(monthly_data["global_trends"]))

    # ── Persist monthly snapshot ───────────────────────────────────────
    with open(month_file, "w", encoding="utf-8") as f:
        json.dump(monthly_data, f, ensure_ascii=False, indent=2)

    # ── Update trending index (read by kb_service at analysis time) ────
    # Load existing index to preserve structure
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            index: dict = json.load(f)
    else:
        index = {"by_face_shape": {s: [] for s in FACE_SHAPES}, "global_trends": []}

    index["last_updated"] = datetime.now().isoformat()
    index["month"] = month
    index["note"] = "Auto-updated by trend_worker.py"

    for shape in FACE_SHAPES:
        index["by_face_shape"][shape] = monthly_data["by_face_shape"].get(shape, [])[:6]

    index["global_trends"] = monthly_data.get("global_trends", [])[:8]

    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    logger.info("Trend research complete. Index updated.")
    return index


def get_reference_images_for_cut(cut_nombre_en: str, face_shape: str, limit: int = 3) -> list[dict]:
    """
    Returns reference image search metadata for a given haircut style.
    These are search query terms + source hints, not actual image URLs
    (to avoid storage/GDPR issues with downloaded images).

    The mobile app uses these to show Pinterest/Google Image search deeplinks.
    """
    index_file = KB_DIR / "trending_index.json"
    shape_file = KB_DIR / f"{face_shape}.json"

    references = []
    cut_lower = cut_nombre_en.lower()

    # Check KB for matching cut
    shape_data = None
    try:
        with open(shape_file, "r", encoding="utf-8") as f:
            shape_data = json.load(f)
    except Exception:
        pass

    if shape_data:
        for cut in shape_data.get("cuts", []):
            if cut_lower in cut.get("nombre_en", "").lower():
                references.append({
                    "search_query": cut.get("search_query", cut["nombre_en"]),
                    "source": "knowledge_base",
                    "nombre_en": cut["nombre_en"],
                    "technique_hint": cut.get("technique", ""),
                })
                break

    # Check trending index
    try:
        with open(index_file, "r", encoding="utf-8") as f:
            index = json.load(f)
        for t in index.get("by_face_shape", {}).get(face_shape, []):
            if cut_lower in t.get("nombre_en", "").lower():
                references.append({
                    "search_query": t.get("reference_search", t["nombre_en"]),
                    "source": "trending",
                    "nombre_en": t["nombre_en"],
                    "trend_context": t.get("trend_context", ""),
                })
    except Exception:
        pass

    # Always include a generic search query as fallback
    if not references:
        references.append({
            "search_query": f"{cut_nombre_en} men haircut 2025",
            "source": "fallback",
            "nombre_en": cut_nombre_en,
            "technique_hint": "",
        })

    # Add additional search variants
    base_query = cut_nombre_en.lower().replace(" ", "+")
    references.append({
        "search_query": f"{cut_nombre_en} men barbershop tutorial",
        "source": "tutorial",
        "nombre_en": cut_nombre_en,
        "technique_hint": "",
    })

    return references[:limit]
