"""
StyleScan — Visagismo Professional Engine

Takes raw FaceMetrics and produces a structured visagismo analysis:
  - Primary face shape correction goal
  - List of detected secondary defects (from biometric thresholds)
  - Conflict resolutions from the shape×defect matrix
  - Prioritized list of techniques (mandatory, recommended, forbidden)
  - A formatted block ready to be injected into Claude's prompt

This replaces the old simple KB lookup. The output is a rich, specific
instruction set that Claude uses to generate medically-informed recommendations.

Reference: Fernand Aubry visagisme method + modern aesthetic research
"""

import json
import logging
from pathlib import Path
from typing import NamedTuple

from app.services.face_analysis import FaceMetrics

logger = logging.getLogger(__name__)

_VIS_DIR = Path(__file__).parent.parent.parent / "knowledge_base" / "visagismo"


def _load(filename: str) -> dict:
    try:
        with open(_VIS_DIR / filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("visagismo load failed (%s): %s", filename, e)
        return {}


class VisagismoAnalysis(NamedTuple):
    shape: str
    shape_goal: str
    detected_defects: list[str]       # IDs from defects.json
    defect_labels: list[str]          # Human-readable labels
    conflict_resolutions: list[str]   # From feature_matrix
    mandatory_techniques: list[str]
    forbidden_techniques: list[str]
    priority_notes: list[str]         # High-priority custom notes
    formatted_block: str              # Ready for Claude injection


def _detect_defects(metrics: FaceMetrics) -> list[str]:
    """Map biometric thresholds to defect IDs."""
    defects = []

    # Forehead analysis
    if metrics.forehead_to_face_ratio > 1.05:
        defects.append("forehead_wide")
    if metrics.forehead_to_face_ratio < 0.90:
        defects.append("forehead_low")

    # Length analysis for forehead height (proxy: if very long face + high ratio)
    if metrics.length_width_ratio > 1.65 and metrics.forehead_to_face_ratio > 1.0:
        defects.append("forehead_high")

    # Jaw analysis
    if metrics.jaw_to_face_ratio < 0.88:
        defects.append("jaw_weak")
    elif metrics.jaw_to_face_ratio > 0.96:
        defects.append("jaw_strong")

    # Asymmetry
    if metrics.asymmetry_score >= 0.15:
        defects.append("asymmetry_notable")

    # fWHR proxy from length_width_ratio
    if metrics.length_width_ratio < 1.30:
        defects.append("high_fwhr")
    elif metrics.length_width_ratio > 1.70:
        defects.append("low_fwhr")

    return defects


def analyze(metrics: FaceMetrics) -> VisagismoAnalysis:
    """Full visagismo analysis from face metrics."""
    defects_db = _load("defects.json")
    shapes_db = _load("shape_rules.json")
    matrix_db = _load("feature_matrix.json")

    shape = metrics.face_shape
    detected_defect_ids = _detect_defects(metrics)

    # Shape rules
    shape_rules = shapes_db.get("shapes", {}).get(shape, {})
    shape_goal = shape_rules.get("goal", "")
    mandatory = list(shape_rules.get("mandatory_techniques", []))
    forbidden = list(shape_rules.get("forbidden_techniques", []))
    priority_notes = []

    if shape_rules.get("visagismo_priority"):
        priority_notes.append(f"[FORMA] {shape_rules['visagismo_priority']}")
    if shape_rules.get("barber_baseline"):
        priority_notes.append(f"[BARBERO] {shape_rules['barber_baseline']}")

    # Defect analysis
    defect_entries = {d["id"]: d for d in defects_db.get("defects", [])}
    defect_labels = []

    for defect_id in detected_defect_ids:
        entry = defect_entries.get(defect_id)
        if not entry:
            continue
        defect_labels.append(entry["label"])
        correction = entry.get("correction", {})

        # Add techniques from this defect
        for tech in correction.get("techniques", []):
            if tech not in mandatory:
                mandatory.append(f"[{entry['label']}] {tech}")
        for avoid in entry.get("avoid", []):
            if avoid not in forbidden:
                forbidden.append(f"[{entry['label']}] {avoid}")

        # Severity note
        if entry.get("severity") == "high_priority":
            priority_notes.append(
                f"⚠ DEFECTO PRIORITARIO — {entry['label']}: {correction.get('principle', '')}"
            )
        elif entry.get("severity") == "positive_feature":
            priority_notes.append(
                f"✓ RASGO FAVORABLE — {entry['label']}: potenciar, no corregir"
            )

    # Matrix conflict resolutions
    matrix_entries = matrix_db.get("matrix", [])
    conflict_resolutions = []
    for entry in matrix_entries:
        if entry["shape"] == shape and entry["defect"] in detected_defect_ids:
            conflict_resolutions.append(
                f"CONFLICTO [{entry['defect']}]: {entry['conflict']} → {entry['final_instruction']}"
            )

    # Build the formatted block for Claude
    formatted_block = _build_block(
        shape=shape,
        shape_goal=shape_goal,
        detected_defect_ids=detected_defect_ids,
        defect_labels=defect_labels,
        conflict_resolutions=conflict_resolutions,
        mandatory=mandatory,
        forbidden=forbidden,
        priority_notes=priority_notes,
    )

    return VisagismoAnalysis(
        shape=shape,
        shape_goal=shape_goal,
        detected_defects=detected_defect_ids,
        defect_labels=defect_labels,
        conflict_resolutions=conflict_resolutions,
        mandatory_techniques=mandatory,
        forbidden_techniques=forbidden,
        priority_notes=priority_notes,
        formatted_block=formatted_block,
    )


def _build_block(
    shape: str,
    shape_goal: str,
    detected_defect_ids: list[str],
    defect_labels: list[str],
    conflict_resolutions: list[str],
    mandatory: list[str],
    forbidden: list[str],
    priority_notes: list[str],
) -> str:
    lines = [
        "════ ANÁLISIS DE VISAGISMO PROFESIONAL ════",
        "",
        f"FORMA FACIAL: {shape.upper()}",
        f"OBJETIVO CORRECTOR: {shape_goal}",
        "",
    ]

    if defect_labels:
        lines.append("CARACTERÍSTICAS SECUNDARIAS DETECTADAS:")
        for label in defect_labels:
            lines.append(f"  • {label}")
        lines.append("")

    if priority_notes:
        lines.append("PRIORIDADES ABSOLUTAS (aplicar ANTES que cualquier tendencia):")
        for note in priority_notes:
            lines.append(f"  {note}")
        lines.append("")

    if conflict_resolutions:
        lines.append("RESOLUCIÓN DE CONFLICTOS (cuando forma + defecto crean dilema técnico):")
        for res in conflict_resolutions:
            lines.append(f"  → {res}")
        lines.append("")

    if mandatory:
        lines.append("TÉCNICAS OBLIGATORIAS (deben reflejarse en los 3 cortes recomendados):")
        for tech in mandatory[:8]:  # Cap to avoid token explosion
            lines.append(f"  ✓ {tech}")
        lines.append("")

    if forbidden:
        lines.append("TÉCNICAS PROHIBIDAS (no incluir NUNCA en las recomendaciones):")
        for tech in forbidden[:6]:
            lines.append(f"  ✗ {tech}")
        lines.append("")

    lines.append(
        "INSTRUCCIÓN: Los 3 cortes recomendados DEBEN respetar todas las técnicas obligatorias "
        "y NO incluir ninguna técnica prohibida. Si hay conflicto entre tendencia y corrección, "
        "la corrección de visagismo SIEMPRE tiene prioridad. "
        "En la descripcion_favorece de cada corte, EXPLICA en términos visuales cómo este "
        "corte corrige la(s) característica(s) detectadas."
    )

    return "\n".join(lines) + "\n"
