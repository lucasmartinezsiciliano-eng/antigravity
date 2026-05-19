"""
LLM-powered weekly trend analyzer for VISAI.

Reads `knowledge_base/trend_data.json`, asks the LLM (OpenRouter / DeepSeek)
for a Spanish weekly brief + a list of new haircut candidates not yet in
`knowledge_base/haircut_aliases.json`, and writes the result to
`knowledge_base/trend_brief.json`. Any new cuts detected are auto-added
to `haircut_aliases.json` with `auto_added=true`.

Run:
    python -m scripts.trend_analyzer
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT          = Path(__file__).parent.parent
KB_DIR        = ROOT / "knowledge_base"
ENV_PATH      = ROOT / ".env"
TREND_PATH    = KB_DIR / "trend_data.json"
ALIASES_PATH  = KB_DIR / "haircut_aliases.json"
BRIEF_PATH    = KB_DIR / "trend_brief.json"

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("trend_analyzer")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL          = "deepseek/deepseek-chat-v3-0324"


def _read_dotenv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip().strip('"').strip("'")
    except Exception as e:
        logger.warning("Could not read .env: %s", e)
    return out


def _load_aliases() -> dict:
    if not ALIASES_PATH.exists():
        return {"cuts": {}, "generic_terms": {}}
    try:
        data = json.loads(ALIASES_PATH.read_text(encoding="utf-8"))
        if "cuts" not in data:
            data["cuts"] = {}
        return data
    except Exception as e:
        logger.warning("haircut_aliases.json unreadable (%s) — using empty", e)
        return {"cuts": {}, "generic_terms": {}}


def _known_cut_keys(aliases: dict) -> set[str]:
    keys: set[str] = set()
    for cut_id, cut in (aliases.get("cuts") or {}).items():
        keys.add(cut_id.lower())
        for field in ("canonical_es", "canonical_en"):
            v = cut.get(field)
            if isinstance(v, str):
                keys.add(v.lower())
        for alias in cut.get("aliases", []) or []:
            if isinstance(alias, str):
                keys.add(alias.lower())
    return keys


def _build_prompt(trend: dict, known_keys: set[str]) -> str:
    mentions = trend.get("haircut_mentions", {}) or {}
    trending_up = trend.get("trending_up", []) or []
    week = trend.get("week", "")
    known_sample = ", ".join(sorted(known_keys)[:50]) if known_keys else "(catálogo vacío)"

    return f"""Eres un experto en tendencias de barbería masculina en España. Te paso
los datos de esta semana ({week}) extraídos de Instagram.

Conteo de menciones por corte esta semana:
{json.dumps(mentions, ensure_ascii=False, indent=2)}

Cortes que están subiendo respecto a la semana pasada:
{json.dumps(trending_up, ensure_ascii=False)}

Cortes ya en nuestro catálogo (no los marques como nuevos):
{known_sample}

Devuelve EXACTAMENTE este JSON, sin comentarios, sin markdown:
{{
  "weekly_brief": "2-3 frases en español, tono editorial breve, sobre qué se está llevando esta semana en barberías españolas",
  "top_5_cuts": ["nombre en español", "..."],
  "new_cuts_detected": ["nombres en inglés o español que NO están en el catálogo"],
  "catalog_suggestions": [
    {{
      "id": "slug_minusculas_con_guiones_bajos",
      "canonical_es": "Nombre en español",
      "canonical_en": "English name",
      "aliases": ["variant 1", "variant 2"]
    }}
  ]
}}

Reglas:
- Si no detectas cortes nuevos, devuelve listas vacías para new_cuts_detected y catalog_suggestions.
- top_5_cuts ordenado por relevancia esta semana (no por menciones totales si la subida es relevante).
- canonical_es en español castellano de barbería (ej: "Corte Edgar", "Degradado a Piel").
""".strip()


def _call_llm(prompt: str, api_key: str) -> Optional[str]:
    try:
        resp = httpx.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error("OpenRouter call failed: %s", e)
        return None


def _parse_json(raw: str) -> Optional[dict]:
    """Strip markdown fences and parse JSON."""
    if not raw:
        return None
    s = raw.strip()
    # Strip ```json fences
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?", "", s, count=1).strip()
        if s.endswith("```"):
            s = s[:-3].strip()
    # Sometimes the model returns text before the JSON
    m = re.search(r"\{[\s\S]*\}", s)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception as e:
        logger.error("JSON parse failed: %s — raw: %.300s", e, s)
        return None


def _slugify(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")[:40]


def _merge_new_cuts(aliases: dict, suggestions: list[dict]) -> int:
    """Append auto-detected cuts to the catalog. Returns count added."""
    if not suggestions:
        return 0
    cuts = aliases.setdefault("cuts", {})
    added = 0
    now = datetime.now(timezone.utc).isoformat()
    for s in suggestions:
        if not isinstance(s, dict):
            continue
        cid = s.get("id") or _slugify(s.get("canonical_en") or s.get("canonical_es") or "")
        if not cid or cid in cuts:
            continue
        cuts[cid] = {
            "canonical_es": s.get("canonical_es", ""),
            "canonical_en": s.get("canonical_en", ""),
            "aliases":      s.get("aliases", []) or [],
            "auto_added":   True,
            "added_at":     now,
        }
        added += 1
    return added


def main() -> int:
    if not TREND_PATH.exists():
        logger.warning("trend_data.json missing — run trend_scraper first. Exiting.")
        return 0

    try:
        trend = json.loads(TREND_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error("Could not read trend_data.json: %s", e)
        return 0

    env = _read_dotenv(ENV_PATH)
    api_key = (
        env.get("OPENROUTER_API_KEY")
        or os.environ.get("OPENROUTER_API_KEY", "")
    ).strip()
    if not api_key:
        logger.warning("OPENROUTER_API_KEY not set — cannot run analyzer. Exiting.")
        return 0

    aliases = _load_aliases()
    known   = _known_cut_keys(aliases)
    prompt  = _build_prompt(trend, known)

    raw = _call_llm(prompt, api_key)
    parsed = _parse_json(raw) if raw else None
    if not parsed:
        logger.error("LLM returned no parseable JSON — aborting (no file written)")
        return 0

    brief = {
        "generated_at":         datetime.now(timezone.utc).isoformat(),
        "week":                 trend.get("week", ""),
        "weekly_brief":         parsed.get("weekly_brief", ""),
        "top_5_cuts":           parsed.get("top_5_cuts", []) or [],
        "new_cuts_detected":    parsed.get("new_cuts_detected", []) or [],
        "catalog_suggestions":  parsed.get("catalog_suggestions", []) or [],
        "source_week":          trend.get("week", ""),
        "model":                MODEL,
    }

    try:
        BRIEF_PATH.write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Saved brief → %s", BRIEF_PATH)
    except Exception as e:
        logger.error("Could not write trend_brief.json: %s", e)

    added = _merge_new_cuts(aliases, brief["catalog_suggestions"])
    if added:
        try:
            ALIASES_PATH.write_text(json.dumps(aliases, ensure_ascii=False, indent=2), encoding="utf-8")
            logger.info("Added %d new cuts to haircut_aliases.json", added)
        except Exception as e:
            logger.error("Could not write haircut_aliases.json: %s", e)

    print("\n=== Weekly brief ===")
    print(brief.get("weekly_brief", "(empty)"))
    if brief["top_5_cuts"]:
        print("\nTop 5 cuts:")
        for i, c in enumerate(brief["top_5_cuts"], 1):
            print(f"  {i}. {c}")
    if brief["new_cuts_detected"]:
        print(f"\nNew cuts detected: {brief['new_cuts_detected']}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.exception("Unhandled error in trend_analyzer: %s", e)
        sys.exit(0)
