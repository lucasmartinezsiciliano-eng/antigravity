#!/usr/bin/env python3
"""
Horizon — Business Intelligence Agent
Radar diario de noticias de negocio para identificar oportunidades aplicables a Lucas.
Usa Claude Haiku via Anthropic SDK con tool use nativo.
Lee la salida de forge del día para detectar sinergias.
"""
import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import anthropic
from shared.tools import web_search, fetch_page, read_file, append_file, write_file
from shared.telegram import send as telegram_send, error_alert

# ── Rutas ───────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent.parent
IDENTITY_FILE  = Path(__file__).parent / "IDENTITY.md"
CALIBRATION    = BASE / "INTEL-CALIBRATION.md"
FEEDBACK_LOG   = BASE / "INTEL-FEEDBACK-LOG.md"
LEARNINGS      = Path(__file__).parent / "LEARNINGS.md"
REPORTS_DIR    = Path(__file__).parent / "reports"
FORGE_REPORTS  = BASE / "forge" / "reports"

TODAY     = datetime.now().strftime("%d/%m/%Y")
TODAY_KEY = datetime.now().strftime("%Y%m%d")
MAX_TURNS = 12


# ── Tools ────────────────────────────────────────────────────────────────────
TOOLS = [
    {
        "name": "web_search",
        "description": (
            "Busca noticias de negocio, startups y oportunidades de mercado. "
            "Busca en Indie Hackers, Product Hunt, Hacker News, prensa española, EU-Startups. "
            "Ejemplos: 'indie hackers revenue €10k month 2024', "
            "'proptech spain startup 2024', 'product hunt top launches today'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "freshness": {
                    "type": "string",
                    "enum": ["pd", "pw", "pm"],
                    "default": "pd",
                },
                "num_results": {"type": "integer", "default": 7},
            },
            "required": ["query"],
        },
    },
    {
        "name": "fetch_page",
        "description": "Lee el contenido de una URL concreta (Indie Hackers post, Product Hunt lanzamiento, etc.).",
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
        "description": "Escribe una entrada al LEARNINGS.md al final de la sesión. Llamar UNA sola vez.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entry": {"type": "string"},
            },
            "required": ["entry"],
        },
    },
]


# ── System prompt ─────────────────────────────────────────────────────────────
def build_system_prompt() -> str:
    identity    = read_file(IDENTITY_FILE, "Eres horizon, agente de business intelligence.")
    calibration = read_file(CALIBRATION, "Sin calibración aún.")
    learnings   = read_file(LEARNINGS, "")
    feedback    = read_file(FEEDBACK_LOG, "")

    # Leer informe de forge del día (si existe) para detectar sinergias
    forge_today = FORGE_REPORTS / f"forge-{TODAY_KEY}.md"
    forge_report = read_file(forge_today, "")
    forge_context = (
        f"\n### INFORME FORGE DE HOY (busca sinergias):\n{forge_report[:1500]}"
        if forge_report else
        "\n### INFORME FORGE: No disponible aún hoy."
    )

    return f"""{identity}

---
## SESIÓN DE HOY: {TODAY}

### CALIBRACIÓN ACTUAL:
{calibration[:2500]}

### MIS APRENDIZAJES ANTERIORES:
{learnings[-1500:] if learnings else "Primera sesión."}

### FEEDBACK RECIENTE DE LUCAS:
{feedback[-2000:] if feedback else "Sin feedback aún."}
{forge_context}
---

Ejecuta tu misión completa: busca en las fuentes prioritarias, evalúa oportunidades contra los 3 negocios de Lucas, genera el informe HORIZON en el formato especificado. Si hay sinergias con forge, menciónalas explícitamente. Al finalizar, llama a write_learnings.
"""


# ── Agentic loop ──────────────────────────────────────────────────────────────
def run() -> str | None:
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": f"Ejecuta la misión horizon para hoy {TODAY}."}]

    for turn in range(MAX_TURNS):
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            system=build_system_prompt(),
            tools=TOOLS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            name = block.name
            inp  = block.input
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
            for block in response.content:
                if hasattr(block, "text") and block.text.strip():
                    return block.text
            break

    return None


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        report = run()
        if not report:
            raise RuntimeError("El agente no generó ningún informe.")

        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        report_path = REPORTS_DIR / f"horizon-{TODAY_KEY}.md"
        write_file(report_path, report)

        digest = report[:900]
        if len(report) > 900:
            digest += "\n…_(ver informe completo)_"
        telegram_send(f"🌅 *HORIZON {datetime.now().strftime('%d/%m')}*\n\n{digest}")

        print(f"[horizon] OK — informe guardado en {report_path}")

    except Exception as exc:
        error_alert("horizon", str(exc))
        print(f"[horizon] ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
