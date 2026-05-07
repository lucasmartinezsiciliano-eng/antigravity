"""
Barber Instagram Reference Agent
=================================
Scrapes public barber Instagram accounts, classifies each haircut photo
using Claude Vision, and builds a structured reference database.

The references are used by image_gen_service.py to improve FLUX Kontext
prompts with real barbershop technique details.

Usage:
    # Run full cycle (reads barber_accounts.json)
    python -m scripts.barber_instagram_agent

    # Specific accounts
    python -m scripts.barber_instagram_agent --accounts broskibarbers fademaster.bcn

    # Limit posts per account (useful for first run)
    python -m scripts.barber_instagram_agent --max-posts 20

    # Dry run — classify only, don't save images
    python -m scripts.barber_instagram_agent --dry-run

Output:
    knowledge_base/barber_references/index.json   — structured metadata
    knowledge_base/barber_references/images/       — downloaded haircut photos
    knowledge_base/barber_accounts.json            — updated last_run / counts
"""

import argparse
import base64
import json
import logging
import os
import random
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Load .env from backend root before anything else
_ENV_PATH = Path(__file__).parent.parent / ".env"
if _ENV_PATH.exists():
    for _line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT         = Path(__file__).parent.parent
KB_DIR       = ROOT / "knowledge_base"
REF_DIR      = KB_DIR / "barber_references"
IMG_DIR      = REF_DIR / "images"
INDEX_PATH   = REF_DIR / "index.json"
ACCOUNTS_PATH = KB_DIR / "barber_accounts.json"

SESSION_FILE = KB_DIR / "barber_references" / "instagram_session"

REF_DIR.mkdir(parents=True, exist_ok=True)
IMG_DIR.mkdir(parents=True, exist_ok=True)

# ── Constants ────────────────────────────────────────────────────────────────
FACE_SHAPES     = ["oval", "round", "square", "oblong", "heart", "diamond", "triangle"]
MAINTENANCE     = ["bajo", "medio", "alto"]
STYLE_LEVELS    = ["clásico", "moderno", "atrevido"]
CUT_TYPES       = ["fade", "taper", "undercut", "pompadour", "textured", "slick", "buzz", "quiff", "crop", "otro"]
MAX_IMAGE_MB    = 4          # Claude Vision limit
MIN_QUALITY     = 0.55       # Below this → skip
DELAY_POSTS     = (2, 5)     # Seconds between posts (random)
DELAY_ACCOUNTS  = (10, 20)   # Seconds between accounts (random)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("barber_agent")


# ── Classification prompt ────────────────────────────────────────────────────
CLASSIFY_SYSTEM = """
Eres un barbero experto en visagismo con 15 años de experiencia en España.
Analizas fotos del trabajo de barberos para extraer referencias técnicas.
Respondes SIEMPRE con JSON válido, sin texto adicional.
""".strip()

CLASSIFY_PROMPT = """
Analiza esta imagen de un barbero. Determina si muestra el resultado de un corte de pelo.

Devuelve este JSON (todos los campos obligatorios):
{
  "is_haircut_result": true/false,
  "skip_reason": "solo si is_haircut_result=false: producto/grupo/local/otro",

  "face_shape": "oval|round|square|oblong|heart|diamond|triangle|unknown",
  "hair_texture": "liso|ondulado|rizado|muy_rizado|unknown",
  "beard_present": true/false,

  "cut_name_en": "nombre técnico en inglés (ej: High Fade with Textured Top)",
  "cut_name_es": "nombre en español (ej: Degradado Alto con Tope Texturizado)",
  "cut_type": "fade|taper|undercut|pompadour|textured|slick|buzz|quiff|crop|otro",
  "fade_level": "none|low|mid|high|skin|null",
  "top_style": "textured|slick|natural|quiff|pompadour|crop|buzz|null",

  "maintenance_level": "bajo|medio|alto",
  "style_level": "clásico|moderno|atrevido",

  "why_this_works": "1-2 frases sobre por qué este corte favorece esta forma de cara",
  "barbershop_technique": "instrucciones técnicas concretas para reproducirlo (números de máquina, técnicas)",
  "what_to_avoid": "error común al hacer este corte",

  "photo_quality": 0.0-1.0,
  "tags": ["array", "de", "tags", "relevantes"]
}

Sé específico en barbershop_technique — esto es lo que usaremos para instruir a la IA generadora de imágenes.
""".strip()


# ── Index helpers ────────────────────────────────────────────────────────────
def load_index() -> dict:
    if INDEX_PATH.exists():
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    return {"updated_at": None, "total": 0, "references": []}


def save_index(index: dict) -> None:
    index["updated_at"] = datetime.now(timezone.utc).isoformat()
    index["total"] = len(index["references"])
    INDEX_PATH.write_text(
        json.dumps(index, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("Index saved — %d total references", index["total"])


def already_indexed(index: dict, post_shortcode: str) -> bool:
    return any(r.get("post_shortcode") == post_shortcode for r in index["references"])


# ── Claude Vision ─────────────────────────────────────────────────────────────
def classify_image(image_bytes: bytes, account: str) -> Optional[dict]:
    """Call Claude Vision to classify a haircut image. Returns None on skip/error."""
    try:
        import anthropic
    except ImportError:
        logger.error("anthropic not installed — pip install anthropic")
        return None

    # Check size
    if len(image_bytes) > MAX_IMAGE_MB * 1024 * 1024:
        logger.debug("Image too large (%d MB), skipping", len(image_bytes) // (1024 * 1024))
        return None

    client = anthropic.Anthropic()

    try:
        img_b64 = base64.standard_b64encode(image_bytes).decode()
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=600,
            system=CLASSIFY_SYSTEM,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": img_b64,
                        },
                    },
                    {"type": "text", "text": CLASSIFY_PROMPT},
                ],
            }],
        )
        raw = response.content[0].text.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning("[%s] JSON parse error: %s", account, e)
        return None
    except Exception as e:
        logger.warning("[%s] Claude Vision error: %s", account, e)
        return None


# ── Instagram login ────────────────────────────────────────────────────────────
def get_instaloader():
    """
    Return an authenticated Instaloader instance.
    Tries to load a saved session first; falls back to full login.
    Saves the session to disk after login so subsequent runs are instant.
    """
    try:
        import instaloader
    except ImportError:
        logger.error("instaloader not installed — pip install instaloader")
        return None

    username = os.environ.get("INSTAGRAM_USERNAME", "").strip()
    password = os.environ.get("INSTAGRAM_PASSWORD", "").strip()

    if not username or not password:
        logger.warning("INSTAGRAM_USERNAME / INSTAGRAM_PASSWORD not set — running anonymously (expect 429)")

    L = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        quiet=True,
        max_connection_attempts=3,
        request_timeout=30,
        sleep=True,          # instaloader adds its own polite delays
        compress_json=False,
    )

    if not username:
        return L

    # Try to load saved session (avoids full login on every run)
    session_path = str(SESSION_FILE)
    try:
        L.load_session_from_file(username, session_path)
        logger.info("Instagram session loaded for @%s", username)
        return L
    except Exception:
        pass  # No session yet — do full login

    logger.info("Logging in to Instagram as @%s …", username)
    try:
        L.login(username, password)
        SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        L.save_session_to_file(session_path)
        logger.info("Login OK — session saved to %s", session_path)
    except Exception as e:
        logger.error("Instagram login failed: %s", e)

    return L


# ── Instagram scraping ────────────────────────────────────────────────────────
def scrape_account(
    account: str,
    max_posts: int,
    index: dict,
    L=None,
    dry_run: bool = False,
    save_images: bool = False,
) -> list[dict]:
    """Download and classify posts from one Instagram account."""
    try:
        import instaloader
    except ImportError:
        logger.error("instaloader not installed — pip install instaloader")
        return []

    if L is None:
        L = get_instaloader()

    logger.info("── Account: @%s ──", account)
    new_refs: list[dict] = []
    processed = 0

    try:
        profile = instaloader.Profile.from_username(L.context, account)
    except Exception as e:
        logger.error("[%s] Could not load profile: %s", account, e)
        return []

    logger.info("[%s] %d posts total, processing up to %d", account, profile.mediacount, max_posts)

    for post in profile.get_posts():
        if processed >= max_posts:
            break

        # Skip non-image posts
        if post.is_video:
            continue

        shortcode = post.shortcode

        if already_indexed(index, shortcode):
            logger.debug("[%s] Already indexed: %s", account, shortcode)
            processed += 1
            continue

        # Download image bytes
        try:
            import requests
            img_resp = requests.get(post.url, timeout=15)
            img_resp.raise_for_status()
            image_bytes = img_resp.content
        except Exception as e:
            logger.warning("[%s] Download failed %s: %s", account, shortcode, e)
            time.sleep(random.uniform(*DELAY_POSTS))
            processed += 1
            continue

        # Classify
        logger.info("[%s] Classifying %s …", account, shortcode)
        classification = classify_image(image_bytes, account)

        if not classification:
            processed += 1
            time.sleep(random.uniform(*DELAY_POSTS))
            continue

        # Skip non-haircut images
        if not classification.get("is_haircut_result"):
            logger.debug("[%s] Not a haircut result: %s (%s)", account, shortcode, classification.get("skip_reason", "?"))
            processed += 1
            time.sleep(random.uniform(*DELAY_POSTS))
            continue

        # Quality gate
        quality = float(classification.get("photo_quality", 0))
        if quality < MIN_QUALITY:
            logger.debug("[%s] Low quality (%.2f): %s", account, quality, shortcode)
            processed += 1
            time.sleep(random.uniform(*DELAY_POSTS))
            continue

        # Build reference record — images not saved by default (text metadata is enough for FLUX)
        ref_id = str(uuid.uuid4())
        image_filename: Optional[str] = None
        if save_images and not dry_run:
            image_filename = f"{ref_id}.jpg"
            (IMG_DIR / image_filename).write_bytes(image_bytes)

        ref = {
            "id": ref_id,
            "account": account,
            "post_shortcode": shortcode,
            "post_url": f"https://instagram.com/p/{shortcode}/",
            "image_file": image_filename,

            "face_shape": classification.get("face_shape", "unknown"),
            "hair_texture": classification.get("hair_texture", "unknown"),
            "beard_present": classification.get("beard_present", False),

            "cut_name_en": classification.get("cut_name_en", ""),
            "cut_name_es": classification.get("cut_name_es", ""),
            "cut_type": classification.get("cut_type", "otro"),
            "fade_level": classification.get("fade_level"),
            "top_style": classification.get("top_style"),

            "maintenance_level": classification.get("maintenance_level", "medio"),
            "style_level": classification.get("style_level", "moderno"),

            "why_this_works": classification.get("why_this_works", ""),
            "barbershop_technique": classification.get("barbershop_technique", ""),
            "what_to_avoid": classification.get("what_to_avoid", ""),

            "photo_quality": quality,
            "tags": classification.get("tags", []),
            "indexed_at": datetime.now(timezone.utc).isoformat(),
        }

        new_refs.append(ref)
        logger.info(
            "[%s] ✓ %s | %s | %s | q=%.2f",
            account,
            shortcode,
            ref["face_shape"],
            ref["cut_name_es"] or ref["cut_name_en"],
            quality,
        )

        processed += 1
        time.sleep(random.uniform(*DELAY_POSTS))

    logger.info("[%s] Done — %d new references", account, len(new_refs))
    return new_refs


# ── Reference lookup (used by image_gen_service) ─────────────────────────────
def find_references(
    face_shape: str,
    cut_name: str,
    limit: int = 3,
) -> list[dict]:
    """
    Find barber references matching a face shape and cut name.
    Returns list of dicts with barbershop_technique and why_this_works.
    Used by image_gen_service to enrich FLUX prompts.
    """
    if not INDEX_PATH.exists():
        return []

    try:
        index = load_index()
    except Exception:
        return []

    cut_norm = cut_name.lower()
    scored: list[tuple[float, dict]] = []

    for ref in index.get("references", []):
        score = 0.0

        # Face shape match — most important
        if ref.get("face_shape") == face_shape:
            score += 2.0

        # Cut name similarity (token overlap)
        ref_name = (ref.get("cut_name_en", "") + " " + ref.get("cut_name_es", "")).lower()
        common_tokens = set(cut_norm.split()) & set(ref_name.split())
        score += len(common_tokens) * 0.5

        # Quality bonus
        score += ref.get("photo_quality", 0) * 0.5

        if score > 1.0:
            scored.append((score, ref))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored[:limit]]


def build_reference_context(face_shape: str, cut_name: str) -> str:
    """
    Build a reference context string for FLUX prompts.
    Returns empty string if no references found.
    """
    refs = find_references(face_shape, cut_name, limit=2)
    if not refs:
        return ""

    parts = []
    for ref in refs:
        if ref.get("barbershop_technique"):
            parts.append(ref["barbershop_technique"])
        if ref.get("why_this_works"):
            parts.append(f"Why it works: {ref['why_this_works']}")

    if not parts:
        return ""

    return "Real barbershop reference: " + " | ".join(parts[:2])


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Barber Instagram Reference Agent")
    parser.add_argument(
        "--accounts", nargs="*",
        help="Instagram handles to scrape (without @). Overrides barber_accounts.json.",
    )
    parser.add_argument("--max-posts", type=int, default=30, help="Max posts per account (default: 30)")
    parser.add_argument("--save-images", action="store_true", help="Also save images locally (not needed for FLUX text enrichment)")
    parser.add_argument("--dry-run", action="store_true", help="Classify but write nothing to disk")
    args = parser.parse_args()

    # Resolve accounts
    if args.accounts:
        accounts = [a.lstrip("@") for a in args.accounts]
    else:
        if not ACCOUNTS_PATH.exists():
            logger.error("barber_accounts.json not found and no --accounts provided")
            sys.exit(1)
        config = json.loads(ACCOUNTS_PATH.read_text(encoding="utf-8"))
        accounts = config.get("accounts", [])

    if not accounts:
        logger.error("No accounts to process")
        sys.exit(1)

    logger.info("Barber Instagram Agent starting")
    logger.info("Accounts: %s", accounts)
    logger.info("Max posts/account: %d | Save images: %s | Dry run: %s", args.max_posts, args.save_images, args.dry_run)

    # Single login — reused across all accounts
    L = get_instaloader()

    index = load_index()
    total_new = 0

    for i, account in enumerate(accounts):
        new_refs = scrape_account(account, args.max_posts, index, L, args.dry_run, args.save_images)
        index["references"].extend(new_refs)
        total_new += len(new_refs)

        if not args.dry_run:
            save_index(index)

        if i < len(accounts) - 1:
            delay = random.uniform(*DELAY_ACCOUNTS)
            logger.info("Waiting %.0fs before next account…", delay)
            time.sleep(delay)

    # Update barber_accounts.json
    if not args.dry_run and ACCOUNTS_PATH.exists():
        config = json.loads(ACCOUNTS_PATH.read_text(encoding="utf-8"))
        config["last_run"] = datetime.now(timezone.utc).isoformat()
        config["total_references"] = index["total"]
        ACCOUNTS_PATH.write_text(
            json.dumps(config, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    logger.info("Done — %d new references added. Total: %d", total_new, index["total"])


if __name__ == "__main__":
    main()
