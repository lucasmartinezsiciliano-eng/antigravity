"""
Instagram intelligence module para los agentes Intel.
Multi-fuente: viewers públicos + Meta Graph API (cuando esté configurado) + búsquedas web.
"""
import re
import os
import json
import requests
from pathlib import Path
from shared.tools import web_search, fetch_page

# ── Configuración ──────────────────────────────────────────────────────────

BASE = Path(__file__).parent.parent
META_TOKEN_FILE = BASE / "shared" / "meta_token.txt"

INSTAGRAM_ACCOUNTS_FORGE = [
    "javiniguezoficial",   # IA tech tools en español — muy activo
    "dotcsv",              # Dot CSV — el mayor divulgador IA en español
    "alejandropiad",       # IA + productividad en español
    "theaiguy__",          # English — AI tools reviews
    "ai_for_beginners__",  # English — AI tools for non-tech
    "samwitteveenn",       # English — AI productivity workflows
]

INSTAGRAM_ACCOUNTS_HORIZON = [
    "javiniguezoficial",   # Covers AI business + tools
    "dotcsv",              # Negocios IA + tutoriales
    "emprendedorigital",   # Emprendimiento digital español
    "escuela_de_inversion",# Finanzas e inversión España
    "solopreneur_espa",    # Solopreneur español
    "businessinsider_es",  # Business Insider España
]

HASHTAGS_FORGE = [
    "inteligenciaartificial", "herramientasIA", "iatools",
    "automatizacion", "locallm", "openweights",
    "llm", "agentesIA", "promptengineering",
]

HASHTAGS_HORIZON = [
    "emprendedordigital", "negocioIA", "ganardineroconIA",
    "sidehustle", "solopreneur", "aibusiness",
    "ecommerce", "tiktokshop", "automatizacionnegocios",
    "proptech", "fintech", "hipotecas",
]


# ── Viewer público (sin login) ─────────────────────────────────────────────

def scrape_profile_picuki(username: str) -> str:
    """Obtiene posts recientes de un perfil via picuki.com (viewer sin login)."""
    url = f"https://www.picuki.com/profile/{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Referer": "https://www.google.com/",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return f"picuki.com: HTTP {resp.status_code}"
        text = resp.text
        # Extraer captions de los posts
        captions = re.findall(r'class="photo-description[^"]*"[^>]*>(.*?)</div>', text, re.DOTALL)
        if not captions:
            captions = re.findall(r'<p class="description[^"]*">(.*?)</p>', text, re.DOTALL)
        cleaned = []
        for c in captions[:10]:
            c = re.sub(r"<[^>]+>", "", c).strip()
            c = re.sub(r"\s{2,}", " ", c)
            if len(c) > 20:
                cleaned.append(c)
        if cleaned:
            return f"[picuki.com/{username}]\n" + "\n---\n".join(cleaned[:8])
        # Si no hay captions, devolver texto limpio de la página
        page_text = re.sub(r"<[^>]+>", " ", text)
        page_text = re.sub(r"\s{3,}", "\n", page_text).strip()
        return f"[picuki.com/{username}]\n{page_text[:2000]}"
    except Exception as e:
        return f"picuki.com error: {e}"


def scrape_profile_imginn(username: str) -> str:
    """Obtiene posts recientes via imginn.com (viewer sin login)."""
    url = f"https://imginn.com/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
        "Accept": "text/html",
        "Accept-Language": "es,en;q=0.9",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return f"imginn.com: HTTP {resp.status_code}"
        text = resp.text
        captions = re.findall(r'"caption":"(.*?)"', text)
        if not captions:
            captions = re.findall(r'class="desc[^"]*"[^>]*>(.*?)</[^>]+>', text, re.DOTALL)
        cleaned = []
        for c in captions[:10]:
            c = re.sub(r"<[^>]+>", "", c).replace("\\n", " ").replace('\\"', '"').strip()
            if len(c) > 20:
                cleaned.append(c)
        if cleaned:
            return f"[imginn.com/{username}]\n" + "\n---\n".join(cleaned[:8])
        page_text = re.sub(r"<[^>]+>", " ", text)
        page_text = re.sub(r"\s{3,}", "\n", page_text).strip()
        return f"[imginn.com/{username}]\n{page_text[:2000]}"
    except Exception as e:
        return f"imginn.com error: {e}"


def scrape_profile(username: str) -> str:
    """Intenta picuki → imginn → búsqueda web como fallback."""
    result = scrape_profile_picuki(username)
    if "error" not in result.lower() and len(result) > 100:
        return result
    result2 = scrape_profile_imginn(username)
    if "error" not in result2.lower() and len(result2) > 100:
        return result2
    # Fallback: búsqueda cruzada
    return web_search(f'"{username}" instagram contenido reciente IA herramienta', num_results=5, freshness="pw")


# ── Meta Graph API (cuando esté configurado) ──────────────────────────────

def get_meta_token() -> str | None:
    """Lee el token de Meta Graph API desde archivo local."""
    token = os.environ.get("META_GRAPH_TOKEN")
    if token:
        return token
    if META_TOKEN_FILE.exists():
        return META_TOKEN_FILE.read_text().strip()
    return None


def meta_api_get(endpoint: str, params: dict = None) -> dict | None:
    """Llama a Meta Graph API. Retorna dict o None si no hay token."""
    token = get_meta_token()
    if not token:
        return None
    base = "https://graph.facebook.com/v21.0"
    p = {"access_token": token, **(params or {})}
    try:
        resp = requests.get(f"{base}/{endpoint}", params=p, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def meta_search_hashtag(hashtag: str, user_id: str = None) -> str:
    """
    Busca posts recientes con un hashtag vía Meta Graph API.
    Requiere META_GRAPH_TOKEN + META_USER_ID en env o archivos.
    """
    if not user_id:
        user_id = os.environ.get("META_USER_ID", "")
    if not user_id:
        return f"META_USER_ID no configurado — usa búsqueda web para #{hashtag}"

    # Paso 1: obtener ID del hashtag
    ht_data = meta_api_get("ig-hashtag-search", {"user_id": user_id, "q": hashtag})
    if not ht_data or "data" not in ht_data:
        return f"Meta API: no se encontró #{hashtag} — {ht_data}"
    ht_id = ht_data["data"][0]["id"]

    # Paso 2: obtener posts recientes
    posts = meta_api_get(
        f"{ht_id}/recent_media",
        {"user_id": user_id, "fields": "caption,timestamp,media_type,like_count,comments_count"}
    )
    if not posts or "data" not in posts:
        return f"Meta API: sin posts para #{hashtag}"

    results = []
    for p in posts["data"][:8]:
        caption = p.get("caption", "")[:200]
        ts = p.get("timestamp", "")[:10]
        likes = p.get("like_count", "?")
        comments = p.get("comments_count", "?")
        mtype = p.get("media_type", "")
        results.append(f"[{ts}] {mtype} | ❤️{likes} 💬{comments}\n{caption}")
    return f"[Meta API #{hashtag}]\n" + "\n---\n".join(results)


# ── Búsquedas web cruzadas ─────────────────────────────────────────────────

def instagram_web_intelligence(accounts: list[str], hashtags: list[str], topic: str = "") -> str:
    """
    Estrategia multi-vector para capturar contenido Instagram sin API:
    1. Búsqueda directa Google del usuario
    2. Cross-platform: Reddit y Twitter que hablan de ese contenido
    3. Búsqueda de hashtags en múltiples plataformas
    """
    results = []

    # Accounts
    for username in accounts[:4]:
        q1 = f'"{username}" instagram (IA OR "inteligencia artificial" OR herramienta OR negocio) 2025'
        r = web_search(q1, num_results=5, freshness="pw")
        if r and "Sin resultados" not in r:
            results.append(f"=== @{username} (búsqueda directa) ===\n{r[:1000]}")

        q2 = f'site:reddit.com OR site:twitter.com "{username}" instagram'
        r2 = web_search(q2, num_results=3, freshness="pm")
        if r2 and "Sin resultados" not in r2:
            results.append(f"=== @{username} (cross-platform) ===\n{r2[:800]}")

    # Hashtags
    for ht in hashtags[:5]:
        q = f'instagram "#{ht}" (viral OR tendencia OR "best tool" OR "herramienta") 2025'
        r = web_search(q, num_results=5, freshness="pw")
        if r and "Sin resultados" not in r:
            results.append(f"=== Instagram #{ht} ===\n{r[:800]}")

    # Topic-specific
    if topic:
        q = f'instagram (reel OR post) "{topic}" viral 2025 site:reddit.com OR site:twitter.com'
        r = web_search(q, num_results=5, freshness="pw")
        if r and "Sin resultados" not in r:
            results.append(f"=== Instagram tema: {topic} ===\n{r[:800]}")

    return "\n\n".join(results) if results else "Sin señales Instagram esta ejecución."


# ── Punto de entrada para los agentes ─────────────────────────────────────

def get_instagram_intel_forge() -> str:
    """Recopila señales de Instagram para Forge (tech/IA tools)."""
    sections = []

    # 1. Intentar scraping directo de cuentas prioritarias
    for username in INSTAGRAM_ACCOUNTS_FORGE[:3]:
        data = scrape_profile(username)
        sections.append(f"--- PERFIL @{username} ---\n{data[:1200]}")

    # 2. Meta API hashtags (si hay token)
    token = get_meta_token()
    if token:
        for ht in HASHTAGS_FORGE[:3]:
            sections.append(meta_search_hashtag(ht))
    else:
        # Fallback: búsqueda web para hashtags
        for ht in HASHTAGS_FORGE[:3]:
            r = web_search(f'instagram "#{ht}" nueva herramienta IA 2025', num_results=5, freshness="pw")
            sections.append(f"--- #{ht} (web search) ---\n{r[:800]}")

    # 3. Cross-platform intelligence
    sections.append(instagram_web_intelligence(
        INSTAGRAM_ACCOUNTS_FORGE,
        HASHTAGS_FORGE,
        topic="AI tool free open source"
    ))

    return "\n\n".join(sections)


def get_instagram_intel_horizon() -> str:
    """Recopila señales de Instagram para Horizon (business/negocio)."""
    sections = []

    for username in INSTAGRAM_ACCOUNTS_HORIZON[:3]:
        data = scrape_profile(username)
        sections.append(f"--- PERFIL @{username} ---\n{data[:1200]}")

    token = get_meta_token()
    if token:
        for ht in HASHTAGS_HORIZON[:3]:
            sections.append(meta_search_hashtag(ht))
    else:
        for ht in HASHTAGS_HORIZON[:3]:
            r = web_search(f'instagram "#{ht}" negocio dinero IA 2025', num_results=5, freshness="pw")
            sections.append(f"--- #{ht} (web search) ---\n{r[:800]}")

    sections.append(instagram_web_intelligence(
        INSTAGRAM_ACCOUNTS_HORIZON,
        HASHTAGS_HORIZON,
        topic="cómo ganar dinero IA negocio 2025"
    ))

    return "\n\n".join(sections)
