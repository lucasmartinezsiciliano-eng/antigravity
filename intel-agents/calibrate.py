#!/usr/bin/env python3
"""
Intel Calibrator — ejecutar cada domingo.
Lee el INTEL-FEEDBACK-LOG.md (o Google Sheet) de la semana,
recalibra los pesos de fuentes y actualiza INTEL-CALIBRATION.md.
"""
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

import anthropic
from shared.tools import read_file, write_file, append_file
from shared.telegram import send as telegram_send

BASE             = Path(__file__).parent
CALIBRATION_FILE = BASE / "INTEL-CALIBRATION.md"
FEEDBACK_LOG     = BASE / "INTEL-FEEDBACK-LOG.md"
FORGE_LEARNINGS  = BASE / "forge" / "LEARNINGS.md"
HORIZON_LEARNINGS = BASE / "horizon" / "LEARNINGS.md"

TODAY = datetime.now().strftime("%d/%m/%Y")
WEEK_NUM = datetime.now().isocalendar()[1]


def parse_feedback_log(log_text: str) -> list[dict]:
    """Parsea las entradas del INTEL-FEEDBACK-LOG.md."""
    entries = []
    blocks = re.split(r"^---$", log_text, flags=re.MULTILINE)
    for block in blocks:
        entry = {}
        for field in ["DATE", "AGENT", "SIGNAL_ID", "REACTION", "COMMENT", "ACTION_TAKEN"]:
            m = re.search(rf"^{field}:\s*(.+)$", block, re.MULTILINE)
            if m:
                entry[field.lower()] = m.group(1).strip()
        if entry.get("signal_id"):
            entries.append(entry)
    return entries


def run_calibration():
    feedback_text = read_file(FEEDBACK_LOG, "")
    calibration   = read_file(CALIBRATION_FILE, "")
    forge_log     = read_file(FORGE_LEARNINGS, "")
    horizon_log   = read_file(HORIZON_LEARNINGS, "")

    entries = parse_feedback_log(feedback_text)

    if not entries:
        telegram_send(
            f"📊 *Intel Calibración semana {WEEK_NUM}*\n\n"
            "Sin feedback registrado esta semana. Los pesos se mantienen.\n"
            "_Reacciona al digest diario con 👍1 👎2 ⚡3 para que el sistema aprenda._"
        )
        return

    # Estadísticas básicas
    total = len(entries)
    acted = sum(1 for e in entries if e.get("reaction") in ["⚡", "👍"])
    ignored = sum(1 for e in entries if e.get("reaction") == "👎")

    # Agrupar por agente
    by_agent = defaultdict(list)
    for e in entries:
        by_agent[e.get("agent", "unknown")].append(e)

    # Preparar contexto para Claude
    client = anthropic.Anthropic()
    system = """Eres el calibrador del sistema de inteligencia diaria Intel (forge + horizon).
Tu rol es analizar el feedback de la semana y actualizar el archivo INTEL-CALIBRATION.md.

Debes:
1. Calcular qué tipos de señales/oportunidades actúa el usuario vs ignora
2. Identificar anti-patrones (ignorados ≥2 veces del mismo tipo)
3. Reforzar patrones exitosos (actuados ≥2 veces del mismo tipo)
4. Proponer pesos actualizados para las fuentes
5. Generar un INTEL-CALIBRATION.md actualizado

Sé específico y orientado a datos. El calibrador actualizado debe mejorar el ratio señal/ruido de la semana que viene."""

    prompt = f"""Semana {WEEK_NUM} — {TODAY}

FEEDBACK DE ESTA SEMANA ({total} entradas):
{feedback_text[-3000:]}

APRENDIZAJES DE FORGE ESTA SEMANA:
{forge_log[-1000:]}

APRENDIZAJES DE HORIZON ESTA SEMANA:
{horizon_log[-1000:]}

CALIBRACIÓN ACTUAL:
{calibration[:3000]}

Estadísticas rápidas:
- Total señales con feedback: {total}
- Actuadas (👍 + ⚡): {acted} ({round(acted/total*100) if total else 0}%)
- Ignoradas (👎): {ignored} ({round(ignored/total*100) if total else 0}%)

Por agente: forge={len(by_agent.get('forge', []))} | horizon={len(by_agent.get('horizon', []))}

Genera el INTEL-CALIBRATION.md actualizado completo. Mantén el formato del archivo actual pero actualiza:
1. Los pesos de fuentes con datos reales de esta semana
2. La sección PERFIL DE GUSTO con nuevos patrones detectados
3. Los ANTI-PATRONES si hay nuevos
4. El HISTORIAL DE CALIBRACIÓN (añadir fila de esta semana)
5. Actualizar last_updated y calibrated_weeks

Devuelve SOLO el contenido del archivo INTEL-CALIBRATION.md actualizado, sin explicaciones extra."""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )

    new_calibration = response.content[0].text.strip()
    write_file(CALIBRATION_FILE, new_calibration)

    # Añadir resumen en el feedback log
    summary = (
        f"\n\n## CALIBRACIÓN SEMANA {WEEK_NUM} — {TODAY}\n"
        f"Total feedback: {total} | Actuadas: {acted} | Ignoradas: {ignored}\n"
        f"Ratio señal/ruido: {round(acted/total*100) if total else 0}%\n"
        f"INTEL-CALIBRATION.md actualizado."
    )
    append_file(FEEDBACK_LOG, summary)

    telegram_send(
        f"📊 *Intel Calibración semana {WEEK_NUM}*\n\n"
        f"✅ {acted}/{total} señales fueron útiles ({round(acted/total*100) if total else 0}%)\n"
        f"❌ {ignored} ignoradas — anti-patrones actualizados\n\n"
        f"Los agentes de la próxima semana serán más precisos."
    )
    print(f"[calibrate] OK — semana {WEEK_NUM} calibrada.")


if __name__ == "__main__":
    try:
        run_calibration()
    except Exception as exc:
        from shared.telegram import error_alert
        error_alert("calibrator", str(exc))
        print(f"[calibrate] ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
