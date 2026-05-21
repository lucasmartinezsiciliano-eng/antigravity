#!/usr/bin/env python3
"""
Forge — Stack Intelligence Agent
Radar diario de tech/IA para optimizar el stack de Lucas y reducir costes.
Usa Claude Haiku via Anthropic SDK con tool use nativo.
"""
import sys
import os
from datetime import datetime
from pathlib import Path

# Añadir shared al path
sys.path.insert(0, str(Path(__file__).parent.parent))

import anthropic
from shared.tools import web_search, fetch_page, read_file, append_file, write_file
from shared.telegram import send as telegram_send, error_alert

# ── Rutas ───────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent.parent
IDENTITY_FILE   = Path(__file__).parent / "IDENTITY.md"
CALIBRATION     = BASE / "INTEL-CALIBRATION.md"
FEEDBACK_LOG    = BASE / "INTEL-FEEDBACK-LOG.md"
LEARNINGS       = Path(__file__).parent / "LEARNINGS.md"
REPORTS_DIR     = Path(__file__).parent / "reports"

TODAY      = datetime.now().strftime("%d/%m/%Y")
TODAY_KEY  = datetime.now().strftime("%Y%m%d")
MAX_TURNS  = 12   # máximo ciclos tool-use


# ── Tool definitions para Claude ────────────────────────────────────────────
TOOLS = [
    {
        "name": "web_search",
        "description": (
            "Busca en internet noticias, releases y novedades técnicas de hoy. "
            "Usa búsquedas específicas: 'site:github.com/ollama releases', "
            "'huggingface new models today', 'localLLaMA new model 2024', etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Query de búsqueda"},
                "freshness": {
                    "type": "string",
                    "enum": ["pd", "pw", "pm"],
                    "description": "pd=último día, pw=última semana, pm=último mes",
                    "default": "pd",
                },
                "num_results": {"type": "integer", "default": 7},
            },
            "required": ["query"],
        },
    },
    {
        "name": "fetch_page",
        "description": "Lee el contenido de una URL concreta (GitHub releases, Hugging Face card, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "max_chars": {"type": "integer", "default": 3000},
            },
            "required": ["url"],
        },
    },
    {
        "name": "write_learnings",
        "description": (
            "Escribe una entrada al LEARNINGS.md al final de la sesión. "
            "Llamar UNA sola vez al final con el resumen completo de la sesión."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "entry": {"type": "string", "description": "Entrada a añadir (markdown)"},
            },
            "required": ["entry"],
        },
    },
]


# ── System prompt ────────────────────────────────────────────────────────────
def build_system_prompt() -> str:
    identity     = read_file(IDENTITY_FILE, "Eres forge, agente de stack intelligence.")
    calibration  = read_file(CALIBRATION, "Sin calibración aún.")
    learnings    = read_file(LEARNINGS, "")
    feedback     = read_file(FEEDBACK_LOG, "")

    return f"""{identity}

---
## SESIÓN DE HOY: {TODAY}

### CALIBRACIÓN ACTUAL (pesos de fuentes + perfil de Lucas):
{calibration[:2500]}

### MIS APRENDIZAJES ANTERIORES:
{learnings[-1500:] if learnings else "Primera sesión. Sin datos previos."}

### FEEDBACK RECIENTE DE LUCAS:
{feedback[-2000:] if feedback else "Sin feedback aún."}
---

Ejecuta tu misión completa: busca en las fuentes prioritarias, evalúa señales contra el stack actual, genera el informe FORGE en el formato especificado. Al finalizar, llama a write_learnings con el resumen de sesión.
"""


# ── Agentic loop ─────────────────────────────────────────────────────────────
def run() -> str | None:
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": f"Ejecuta la misión forge para hoy {TODAY}."}]

    for turn in range(MAX_TURNS):
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            system=build_system_prompt(),
            tools=TOOLS,
            messages=messages,
        )

        # Acumular respuesta del asistente
        messages.append({"role": "assistant", "content": response.content})

        # Procesar tool calls
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            name  = block.name
            inp   = block.input
            result_text = ""

            if name == "web_search":
                result_text = web_search(
                    inp["query"],
                    inp.get("num_results", 7),
                    inp.get("freshness", "pd"),
                )
            elif name == "fetch_page":
                result_text = fetch_page(inp["url"], inp.get("max_chars", 3000))
            elif name == "write_learnings":
                entry = f"\n[{TODAY}] {inp['entry']}"
                append_file(LEARNINGS, entry)
                result_text = "LEARNINGS.md actualizado."

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result_text,
            })

        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        else:
            # Sin más tool calls → respuesta final
            for block in response.content:
                if hasattr(block, "text") and block.text.strip():
                    return block.text
            break

    return None


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        report = run()
        if not report:
            raise RuntimeError("El agente no generó ningún informe.")

        # Guardar informe
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        report_path = REPORTS_DIR / f"forge-{TODAY_KEY}.md"
        write_file(report_path, report)

        # Enviar digest a Telegram (primeras 900 chars para no saturar)
        digest = report[:900]
        if len(report) > 900:
            digest += "\n…_(ver informe completo)_"
        telegram_send(f"🔧 *FORGE {datetime.now().strftime('%d/%m')}*\n\n{digest}")

        print(f"[forge] OK — informe guardado en {report_path}")

    except Exception as exc:
        error_alert("forge", str(exc))
        print(f"[forge] ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
