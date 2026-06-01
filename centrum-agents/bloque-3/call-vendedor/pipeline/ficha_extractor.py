"""
ficha_extractor.py
═════════════════════════════════════════════════════════════════════════════
Al terminar la llamada, convierte la transcripción en la ficha estructurada
`call_ia_completada` que consume call-prep / ficha-builder (ver IDENTITY.md).

Usa el MISMO LLM local (Gemma via vLLM) en modo extracción JSON — coste 0 y los
datos no salen del DGX (RGPD). Detecta urgencia y estima categoría A/B/C/D/E
(orientativa; Mariano confirma).

NO hace asesoramiento. Solo estructura lo que se dijo en la llamada.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import aiohttp
from loguru import logger

CAMPOS_FICHA = [
    "nombre", "contacto", "inmueble_ubicacion", "deuda_capital", "impago_cuotas",
    "cuota_mensual", "banco", "titulares", "avalistas", "tipo_interes",
    "plazo_restante", "otras_deudas", "judicial",
]
CRITICOS = {"impago_cuotas", "banco", "judicial"}

# Disparadores de urgencia (subasta/demanda/desahucio con fecha o inminente).
PATRONES_URGENCIA = re.compile(
    r"\b(subasta|deman[dn]|desahucio|lanzamiento|buro ?fax|juzgado|embargo|"
    r"notari[ao]|ejecuci[oó]n hipotecaria)\b",
    re.IGNORECASE,
)

PROMPT_EXTRACCION = """\
Eres un extractor de datos. A partir de la TRANSCRIPCIÓN de una llamada entre \
Ana (asistente IA de Centrum) y un cliente con problemas de hipoteca, devuelve \
SOLO un objeto JSON válido, sin texto antes ni después, con esta forma exacta:

{{
  "nombre": "", "contacto": {{"telefono": "", "email": ""}},
  "inmueble_ubicacion": "", "deuda_capital": "", "impago_cuotas": "",
  "cuota_mensual": "", "banco": "", "titulares": "", "avalistas": "",
  "tipo_interes": "", "plazo_restante": "", "otras_deudas": "", "judicial": "",
  "datos_extendidos": {{
    "anio_hipoteca": "", "senal_clausula_suelo": "", "acreedor_actual": "",
    "contacto_previo_banco": "", "vivienda_habitual": "", "ingresos_hogar": "",
    "personas_hogar": "", "inmueble_detalle": "", "seguros_vinculados": ""
  }},
  "objetivo_cliente": "", "objetivo_matiz": "",
  "notas_emocionales": "", "categoria_estimada": ""
}}

Reglas:
- Si un dato no se dijo, déjalo como cadena vacía "". NO inventes.
- "datos_extendidos": datos que afinan el análisis (año de la hipoteca, señal de \
cláusula suelo, si la deuda la tiene el banco o un fondo, contacto previo, si es \
vivienda habitual, ingresos, personas en el hogar, detalle del inmueble, seguros). \
Rellena solo lo que se haya dicho.
- "objetivo_cliente": una de estas palabras si se deduce — "quedarse", \
"salir_limpio", "ganar_tiempo", "liquidez", "indeciso". "objetivo_matiz": lo que \
de verdad pesa, en palabras del cliente.
- "notas_emocionales": estado anímico y señales relevantes para el asesor humano.
- "categoria_estimada": una letra A/B/C/D/E (A=urgente subasta/demanda, \
B=impago normal, C=no cualifica, D=caso de abogado, E=entrega de posesión). \
Es orientativa.

TRANSCRIPCIÓN:
{transcripcion}
"""


def _detectar_urgencia(transcripcion: str, judicial: str) -> bool:
    if PATRONES_URGENCIA.search(transcripcion):
        return True
    return bool(judicial) and judicial.strip().lower() not in ("", "no", "ninguna")


def _extraer_json(texto: str) -> dict:
    """Saca el primer objeto JSON del texto del LLM (por si añade ruido)."""
    inicio = texto.find("{")
    fin = texto.rfind("}")
    if inicio == -1 or fin == -1:
        return {}
    try:
        return json.loads(texto[inicio:fin + 1])
    except json.JSONDecodeError:
        return {}


async def extraer_ficha(
    transcripcion: str,
    llm_base_url: str,
    llm_model: str,
    llm_api_key: str = "not-needed",
) -> dict:
    """Llama al LLM local para estructurar la transcripción en la ficha."""
    payload = {
        "model": llm_model,
        "messages": [
            {"role": "user", "content": PROMPT_EXTRACCION.format(transcripcion=transcripcion)}
        ],
        "temperature": 0.0,
        "max_tokens": 1024,
    }
    headers = {"Authorization": f"Bearer {llm_api_key}"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{llm_base_url}/chat/completions", json=payload, headers=headers,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                data = await resp.json()
        contenido = data["choices"][0]["message"]["content"]
        return _extraer_json(contenido)
    except (aiohttp.ClientError, KeyError, IndexError) as e:
        logger.error(f"[ficha_extractor] fallo extracción LLM: {e}")
        return {}


def construir_evento(
    caso_id: str,
    ficha_llm: dict,
    transcripcion: str,
    consentimiento_grabacion: bool,
    duracion_seg: int,
    transcripcion_ref: str,
) -> dict:
    """Ensambla el evento `call_ia_completada` con el esquema de IDENTITY.md."""
    ficha = {c: ficha_llm.get(c, "") for c in CAMPOS_FICHA}
    if isinstance(ficha.get("contacto"), str):
        ficha["contacto"] = {"telefono": ficha["contacto"], "email": ""}

    pendientes = [c for c in CAMPOS_FICHA if not ficha.get(c)]
    urgencia = _detectar_urgencia(transcripcion, str(ficha.get("judicial", "")))

    return {
        "evento": "call_ia_completada",
        "caso_id": caso_id,
        "canal": "call_ia",
        "consentimiento_grabacion": consentimiento_grabacion,
        "duracion_seg": duracion_seg,
        "ficha": ficha,
        "datos_extendidos": ficha_llm.get("datos_extendidos", {}),
        "objetivo_cliente": ficha_llm.get("objetivo_cliente", ""),
        "objetivo_matiz": ficha_llm.get("objetivo_matiz", ""),
        "datos_pendientes": pendientes,
        "urgencia": urgencia,
        "categoria_estimada": ficha_llm.get("categoria_estimada", ""),
        "notas_emocionales": ficha_llm.get("notas_emocionales", ""),
        "transcripcion_ref": transcripcion_ref,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def guardar_evento(caso_id: str, cases_dir: str, evento: dict) -> Path:
    """Persiste el evento en el caso (datos del cliente SOLO en local, RGPD)."""
    destino = Path(cases_dir) / caso_id
    destino.mkdir(parents=True, exist_ok=True)
    ruta = destino / "call_ia_completada.json"
    ruta.write_text(json.dumps(evento, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"[ficha_extractor] evento guardado en {ruta}")
    return ruta


async def emitir_a_orquestador(evento: dict, orchestrator_event_url: str) -> None:
    """Notifica al orquestador para que dispare call-prep / call-scheduler.
    Si la urgencia es alta, el orquestador hace la escalación en caliente a Mariano."""
    if not orchestrator_event_url:
        return
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(
                orchestrator_event_url, json=evento,
                timeout=aiohttp.ClientTimeout(total=15),
            )
    except aiohttp.ClientError as e:
        logger.error(f"[ficha_extractor] no se pudo emitir al orquestador: {e}")
