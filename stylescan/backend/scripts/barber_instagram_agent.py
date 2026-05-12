"""
Barber Instagram Reference Agent
=================================
Scrapes public barber Instagram accounts, classifies each photo with Claude
Vision, and builds a structured reference database used by image_gen_service.py.

RATE LIMIT STRATEGY — respeta Instagram sin bans:
  - Presupuesto diario: 80 peticiones/día (profile loads + image downloads)
  - Entre posts:     30-60 s aleatorio
  - Entre cuentas:   4-8 min aleatorio
  - Si recibe 429:   para el día, guarda estado, reintenta mañana
  - Estado persistido en knowledge_base/barber_references/agent_state.json

COBERTURA — detecta cortes de TODAS las edades y regiones de España:
  - barber_accounts.json tiene cuentas clasificadas por demografía y región
  - El prompt de Claude detecta edad estimada del cliente
  - El índice almacena trending_score basado en fecha del post
  - Candidatos para curated/ (fotos de nuca sin cara) se detectan automáticamente

Usage:
    python -m scripts.barber_instagram_agent               # ciclo completo
    python -m scripts.barber_instagram_agent --max-posts 5  # test rápido
    python -m scripts.barber_instagram_agent --save-images  # guarda jpgs también
    python -m scripts.barber_instagram_agent --curated-only # solo candidatos nuca
"""

import argparse
import base64
import json
import logging
import os
import random
import sqlite3
import sys
import time
import shutil
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Cargar .env ──────────────────────────────────────────────────────────────
_ENV_PATH = Path(__file__).parent.parent / ".env"
if _ENV_PATH.exists():
    for _line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

# ── Rutas ────────────────────────────────────────────────────────────────────
ROOT          = Path(__file__).parent.parent
KB_DIR        = ROOT / "knowledge_base"
REF_DIR       = KB_DIR / "barber_references"
IMG_DIR       = REF_DIR / "images"
CURATED_DIR   = REF_DIR / "curated"
DB_PATH       = REF_DIR / "barber_refs.db"
INDEX_PATH    = DB_PATH   # backwards-compat alias — callers that check .exists() get the DB file
STATE_PATH    = REF_DIR / "agent_state.json"
ACCOUNTS_PATH = KB_DIR / "barber_accounts.json"
SESSION_FILE  = REF_DIR / "instagram_session"

for _d in [REF_DIR, IMG_DIR, CURATED_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# ── Constantes ───────────────────────────────────────────────────────────────
MAX_IMAGE_MB      = 4
MIN_QUALITY       = 0.55
CURATED_MIN_Q     = 0.72      # Umbral más alto para candidatos a curated/
DAILY_BUDGET      = 80        # Peticiones máximas por día
DELAY_POSTS       = (30, 60)  # Segundos entre posts — conservador
DELAY_ACCOUNTS    = (240, 480)  # 4-8 min entre cuentas

# Trending: posts de los últimos N días reciben score extra
TRENDING_DAYS     = 90

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("barber_agent")


# ── PROMPT CLASIFICACIÓN ─────────────────────────────────────────────────────
CLASSIFY_SYSTEM = """
Eres un barbero experto en visagismo con 15 años de experiencia en España.
Trabajas en una barbería que atiende a hombres de TODAS las edades — desde chicos de 18 años
hasta señores de 70. Conoces perfectamente los cortes clásicos (navaja, tijera, caballero)
igual que los modernos (fade, textured, wolf cut).
Analizas fotos de trabajo de barberos para extraer referencias técnicas.
Respondes SIEMPRE con JSON válido, sin texto adicional.
""".strip()

CLASSIFY_PROMPT = """
Analiza esta imagen de una barbería. Determina si muestra el resultado de un corte de pelo masculino.

Devuelve EXACTAMENTE este JSON (todos los campos obligatorios):
{
  "is_haircut_result": true/false,
  "skip_reason": "solo si false: producto/grupo/local/mujer/otro",

  "face_shape": "oval|round|square|oblong|heart|diamond|triangle|unknown",
  "hair_texture": "liso|ondulado|rizado|muy_rizado|unknown",
  "beard_present": true/false,
  "beard_style": "sin_barba|barba_corta|barba_media|barba_larga|bigote|null",

  "client_age_group": "joven|adulto|mayor",
  "client_age_estimate": 25,

  "cut_name_en": "nombre técnico en inglés (ej: Classic Taper with Side Part)",
  "cut_name_es": "nombre en español (ej: Taper Clásico con Raya al Lado)",
  "cut_type": "fade|taper|undercut|pompadour|textured|slick|buzz|quiff|crop|clasico|navaja|otro",
  "fade_level": "none|low|mid|high|skin|null",
  "top_style": "textured|slick|natural|quiff|pompadour|crop|buzz|clasico|null",
  "length_on_top": "muy_corto|corto|medio|largo",

  "is_trending_spain": true/false,
  "trending_reason": "1 frase: por qué este corte está en tendencia en España ahora o es un clásico atemporal",

  "photo_angle": "front|side_left|side_right|back|detail|unknown",
  "is_nuca_shot": true/false,
  "has_face_visible": true/false,
  "curated_candidate": true/false,

  "skin_tone": "claro|medio|oscuro|muy_oscuro|unknown",

  "maintenance_level": "bajo|medio|alto",
  "style_level": "clasico|moderno|atrevido",

  "why_this_works": "1-2 frases sobre por qué este corte favorece la forma de cara detectada",
  "barbershop_technique": "instrucciones técnicas específicas: números de máquina, tipo de degradado, técnica de tijera/navaja, puntos clave",
  "what_to_avoid": "el error más común al hacer este corte",

  "photo_quality": 0.0,
  "tags": ["array", "de", "tags"]
}

IMPORTANTE sobre client_age_group:
- joven: 15-34 años (pelo abundante, estilos modernos/atrevidos)
- adulto: 35-55 años (mezcla de estilos, puede haber canas)
- mayor: 56+ años (pelo más escaso, estilos clásicos, canas/blanco)

IMPORTANTE sobre skin_tone (tono de piel del cliente en la foto):
- claro: piel muy clara, tipo I-II Fitzpatrick (europeo del norte, rubio/pelirrojo)
- medio: piel media, tipo III-IV Fitzpatrick (mediterráneo, latino claro, asiático)
- oscuro: piel oscura, tipo V Fitzpatrick (latino oscuro, árabe, sudamericano)
- muy_oscuro: tipo VI Fitzpatrick (africano subsahariano, caribeño oscuro)
- unknown: si has_face_visible=false o no se puede determinar con certeza
- Crítico para IA generativa: el modelo de imagen mezcla tonos del cliente y la referencia

IMPORTANTE sobre curated_candidate:
- Solo true si: is_nuca_shot=true AND has_face_visible=false AND photo_quality >= 0.72
- Estas fotos son las que usaremos como referencia para generar imágenes con IA

IMPORTANTE sobre is_trending_spain:
- Considera tendencia si: aparece mucho en barberías españolas actuales, es viral en redes, o es un clásico que nunca pasa de moda
- Cortes clásicos atemporales (taper, navaja, caballero): también son true porque son siempre demandados

Sé muy específico en barbershop_technique — es lo que usará la IA para generar las imágenes.
""".strip()


# ── ESTADO DEL AGENTE (presupuesto diario) ───────────────────────────────────
def load_state() -> dict:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if STATE_PATH.exists():
        try:
            state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            if state.get("date") == today:
                return state
        except Exception:
            pass
    return {"date": today, "requests_today": 0, "accounts_done": [], "last_429": None}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def budget_ok(state: dict) -> bool:
    return state["requests_today"] < DAILY_BUDGET


def charge_request(state: dict, n: int = 1) -> None:
    state["requests_today"] += n
    save_state(state)


# ── SQLITE — esquema ─────────────────────────────────────────────────────────
_SCHEMA = """
CREATE TABLE IF NOT EXISTS barber_refs (
    id TEXT PRIMARY KEY,
    ref_key TEXT UNIQUE NOT NULL,
    set_id TEXT NOT NULL,
    slide_index INTEGER DEFAULT 0,
    carousel_total INTEGER DEFAULT 1,
    is_carousel INTEGER DEFAULT 0,
    photo_angle TEXT DEFAULT 'unknown',
    skin_tone TEXT DEFAULT 'unknown',

    account TEXT,
    account_demographic TEXT,
    account_region TEXT,
    post_shortcode TEXT,
    post_url TEXT,
    post_date TEXT,
    image_file TEXT,
    instagram_cdn_url TEXT,
    curated_file TEXT,

    face_shape TEXT,
    hair_texture TEXT,
    beard_present INTEGER DEFAULT 0,
    beard_style TEXT,

    client_age_group TEXT,
    client_age_estimate INTEGER,

    cut_name_en TEXT DEFAULT '',
    cut_name_es TEXT DEFAULT '',
    cut_type TEXT DEFAULT 'otro',
    fade_level TEXT,
    top_style TEXT,
    length_on_top TEXT,

    is_trending_spain INTEGER DEFAULT 0,
    trending_reason TEXT DEFAULT '',
    trending_score REAL DEFAULT 0.3,

    is_nuca_shot INTEGER DEFAULT 0,
    has_face_visible INTEGER DEFAULT 1,
    curated_candidate INTEGER DEFAULT 0,

    maintenance_level TEXT DEFAULT 'medio',
    style_level TEXT DEFAULT 'moderno',
    why_this_works TEXT DEFAULT '',
    barbershop_technique TEXT DEFAULT '',
    what_to_avoid TEXT DEFAULT '',

    photo_quality REAL DEFAULT 0.0,
    tags TEXT DEFAULT '[]',
    indexed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_face_shape  ON barber_refs(face_shape);
CREATE INDEX IF NOT EXISTS idx_photo_angle ON barber_refs(photo_angle);
CREATE INDEX IF NOT EXISTS idx_age_group   ON barber_refs(client_age_group);
CREATE INDEX IF NOT EXISTS idx_trending    ON barber_refs(is_trending_spain);
CREATE INDEX IF NOT EXISTS idx_skin_tone   ON barber_refs(skin_tone);
CREATE INDEX IF NOT EXISTS idx_set_id      ON barber_refs(set_id);
"""


@contextmanager
def _db():
    """WAL-mode connection — safe for concurrent reads while agent writes."""
    con = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def _init_db() -> None:
    with _db() as con:
        con.executescript(_SCHEMA)


_init_db()


# ── ÍNDICE ───────────────────────────────────────────────────────────────────
def count_refs() -> int:
    with _db() as con:
        return con.execute("SELECT COUNT(*) FROM barber_refs").fetchone()[0]


def already_indexed(ref_key: str) -> bool:
    """O(1) lookup via UNIQUE index. ref_key = shortcode_slideIdx."""
    with _db() as con:
        return con.execute(
            "SELECT 1 FROM barber_refs WHERE ref_key=?", (ref_key,)
        ).fetchone() is not None


def insert_ref(ref: dict) -> None:
    """Insert or replace a reference row atomically."""
    with _db() as con:
        con.execute(
            """
            INSERT OR REPLACE INTO barber_refs (
                id, ref_key, set_id, slide_index, carousel_total, is_carousel,
                photo_angle, skin_tone,
                account, account_demographic, account_region,
                post_shortcode, post_url, post_date,
                image_file, instagram_cdn_url, curated_file,
                face_shape, hair_texture, beard_present, beard_style,
                client_age_group, client_age_estimate,
                cut_name_en, cut_name_es, cut_type, fade_level, top_style, length_on_top,
                is_trending_spain, trending_reason, trending_score,
                is_nuca_shot, has_face_visible, curated_candidate,
                maintenance_level, style_level,
                why_this_works, barbershop_technique, what_to_avoid,
                photo_quality, tags, indexed_at
            ) VALUES (
                :id, :ref_key, :set_id, :slide_index, :carousel_total, :is_carousel,
                :photo_angle, :skin_tone,
                :account, :account_demographic, :account_region,
                :post_shortcode, :post_url, :post_date,
                :image_file, :instagram_cdn_url, :curated_file,
                :face_shape, :hair_texture, :beard_present, :beard_style,
                :client_age_group, :client_age_estimate,
                :cut_name_en, :cut_name_es, :cut_type, :fade_level, :top_style, :length_on_top,
                :is_trending_spain, :trending_reason, :trending_score,
                :is_nuca_shot, :has_face_visible, :curated_candidate,
                :maintenance_level, :style_level,
                :why_this_works, :barbershop_technique, :what_to_avoid,
                :photo_quality, :tags, :indexed_at
            )
            """,
            {
                **ref,
                "is_carousel":       int(bool(ref.get("is_carousel", False))),
                "beard_present":     int(bool(ref.get("beard_present", False))),
                "is_trending_spain": int(bool(ref.get("is_trending_spain", False))),
                "is_nuca_shot":      int(bool(ref.get("is_nuca_shot", False))),
                "has_face_visible":  int(bool(ref.get("has_face_visible", True))),
                "curated_candidate": int(bool(ref.get("curated_candidate", False))),
                "skin_tone":         ref.get("skin_tone", "unknown"),
                "tags":              json.dumps(ref.get("tags", []), ensure_ascii=False),
            },
        )
    logger.info("DB ✓ %s — %s", ref.get("ref_key"), ref.get("cut_name_es", ""))


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    for col in ("is_carousel", "beard_present", "is_trending_spain",
                "is_nuca_shot", "has_face_visible", "curated_candidate"):
        d[col] = bool(d.get(col, 0))
    try:
        d["tags"] = json.loads(d.get("tags") or "[]")
    except Exception:
        d["tags"] = []
    return d


# ── TRENDING SCORE ────────────────────────────────────────────────────────────
def trending_score(post_timestamp: Optional[datetime]) -> float:
    """0.0–1.0 según la antigüedad del post. Más reciente = más trending."""
    if not post_timestamp:
        return 0.3
    now = datetime.now(timezone.utc)
    if post_timestamp.tzinfo is None:
        post_timestamp = post_timestamp.replace(tzinfo=timezone.utc)
    age_days = (now - post_timestamp).days
    if age_days <= 30:
        return 1.0
    if age_days <= 90:
        return 0.8
    if age_days <= 180:
        return 0.5
    return 0.2


# ── CLAUDE VISION ─────────────────────────────────────────────────────────────
def classify_image(image_bytes: bytes, account: str) -> Optional[dict]:
    try:
        import anthropic
    except ImportError:
        logger.error("anthropic no instalado — pip install anthropic")
        return None

    if len(image_bytes) > MAX_IMAGE_MB * 1024 * 1024:
        logger.debug("Imagen demasiado grande, omitiendo")
        return None

    client = anthropic.Anthropic()
    try:
        img_b64 = base64.standard_b64encode(image_bytes).decode()
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",   # Haiku: mismo análisis, 10x más barato
            max_tokens=700,
            system=CLASSIFY_SYSTEM,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}},
                    {"type": "text", "text": CLASSIFY_PROMPT},
                ],
            }],
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning("[%s] Error JSON en clasificación: %s", account, e)
        return None
    except Exception as e:
        logger.warning("[%s] Error Claude Vision: %s", account, e)
        return None


# ── CLASIFICACIÓN LIGERA (solo ángulo — para slides 2+ de carrusel) ──────────
def classify_image_angle(image_bytes: bytes, account: str, main_clf: dict) -> Optional[dict]:
    """Prompt mínimo para detectar el ángulo de slides adicionales del carrusel."""
    try:
        import anthropic
    except ImportError:
        return None

    if len(image_bytes) > MAX_IMAGE_MB * 1024 * 1024:
        return None

    client = anthropic.Anthropic()
    ctx = f"Corte: {main_clf.get('cut_name_en', '?')}. Edad: {main_clf.get('client_age_group', '?')}."
    try:
        img_b64 = base64.standard_b64encode(image_bytes).decode()
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=120,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}},
                    {"type": "text", "text": (
                        f"Contexto: {ctx}\n"
                        "¿Desde qué ángulo está tomada esta foto de barbería?\n"
                        'Responde SOLO JSON: {"photo_angle":"front|side_left|side_right|back|detail|unknown",'
                        '"photo_quality":0.0,"is_haircut_result":true}'
                    )},
                ],
            }],
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except Exception as e:
        logger.warning("[%s] Error classify_angle: %s", account, e)
        return None


# ── LOGIN INSTAGRAM ───────────────────────────────────────────────────────────
def get_instaloader():
    try:
        import instaloader
    except ImportError:
        logger.error("instaloader no instalado — pip install instaloader")
        return None

    username = os.environ.get("INSTAGRAM_USERNAME", "").strip()
    password = os.environ.get("INSTAGRAM_PASSWORD", "").strip()

    L = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        quiet=True,
        max_connection_attempts=1,  # Falla inmediato en 429 — sin esperar 30 min
        request_timeout=30,
        sleep=True,
        compress_json=False,
    )

    if not username:
        logger.warning("Sin credenciales — modo anónimo (rate limit agresivo)")
        return L

    try:
        L.load_session_from_file(username, str(SESSION_FILE))
        logger.info("Sesión Instagram cargada para @%s", username)
        return L
    except Exception:
        pass

    logger.info("Haciendo login en Instagram como @%s…", username)
    try:
        L.login(username, password)
        SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        L.save_session_to_file(str(SESSION_FILE))
        logger.info("Login OK — sesión guardada")
    except Exception as e:
        logger.error("Login fallido: %s", e)

    return L


# ── SCRAPING DE UNA CUENTA ───────────────────────────────────────────────────
def scrape_account(
    account: str,
    account_meta: dict,
    max_posts: int,
    state: dict,
    L=None,
    dry_run: bool = False,
    save_images: bool = False,
    curated_only: bool = False,
) -> list[dict]:
    try:
        import instaloader
        import requests as req
    except ImportError:
        logger.error("instaloader/requests no instalados")
        return []

    if L is None:
        L = get_instaloader()

    demo   = account_meta.get("demographic", "mixto")
    region = account_meta.get("region", "España")
    logger.info("── @%s  [%s · %s] ──", account, demo, region)

    new_refs: list[dict] = []
    processed = 0

    # Cargar perfil — cuenta como 1 request
    if not budget_ok(state):
        logger.warning("Presupuesto diario agotado — parando")
        return []

    try:
        profile = instaloader.Profile.from_username(L.context, account)
        charge_request(state, 1)
    except Exception as e:
        msg = str(e)
        if "429" in msg:
            logger.warning("[%s] 429 al cargar perfil — guardando estado y parando", account)
            state["last_429"] = datetime.now(timezone.utc).isoformat()
            save_state(state)
            return []
        logger.error("[%s] No se pudo cargar el perfil: %s", account, e)
        return []

    logger.info("[%s] %d posts · procesando hasta %d", account, profile.mediacount, max_posts)

    for post in profile.get_posts():
        if processed >= max_posts:
            break

        if not budget_ok(state):
            logger.warning("Presupuesto diario agotado a mitad de @%s — guardando progreso", account)
            break

        shortcode = post.shortcode

        # Saltar si el primer slide ya está indexado
        if already_indexed(f"{shortcode}_0"):
            processed += 1
            continue

        # ── Obtener todas las URLs del post (carrusel o foto única) ──────────
        image_urls: list[tuple[int, str]] = []  # (slide_idx, url)
        is_carousel = False

        try:
            if getattr(post, "typename", None) == "GraphSidecar":
                is_carousel = True
                for slide_idx, node in enumerate(post.get_sidecar_nodes()):
                    if not node.is_video:
                        image_urls.append((slide_idx, node.display_url))
            elif not post.is_video:
                image_urls = [(0, post.url)]
        except Exception as e:
            logger.warning("[%s] Error leyendo carrusel %s: %s — usando foto principal", account, shortcode, e)
            if not post.is_video:
                image_urls = [(0, post.url)]

        if not image_urls:
            processed += 1
            continue

        try:
            post_date = post.date_utc
        except Exception:
            post_date = None

        t_score    = trending_score(post_date)
        carousel_n = len(image_urls)
        set_id     = shortcode
        main_clf: Optional[dict] = None  # Clasificación completa del slide 0

        for slide_idx, img_url in image_urls:
            ref_key = f"{shortcode}_{slide_idx}"
            if already_indexed(ref_key):
                continue

            if not budget_ok(state):
                break

            # Descargar imagen
            try:
                img_resp = req.get(img_url, timeout=15)
                img_resp.raise_for_status()
                image_bytes = img_resp.content
                charge_request(state, 1)
            except Exception as e:
                logger.warning("[%s] Descarga fallida %s[%d]: %s", account, shortcode, slide_idx, e)
                _wait(DELAY_POSTS)
                continue

            # Clasificar
            if slide_idx == 0:
                # Clasificación completa para el slide principal
                logger.info("[%s] Clasificando %s (carrusel:%s, slides:%d)…",
                            account, shortcode, is_carousel, carousel_n)
                clf = classify_image(image_bytes, account)
                charge_request(state, 1)

                if not clf or not clf.get("is_haircut_result"):
                    reason = (clf or {}).get("skip_reason", "?")
                    logger.debug("[%s] No es un corte: %s (%s)", account, shortcode, reason)
                    break  # Si el slide 0 no es corte, saltar el post entero

                quality = float(clf.get("photo_quality", 0))
                if quality < MIN_QUALITY:
                    logger.debug("[%s] Calidad baja (%.2f): %s", account, quality, shortcode)
                    break

                main_clf = clf
            else:
                # Clasificación ligera: solo ángulo para slides adicionales
                if main_clf is None:
                    continue
                clf = classify_image_angle(image_bytes, account, main_clf)
                charge_request(state, 1)
                if not clf or not clf.get("is_haircut_result", True):
                    logger.debug("[%s] Slide %d no es corte — omitiendo", account, slide_idx)
                    _wait(DELAY_POSTS)
                    continue
                # Hereda los datos de análisis del slide 0
                quality = float(clf.get("photo_quality", main_clf.get("photo_quality", 0.6)))

            # Modo curated-only
            is_curated = bool(main_clf.get("curated_candidate")) if main_clf else False
            if curated_only and not is_curated:
                _wait(DELAY_POSTS)
                continue

            # Guardar imagen
            ref_id: str = str(uuid.uuid4())
            image_filename: Optional[str] = None
            curated_filename: Optional[str] = None

            if save_images and not dry_run:
                image_filename = f"{ref_id}.jpg"
                (IMG_DIR / image_filename).write_bytes(image_bytes)

            if is_curated and quality >= CURATED_MIN_Q and not dry_run:
                cut_key = _slugify((main_clf or clf).get("cut_name_en", "cut"))
                curated_filename = f"{cut_key}_{ref_id[:8]}.jpg"
                curated_path = CURATED_DIR / curated_filename
                if save_images and image_filename:
                    shutil.copy(IMG_DIR / image_filename, curated_path)
                else:
                    curated_path.write_bytes(image_bytes)
                logger.info("[%s] ★ Candidato curated guardado: %s", account, curated_filename)

            cdn_url: Optional[str] = img_url

            # Ángulo detectado
            if slide_idx == 0:
                photo_angle = (main_clf or {}).get("photo_angle", "unknown")
            else:
                photo_angle = clf.get("photo_angle", "unknown")

            # Referencia base del slide 0, heredada por slides adicionales
            base = main_clf or clf
            ref = {
                "id": ref_id,
                "ref_key": ref_key,        # shortcode_slideIdx — clave única
                "set_id": set_id,          # shortcode — agrupa todos los slides del mismo post
                "slide_index": slide_idx,
                "carousel_total": carousel_n,
                "is_carousel": is_carousel,
                "photo_angle": photo_angle,

                "account": account,
                "account_demographic": demo,
                "account_region": region,
                "post_shortcode": shortcode,
                "post_url": f"https://instagram.com/p/{shortcode}/",
                "post_date": post_date.isoformat() if post_date else None,
                "image_file": image_filename,
                "instagram_cdn_url": cdn_url,
                "curated_file": curated_filename,

                "face_shape":    base.get("face_shape", "unknown"),
                "hair_texture":  base.get("hair_texture", "unknown"),
                "beard_present": base.get("beard_present", False),
                "beard_style":   base.get("beard_style"),

                "client_age_group":    base.get("client_age_group", "adulto"),
                "client_age_estimate": base.get("client_age_estimate"),

                "cut_name_en":  base.get("cut_name_en", ""),
                "cut_name_es":  base.get("cut_name_es", ""),
                "cut_type":     base.get("cut_type", "otro"),
                "fade_level":   base.get("fade_level"),
                "top_style":    base.get("top_style"),
                "length_on_top": base.get("length_on_top"),

                "is_trending_spain": base.get("is_trending_spain", False),
                "trending_reason":   base.get("trending_reason", ""),
                "trending_score":    t_score,

                "is_nuca_shot":      base.get("is_nuca_shot", False),
                "has_face_visible":  base.get("has_face_visible", True),
                "curated_candidate": is_curated,

                "skin_tone": base.get("skin_tone", "unknown"),

                "maintenance_level":  base.get("maintenance_level", "medio"),
                "style_level":        base.get("style_level", "moderno"),
                "why_this_works":     base.get("why_this_works", ""),
                "barbershop_technique": base.get("barbershop_technique", ""),
                "what_to_avoid":      base.get("what_to_avoid", ""),

                "photo_quality": quality,
                "tags": base.get("tags", []),
                "indexed_at": datetime.now(timezone.utc).isoformat(),
            }

            new_refs.append(ref)
            angle_tag = f"[{photo_angle}]" if photo_angle != "unknown" else ""
            age_tag   = base.get("client_age_group", "?")
            trend     = "📈" if base.get("is_trending_spain") else "  "
            curated_tag = " ★" if is_curated else ""
            logger.info(
                "[%s] ✓ %s%s %s | %s | %s | edad:%s | q=%.2f%s",
                account, trend, shortcode,
                f"[{slide_idx}/{carousel_n-1}]{angle_tag}",
                ref["face_shape"],
                ref["cut_name_es"] or ref["cut_name_en"],
                age_tag, quality, curated_tag,
            )

            if not dry_run:
                insert_ref(ref)
                new_refs = new_refs[:-1]  # Ya guardado en DB en tiempo real

            _wait(DELAY_POSTS)

        processed += 1
        if is_carousel and carousel_n > 1:
            logger.info("[%s] Set carrusel: %s — %d ángulos procesados", account, shortcode, carousel_n)

    # dry_run: los refs se acumularon en new_refs (no se guardaron en tiempo real)
    if dry_run and new_refs:
        logger.info("[DRY-RUN] %d referencias que se habrían guardado", len(new_refs))

    logger.info("[%s] Fin. Referencias añadidas al índice esta sesión.", account)
    return new_refs


# ── HELPERS ──────────────────────────────────────────────────────────────────
def _wait(delay_range: tuple) -> None:
    t = random.uniform(*delay_range)
    logger.debug("Esperando %.0f s…", t)
    time.sleep(t)


def _slugify(text: str) -> str:
    import re
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")[:40]


# ── BÚSQUEDA EN DB (usada por image_gen_service y references.py) ──────────────
_TONE_ORDER = ["claro", "medio", "oscuro", "muy_oscuro"]


def find_references(
    face_shape: str,
    cut_name: str,
    limit: int = 3,
    require_image: bool = True,
    age_group: Optional[str] = None,
    trending_only: bool = False,
    prefer_angle: Optional[str] = None,
    skin_tone: Optional[str] = None,   # "claro"|"medio"|"oscuro"|"muy_oscuro" — filtra por tono de piel
) -> list[dict]:
    """
    Busca referencias en SQLite. SQL pre-filtra; Python post-puntúa por:
      face_shape (2.0) + token-overlap corte (0.5/token) + trending (0.5)
      + quality (0.5) + angle match (1.0) + skin_tone exact (0.8) + carousel (0.3).
    Devuelve conjuntos diversos (evita que todos vengan del mismo post).
    """
    clauses: list[str] = []
    params: list = []

    if require_image:
        clauses.append("(image_file IS NOT NULL OR instagram_cdn_url IS NOT NULL)")
    if trending_only:
        clauses.append("is_trending_spain = 1")
    if age_group:
        clauses.append("client_age_group = ?")
        params.append(age_group)
    if skin_tone and skin_tone in _TONE_ORDER:
        idx = _TONE_ORDER.index(skin_tone)
        adjacent = {skin_tone, "unknown"}
        if idx > 0:
            adjacent.add(_TONE_ORDER[idx - 1])
        if idx < len(_TONE_ORDER) - 1:
            adjacent.add(_TONE_ORDER[idx + 1])
        placeholders = ",".join("?" * len(adjacent))
        clauses.append(f"skin_tone IN ({placeholders})")
        params.extend(list(adjacent))

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"SELECT * FROM barber_refs {where}"

    try:
        with _db() as con:
            rows = con.execute(sql, params).fetchall()
    except Exception:
        return []

    cut_norm = cut_name.lower()
    scored: list[tuple[float, dict]] = []

    for row in rows:
        ref = _row_to_dict(row)
        score = 0.0

        if face_shape != "any":
            if ref.get("face_shape") == face_shape:
                score += 2.0
            elif ref.get("face_shape") in ("unknown", None):
                score += 0.5
        else:
            score += 0.5

        ref_name = (ref.get("cut_name_en", "") + " " + ref.get("cut_name_es", "")).lower()
        common = set(cut_norm.split()) & set(ref_name.split())
        score += len(common) * 0.5

        score += ref.get("trending_score", 0.3) * 0.5
        score += ref.get("photo_quality", 0) * 0.5

        if prefer_angle and ref.get("photo_angle") == prefer_angle:
            score += 1.0

        if skin_tone and ref.get("skin_tone") == skin_tone:
            score += 0.8

        if ref.get("is_carousel"):
            score += 0.3

        if score > 0.5:
            scored.append((score, ref))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = [r for _, r in scored[:limit]]

    if len(results) >= 2:
        seen_sets = {r.get("set_id") for r in results}
        if len(seen_sets) == 1:
            extras = [r for _, r in scored[limit:limit + 10] if r.get("set_id") not in seen_sets]
            if extras:
                results = results[:limit - 1] + extras[:1]

    return results


def build_reference_context(face_shape: str, cut_name: str) -> str:
    """Contexto de referencia para los prompts de FLUX. Prioriza tendencias España."""
    refs = find_references(face_shape, cut_name, limit=2, require_image=False)
    if not refs:
        return ""
    parts = []
    for ref in refs:
        if ref.get("barbershop_technique"):
            parts.append(ref["barbershop_technique"])
        if ref.get("why_this_works"):
            parts.append(f"Why it works: {ref['why_this_works']}")
        if ref.get("trending_reason"):
            parts.append(f"Trending: {ref['trending_reason']}")
    return "Real barbershop reference (Spain): " + " | ".join(parts[:3]) if parts else ""


# ── MAIN ─────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Barber Instagram Reference Agent")
    parser.add_argument("--accounts", nargs="*", help="Handles sin @ (sobreescribe accounts.json)")
    parser.add_argument("--max-posts", type=int, default=15, help="Máx posts por cuenta (default: 15)")
    parser.add_argument("--save-images", action="store_true", help="Guarda imágenes en images/")
    parser.add_argument("--dry-run", action="store_true", help="Clasifica sin escribir nada")
    parser.add_argument("--curated-only", action="store_true", help="Solo guarda candidatos a curated/ (fotos nuca)")
    parser.add_argument("--status", action="store_true", help="Muestra estado del agente y sale")
    args = parser.parse_args()

    state = load_state()

    if args.status:
        print(json.dumps(state, indent=2, ensure_ascii=False))
        with _db() as con:
            total = con.execute("SELECT COUNT(*) FROM barber_refs").fetchone()[0]
            age_rows = con.execute(
                "SELECT client_age_group, COUNT(*) FROM barber_refs GROUP BY client_age_group"
            ).fetchall()
            trending = con.execute(
                "SELECT COUNT(*) FROM barber_refs WHERE is_trending_spain=1"
            ).fetchone()[0]
            curated = con.execute(
                "SELECT COUNT(*) FROM barber_refs WHERE curated_candidate=1"
            ).fetchone()[0]
            tones = con.execute(
                "SELECT skin_tone, COUNT(*) FROM barber_refs GROUP BY skin_tone"
            ).fetchall()
        print(f"\nReferencias totales: {total}")
        print(f"Por edad: { {r[0]: r[1] for r in age_rows} }")
        print(f"En tendencia España: {trending}")
        print(f"Candidatos curated/: {curated}")
        print(f"Por tono de piel: { {r[0]: r[1] for r in tones} }")
        return

    if not budget_ok(state):
        logger.warning(
            "Presupuesto diario agotado (%d/%d peticiones). Reinicia mañana.",
            state["requests_today"], DAILY_BUDGET,
        )
        sys.exit(0)

    # Cuentas
    if args.accounts:
        accounts = [{"handle": a.lstrip("@"), "demographic": "mixto", "region": "España"} for a in args.accounts]
    else:
        if not ACCOUNTS_PATH.exists():
            logger.error("barber_accounts.json no encontrado")
            sys.exit(1)
        config = json.loads(ACCOUNTS_PATH.read_text(encoding="utf-8"))
        accounts = config.get("accounts", [])

    if not accounts:
        logger.error("No hay cuentas para procesar")
        sys.exit(1)

    logger.info("=== Barber Instagram Agent ===")
    logger.info("Presupuesto restante hoy: %d / %d", DAILY_BUDGET - state["requests_today"], DAILY_BUDGET)
    logger.info("Cuentas: %d | Max posts: %d | Save images: %s | Curated only: %s",
                len(accounts), args.max_posts, args.save_images, args.curated_only)

    L = get_instaloader()
    total_new = 0

    # Omitir cuentas ya procesadas hoy
    accounts_to_run = [
        a for a in accounts
        if a["handle"] not in state.get("accounts_done", [])
    ]
    logger.info("Cuentas pendientes hoy: %d / %d", len(accounts_to_run), len(accounts))

    for i, acc_meta in enumerate(accounts_to_run):
        if not budget_ok(state):
            logger.warning("Presupuesto agotado — parando. Reanudar mañana.")
            break

        handle = acc_meta["handle"]
        new_refs = scrape_account(
            handle, acc_meta, args.max_posts, state,
            L, args.dry_run, args.save_images, args.curated_only,
        )
        total_new += len(new_refs)
        state.setdefault("accounts_done", []).append(handle)
        save_state(state)

        if i < len(accounts_to_run) - 1 and budget_ok(state):
            delay = random.uniform(*DELAY_ACCOUNTS)
            logger.info("Esperando %.0f min antes de la siguiente cuenta…", delay / 60)
            time.sleep(delay)

    # Actualizar accounts.json con total desde DB
    total_in_db = count_refs()
    if not args.dry_run and ACCOUNTS_PATH.exists():
        config = json.loads(ACCOUNTS_PATH.read_text(encoding="utf-8"))
        config["last_run"] = datetime.now(timezone.utc).isoformat()
        config["total_references"] = total_in_db
        ACCOUNTS_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info("=== Fin — %d nuevas referencias añadidas. Total en DB: %d ===", total_new, total_in_db)
    logger.info("Peticiones usadas hoy: %d / %d", state["requests_today"], DAILY_BUDGET)


if __name__ == "__main__":
    main()
