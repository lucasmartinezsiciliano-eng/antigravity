"""
Herramientas compartidas para los agentes Intel (forge + horizon).
Web search via Brave API con fallback a DuckDuckGo.
"""
import os
import re
import requests
from datetime import datetime
from pathlib import Path


# ── Web Search ─────────────────────────────────────────────────────────────

def web_search(query: str, num_results: int = 7, freshness: str = "pd") -> str:
    """
    Busca en internet. Usa Brave API si BRAVE_API_KEY está disponible.
    freshness: pd = past day, pw = past week, pm = past month
    """
    api_key = os.environ.get("BRAVE_API_KEY")
    if api_key:
        return _brave_search(query, num_results, freshness, api_key)
    return _ddg_search(query, num_results)


def _brave_search(query: str, num_results: int, freshness: str, api_key: str) -> str:
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key,
    }
    params = {"q": query, "count": min(num_results, 10), "freshness": freshness}
    try:
        resp = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers=headers,
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        results = []
        for item in data.get("web", {}).get("results", []):
            title = item.get("title", "")
            url = item.get("url", "")
            desc = item.get("description", "")
            results.append(f"**{title}**\n{url}\n{desc}")
        return "\n\n---\n\n".join(results) if results else "Sin resultados."
    except Exception as e:
        return f"Error Brave Search: {e}"


def _ddg_search(query: str, num_results: int) -> str:
    """Fallback: DuckDuckGo HTML scraping (sin API key)."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; IntelAgent/1.0)"}
        params = {"q": query, "kl": "es-es"}
        resp = requests.get("https://html.duckduckgo.com/html/", headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        # Extraer snippets básicos del HTML
        snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', resp.text, re.DOTALL)
        titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', resp.text, re.DOTALL)
        results = []
        for i, (t, s) in enumerate(zip(titles[:num_results], snippets[:num_results])):
            t_clean = re.sub(r"<[^>]+>", "", t).strip()
            s_clean = re.sub(r"<[^>]+>", "", s).strip()
            results.append(f"**{t_clean}**\n{s_clean}")
        return "\n\n---\n\n".join(results) if results else "Sin resultados."
    except Exception as e:
        return f"Error DuckDuckGo: {e}"


def fetch_page(url: str, max_chars: int = 3000) -> str:
    """Descarga el texto plano de una URL (para leer GitHub releases, HF cards, etc.)."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; IntelAgent/1.0)"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        # Limpiar HTML básico
        text = re.sub(r"<script[^>]*>.*?</script>", " ", resp.text, flags=re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s{3,}", "\n", text)
        return text.strip()[:max_chars]
    except Exception as e:
        return f"Error al cargar {url}: {e}"


# ── File helpers ────────────────────────────────────────────────────────────

def read_file(path: Path, default: str = "") -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return default


def append_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(content.rstrip() + "\n")


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
