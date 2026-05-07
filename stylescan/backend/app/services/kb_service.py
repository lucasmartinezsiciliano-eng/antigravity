"""
StyleScan — Knowledge Base Service

Loads the structured haircut knowledge base for a given face shape
and injects the most relevant + trending cuts into Claude's prompt.

KB structure:
  knowledge_base/{face_shape}.json         — static per-shape recommendations
  knowledge_base/trending_index.json       — updated weekly by trend_worker.py
  knowledge_base/spain_trends_2024_2025.json — Spain-specific trending catalogue
  knowledge_base/visagismo/advanced_visagismo.json — expert visagismo rules
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

KB_DIR = Path(__file__).parent.parent.parent / "knowledge_base"
_SPAIN_TRENDS_PATH = KB_DIR / "spain_trends_2024_2025.json"
_ADVANCED_VISAGISMO_PATH = KB_DIR / "visagismo" / "advanced_visagismo.json"

# Weight line position by face shape (Fernand Aubry method)
_WEIGHT_LINE_POSITION: dict[str, str] = {
    "round":    "alta",
    "heart":    "alta",
    "triangle": "alta",
    "oval":     "media",
    "square":   "media",
    "diamond":  "media",
    "oblong":   "baja",
}

# Error keywords that signal relevance to a face shape
_SHAPE_ERROR_KEYWORDS: dict[str, list[str]] = {
    "round":    ["redond"],
    "square":   ["cuadrad"],
    "oblong":   ["oblong", "alargad"],
    "heart":    ["corazón", "heart"],
    "triangle": ["triangul"],
    "diamond":  ["diamante"],
    "oval":     [],
}

# Always-relevant error IDs regardless of face shape
_ALWAYS_RELEVANT_ERRORS = {"error-006", "error-011"}  # asimetría + pelo fino/grueso


def _load_json(path: Path) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("KB load failed (%s): %s", path, e)
        return None


def get_kb_context(face_shape: str, limit: int = 4) -> str:
    """
    Returns a formatted string with:
    - Top cuts from the static KB for this face shape
    - Currently trending cuts from the weekly-updated index
    """
    shape_data = _load_json(KB_DIR / f"{face_shape}.json")
    trending_data = _load_json(KB_DIR / "trending_index.json")

    if not shape_data:
        return ""

    cuts = shape_data.get("cuts", [])
    cuts_sorted = sorted(cuts, key=lambda c: c.get("trend_score", 0), reverse=True)
    top_cuts = cuts_sorted[:limit]

    trending_block = ""
    if trending_data and trending_data.get("last_updated"):
        shape_trends = trending_data.get("by_face_shape", {}).get(face_shape, [])
        global_trends = trending_data.get("global_trends", [])

        trend_lines = []
        for t in (shape_trends + global_trends)[:4]:
            name = t.get("nombre_en") or t.get("style", "")
            score = t.get("trend_score", 0)
            desc = t.get("trend_context", "")
            if name:
                trend_lines.append(f"  • {name} (score {score:.0%}){' — ' + desc if desc else ''}")

        if trend_lines:
            month = trending_data.get("month", "")
            trending_block = (
                f"\nTENDENCIAS ACTUALES ({month}) — úsalas para orientar los nombres y referencias:\n"
                + "\n".join(trend_lines)
            )

    kb_lines = []
    for cut in top_cuts:
        kb_lines.append(
            f"  • {cut['nombre_en']} — {cut.get('why_works_short', '')} "
            f"[técnica: {cut.get('technique', '')}]"
        )

    if not kb_lines:
        return trending_block

    return (
        "\n════ BASE DE CONOCIMIENTO — CORTES VALIDADOS PARA ESTA FORMA FACIAL ════\n"
        "Los siguientes cortes están científicamente validados para esta forma. "
        "Inspírate en ellos para tus recomendaciones (no copies literalmente — adapta a los ratios del usuario):\n"
        + "\n".join(kb_lines)
        + trending_block
        + "\n"
    )


def get_spain_trends_context(face_shape: str, limit: int = 4) -> str:
    """
    Returns top Spain-trending cuts that are visagismo-compatible with face_shape.
    Filtered by formas_ideales and no_recomendado from the Spain catalogue.
    """
    data = _load_json(_SPAIN_TRENDS_PATH)
    if not data:
        return ""

    cuts = data.get("cuts", [])

    relevant = []
    for cut in cuts:
        vis = cut.get("visagismo", {})
        formas_ideales = vis.get("formas_ideales", [])
        no_recomendado = vis.get("no_recomendado", [])
        if face_shape in formas_ideales and face_shape not in no_recomendado:
            relevant.append(cut)

    top = sorted(relevant, key=lambda c: c.get("trend_score", 0), reverse=True)[:limit]
    if not top:
        return ""

    lines = []
    for cut in top:
        nombre_es = cut.get("nombre_es", "")
        nombre_en = cut.get("nombre_en", "")
        trend = cut.get("trend_score", 0)
        tendencia = cut.get("tendencia_2024_2025", "")
        desc = cut.get("descripcion_tecnica", {})
        instrucciones = cut.get("instrucciones_barbero", "")

        fade_type = desc.get("fade_type", "")
        tope_largo = desc.get("tope_largo", "")
        tecnica_tope = desc.get("tecnica_tope", "")

        lines.append(
            f"  • {nombre_es} / {nombre_en} (popularidad España: {trend:.0%})\n"
            f"    {tendencia[:160]}\n"
            f"    Técnica: {fade_type}. Tope: {tope_largo}. {tecnica_tope[:100]}\n"
            f"    Para el barbero: «{instrucciones[:220]}»"
        )

    return (
        f"\n════ TENDENCIAS ESPAÑA 2024-2025 — COMPATIBLES CON FORMA {face_shape.upper()} ════\n"
        "Cortes más pedidos en barberías españolas que funcionan bien para esta forma facial.\n"
        "Úsalos para nombres, referencias culturales y frases del barbero:\n"
        + "\n".join(lines)
        + "\n"
    )


def get_advanced_visagismo_context(face_shape: str) -> str:
    """
    Returns expert visagismo guidance for this face shape:
    beard integration, weight line position, and critical errors to avoid.
    """
    data = _load_json(_ADVANCED_VISAGISMO_PATH)
    if not data:
        return ""

    parts: list[str] = []

    # --- Beard guidance ---
    beard_data = (
        data.get("barba_y_corte", {})
            .get("formas_faciales", {})
            .get(face_shape, {})
    )
    if beard_data:
        barba_ideal = beard_data.get("barba_ideal", "")
        efecto = beard_data.get("efecto_corrector") or beard_data.get("barba_potenciadora", "")
        barba_evitar = beard_data.get("barba_a_evitar", "")
        prioridad = beard_data.get("prioridad", "")

        beard_lines = [f"  Barba ideal: {barba_ideal}"]
        if efecto:
            beard_lines.append(f"  Efecto corrector: {efecto}")
        if barba_evitar:
            beard_lines.append(f"  Evitar: {barba_evitar}")
        if prioridad:
            beard_lines.append(f"  ⚠ PRIORIDAD: {prioridad}")
        parts.append("BARBA (sistema integrado corte+barba):\n" + "\n".join(beard_lines))

    # --- Weight line position ---
    linea_peso = data.get("proporcion_aurea", {}).get("linea_de_peso", {})
    if linea_peso:
        posiciones = linea_peso.get("posiciones", {})
        errores_peso = linea_peso.get("errores_comunes", [])
        pos_key = _WEIGHT_LINE_POSITION.get(face_shape, "media")
        pos_desc = posiciones.get(pos_key, "")

        peso_lines = [f"  Posición óptima: {pos_key.upper()} — {pos_desc}"]
        for e in errores_peso[:2]:
            peso_lines.append(f"  ✗ Error típico: {e}")
        parts.append("LÍNEA DE PESO (zona de máximo volumen):\n" + "\n".join(peso_lines))

    # --- Critical errors ---
    errores = data.get("errores_comunes", {}).get("errores", [])
    keywords = _SHAPE_ERROR_KEYWORDS.get(face_shape, [])

    relevant_errors: list[dict] = []
    seen_ids: set[str] = set()
    for e in errores:
        eid = e.get("id", "")
        text = (e.get("nombre", "") + e.get("descripcion", "")).lower()
        if any(k in text for k in keywords) and eid not in seen_ids:
            relevant_errors.append(e)
            seen_ids.add(eid)
    for e in errores:
        eid = e.get("id", "")
        if eid in _ALWAYS_RELEVANT_ERRORS and eid not in seen_ids:
            relevant_errors.append(e)
            seen_ids.add(eid)

    if relevant_errors[:4]:
        error_lines = []
        for e in relevant_errors[:4]:
            regla = e.get("regla_absoluta") or e.get("solucion", "")
            error_lines.append(
                f"  ✗ {e['nombre']}: {e.get('consecuencia', '')} → {regla[:160]}"
            )
        parts.append("ERRORES CRÍTICOS A EVITAR:\n" + "\n".join(error_lines))

    if not parts:
        return ""

    return (
        "\n════ VISAGISMO AVANZADO — GUÍA TÉCNICA ════\n"
        + "\n\n".join(parts)
        + "\n"
    )
