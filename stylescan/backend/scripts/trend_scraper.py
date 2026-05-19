"""
Weekly Instagram hashtag trend scraper for VISAI.

Scrapes a fixed set of haircut hashtags, aggregates mention counts and
average engagement, and saves the result to
`knowledge_base/trend_data.json` for the analyzer step.

Run:
    python -m scripts.trend_scraper

Design notes
------------
- Uses instagrapi if available + INSTAGRAM_USERNAME / INSTAGRAM_PASSWORD
  in `.env`. Otherwise falls back to deterministic sample data so the
  downstream analyzer/cron pipeline keeps working end-to-end.
- Optionally complements with Google Trends via `pytrends` if installed.
- Never crashes: any failure → log + write fallback file + exit 0.
"""

from __future__ import annotations

import json
import logging
import os
import random
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).parent.parent
KB_DIR     = ROOT / "knowledge_base"
ENV_PATH   = ROOT / ".env"
OUT_PATH   = KB_DIR / "trend_data.json"

KB_DIR.mkdir(parents=True, exist_ok=True)

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("trend_scraper")

# ── Targets ────────────────────────────────────────────────────────────────
HASHTAGS: list[str] = [
    "fade",
    "skinfade",
    "barbershop",
    "haircutsformen",
    "quiff",
    "mullet",
    "texturedcrop",
    "edgarcut",
    "midskinfade",
    "lowfade",
]

POSTS_PER_HASHTAG = 10

# Phrase → canonical haircut name (lowercase, used to count caption mentions).
# Keys are matched against caption text after lowercasing.
CUT_KEYWORDS: dict[str, str] = {
    "skin fade":      "skin fade",
    "skinfade":       "skin fade",
    "mid fade":       "mid fade",
    "midfade":        "mid fade",
    "low fade":       "low fade",
    "lowfade":        "low fade",
    "high fade":      "high fade",
    "taper fade":     "taper fade",
    "taper":          "taper",
    "quiff":          "quiff",
    "mullet":         "mullet",
    "textured crop":  "textured crop",
    "texturedcrop":   "textured crop",
    "edgar cut":      "edgar cut",
    "edgarcut":       "edgar cut",
    "buzz cut":       "buzz cut",
    "buzzcut":        "buzz cut",
    "crew cut":       "crew cut",
    "pompadour":      "pompadour",
    "undercut":       "undercut",
    "slick back":     "slick back",
    "slickback":      "slick back",
    "fringe":         "fringe",
    "french crop":    "french crop",
    "frenchcrop":     "french crop",
    "wolf cut":       "wolf cut",
    "wolfcut":        "wolf cut",
    "buzz":           "buzz cut",
    "fade":           "fade",
}


# ── .env helper ────────────────────────────────────────────────────────────
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


# ── Fallback / previous data ───────────────────────────────────────────────
def _load_previous() -> Optional[dict]:
    if not OUT_PATH.exists():
        return None
    try:
        return json.loads(OUT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def _sample_data(reason: str) -> dict:
    """Deterministic-ish realistic fallback (used when scraping is unavailable)."""
    rng = random.Random(datetime.now().strftime("%Y-%W"))  # stable per ISO week
    hashtags_out: dict[str, dict] = {}
    for tag in HASHTAGS:
        hashtags_out[f"#{tag}"] = {
            "posts_checked": POSTS_PER_HASHTAG,
            "avg_likes": rng.randint(400, 2200),
        }

    base_mentions = {
        "skin fade":     rng.randint(35, 55),
        "mid fade":      rng.randint(20, 35),
        "low fade":      rng.randint(15, 28),
        "taper fade":    rng.randint(12, 24),
        "quiff":         rng.randint(15, 28),
        "textured crop": rng.randint(12, 22),
        "edgar cut":     rng.randint(8, 20),
        "mullet":        rng.randint(8, 18),
        "buzz cut":      rng.randint(6, 14),
        "french crop":   rng.randint(5, 12),
        "pompadour":     rng.randint(4, 10),
        "undercut":      rng.randint(4, 10),
        "slick back":    rng.randint(3, 9),
        "wolf cut":      rng.randint(3, 8),
    }
    sorted_mentions = dict(sorted(base_mentions.items(), key=lambda x: -x[1]))

    return {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "week": datetime.now(timezone.utc).strftime("%G-W%V"),
        "instagram_hashtags": hashtags_out,
        "haircut_mentions": sorted_mentions,
        "trending_up": ["edgar cut", "mullet", "textured crop"],
        "trending_down": [],
        "google_trends": {},
        "source": "fallback_sample",
        "fallback_reason": reason,
    }


# ── Instagram scraping (instagrapi) ────────────────────────────────────────
def _scrape_instagram(env: dict[str, str]) -> Optional[dict]:
    username = (env.get("INSTAGRAM_USERNAME") or os.environ.get("INSTAGRAM_USERNAME", "")).strip()
    password = (env.get("INSTAGRAM_PASSWORD") or os.environ.get("INSTAGRAM_PASSWORD", "")).strip()
    if not username or not password:
        logger.info("No Instagram credentials in .env — skipping live scrape")
        return None

    try:
        from instagrapi import Client  # type: ignore
    except ImportError:
        logger.info("instagrapi not installed — skipping live scrape")
        return None

    cl = Client()
    cl.delay_range = [2, 5]
    session_file = KB_DIR / "barber_references" / "instagram_session"
    try:
        if session_file.exists():
            try:
                cl.load_settings(session_file)
                cl.login(username, password)
            except Exception:
                cl.login(username, password)
        else:
            cl.login(username, password)
            session_file.parent.mkdir(parents=True, exist_ok=True)
            try:
                cl.dump_settings(session_file)
            except Exception:
                pass
    except Exception as e:
        logger.warning("Instagram login failed: %s", e)
        return None

    hashtags_out: dict[str, dict] = {}
    mention_counter: Counter[str] = Counter()

    for tag in HASHTAGS:
        try:
            medias = cl.hashtag_medias_recent(tag, amount=POSTS_PER_HASHTAG)
        except Exception as e:
            logger.warning("hashtag_medias_recent(%s) failed: %s", tag, e)
            hashtags_out[f"#{tag}"] = {"posts_checked": 0, "avg_likes": 0, "error": str(e)[:120]}
            continue

        likes_total = 0
        checked = 0
        for m in medias:
            likes = int(getattr(m, "like_count", 0) or 0)
            caption = (getattr(m, "caption_text", "") or "").lower()
            likes_total += likes
            checked += 1
            _count_mentions(caption, mention_counter)

        hashtags_out[f"#{tag}"] = {
            "posts_checked": checked,
            "avg_likes": int(likes_total / checked) if checked else 0,
        }
        # be polite between hashtags
        time.sleep(random.uniform(3, 7))

    if not mention_counter:
        logger.warning("Instagram scrape returned 0 mentions — using fallback")
        return None

    return {
        "instagram_hashtags": hashtags_out,
        "haircut_mentions": dict(mention_counter.most_common()),
        "source": "instagram_hashtags",
    }


def _count_mentions(caption: str, counter: Counter[str]) -> None:
    if not caption:
        return
    text = re.sub(r"[#@]", " ", caption.lower())
    # Sort longer keys first so "skin fade" beats "fade"
    for key in sorted(CUT_KEYWORDS, key=len, reverse=True):
        if key in text:
            counter[CUT_KEYWORDS[key]] += 1


# ── Google Trends (optional) ───────────────────────────────────────────────
def _google_trends() -> dict:
    try:
        from pytrends.request import TrendReq  # type: ignore
    except ImportError:
        return {}

    try:
        py = TrendReq(hl="es-ES", tz=60)
        kw = ["skin fade", "mid fade", "edgar cut", "mullet", "quiff", "textured crop"]
        py.build_payload(kw, timeframe="now 7-d", geo="ES")
        df = py.interest_over_time()
        if df is None or df.empty:
            return {}
        return {k: int(df[k].mean()) for k in kw if k in df.columns}
    except Exception as e:
        logger.info("Google Trends skipped: %s", e)
        return {}


# ── Trend up/down detection ────────────────────────────────────────────────
def _detect_movement(current: dict[str, int], previous: Optional[dict]) -> tuple[list[str], list[str]]:
    if not previous:
        # No baseline → mark top 3 as trending up
        return list(current.keys())[:3], []
    prev_mentions: dict[str, int] = previous.get("haircut_mentions", {}) or {}
    up, down = [], []
    for cut, n in current.items():
        prev_n = prev_mentions.get(cut, 0)
        if prev_n == 0 and n >= 5:
            up.append(cut)
        elif prev_n and n > prev_n * 1.3:
            up.append(cut)
        elif prev_n and n < prev_n * 0.7:
            down.append(cut)
    return up[:5], down[:5]


# ── Main ───────────────────────────────────────────────────────────────────
def main() -> int:
    env = _read_dotenv(ENV_PATH)
    now = datetime.now(timezone.utc)
    previous = _load_previous()

    scrape = _scrape_instagram(env)
    if scrape is None:
        logger.warning("Falling back to sample trend data")
        data = _sample_data("instagram_unavailable")
    else:
        up, down = _detect_movement(scrape["haircut_mentions"], previous)
        data = {
            "scraped_at": now.isoformat(),
            "week": now.strftime("%G-W%V"),
            "instagram_hashtags": scrape["instagram_hashtags"],
            "haircut_mentions": scrape["haircut_mentions"],
            "trending_up": up,
            "trending_down": down,
            "google_trends": _google_trends(),
            "source": scrape["source"],
        }

    try:
        OUT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Saved trend data → %s", OUT_PATH)
    except Exception as e:
        logger.error("Could not write trend_data.json: %s", e)
        return 0  # never fail cron

    top = list(data["haircut_mentions"].items())[:5]
    logger.info("Top cuts this week: %s", ", ".join(f"{k} ({v})" for k, v in top))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.exception("Unhandled error in trend_scraper: %s", e)
        sys.exit(0)
