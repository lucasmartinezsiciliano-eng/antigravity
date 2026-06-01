"""
ana_bot.py
═════════════════════════════════════════════════════════════════════════════
El pipeline de voz en tiempo real de Ana (call-vendedor).

Cadena (todo local salvo Twilio):
    Twilio (audio μ-law 8kHz) ─► Whisper Large v3 (STT, CUDA)
        ─► Gemma 4 26B-A4B (LLM, vLLM :8002)   [persona Ana + contexto del caso]
        ─► XTTS-v2 (TTS, servidor local :8010)  [voz femenina ES]
        ─► Twilio ─► teléfono del cliente

Objetivo de latencia: < 1,5 s por turno. Pipecat hace streaming (TTS empieza
antes de que el LLM termine la frase) e interrupciones (VAD Silero).

Al colgar: recoge la transcripción, la estructura en `call_ia_completada` con el
mismo LLM y la emite al orquestador (ficha_extractor).
"""

import os
import time

from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response import LLMContextAggregatorPair
from pipecat.processors.transcript_processor import TranscriptProcessor
from pipecat.frames.frames import EndFrame, TTSSpeakFrame
from pipecat.serializers.twilio import TwilioFrameSerializer
from pipecat.transports.network.fastapi_websocket import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)
from pipecat.services.whisper.stt import WhisperSTTService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.xtts import XTTSService
from pipecat.transcriptions.language import Language

import aiohttp

from ana_prompt import construir_system_prompt, apertura
import ficha_extractor


async def run_ana(
    websocket,
    stream_sid: str,
    call_sid: str,
    caso_id: str,
    nombre: str = "",
):
    """Lanza el pipeline de Ana sobre una llamada Twilio ya conectada."""
    cfg = _config()
    t0 = time.monotonic()

    # ── Transporte: media stream de Twilio sobre websocket ───────────────────
    serializer = TwilioFrameSerializer(
        stream_sid=stream_sid,
        call_sid=call_sid,
        account_sid=cfg["twilio_sid"],
        auth_token=cfg["twilio_token"],
    )
    transport = FastAPIWebsocketTransport(
        websocket=websocket,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            vad_analyzer=SileroVADAnalyzer(
                # Pausa algo más larga: gente en crisis habla lento, no cortar.
                params=VADParams(stop_secs=0.8)
            ),
            serializer=serializer,
        ),
    )

    # ── STT: Whisper Large v3 local en CUDA ──────────────────────────────────
    stt = WhisperSTTService(
        device=cfg["whisper_device"],
        compute_type=cfg["whisper_compute"],
        settings=WhisperSTTService.Settings(
            model=cfg["whisper_model"],
            language=Language.ES,
        ),
    )

    # ── LLM: Gemma 4 26B-A4B local vía vLLM (OpenAI-compatible) ───────────────
    system_prompt, _ficha_parcial = construir_system_prompt(
        caso_id=caso_id, cases_dir=cfg["cases_dir"], nombre=nombre
    )
    llm = OpenAILLMService(
        api_key=cfg["llm_api_key"],
        base_url=cfg["llm_base_url"],
        model=cfg["llm_model"],
        params=OpenAILLMService.InputParams(temperature=0.6),
    )

    # ── TTS: XTTS-v2 local (servidor aparte), voz femenina española ──────────
    aiohttp_session = aiohttp.ClientSession()
    tts = XTTSService(
        settings=XTTSService.Settings(
            voice=cfg["xtts_voice"],
            language=Language.ES,
        ),
        base_url=cfg["xtts_base_url"],
        aiohttp_session=aiohttp_session,
    )

    # ── Contexto de conversación + captura de transcripción ──────────────────
    context = LLMContext(messages=[{"role": "system", "content": system_prompt}])
    user_agg, assistant_agg = LLMContextAggregatorPair(context)
    transcript = TranscriptProcessor()

    pipeline = Pipeline([
        transport.input(),
        stt,
        transcript.user(),       # guarda lo que dice el cliente
        user_agg,
        llm,
        tts,
        transport.output(),
        transcript.assistant(),  # guarda lo que dice Ana
        assistant_agg,
    ])

    task = PipelineTask(
        pipeline,
        params=PipelineParams(allow_interruptions=True),
    )

    # Acumulamos la transcripción para la extracción final.
    turnos: list[str] = []

    @transcript.event_handler("on_transcript_update")
    async def _on_transcript(_proc, frame):
        for msg in frame.messages:
            quien = "Ana" if msg.role == "assistant" else "Cliente"
            turnos.append(f"{quien}: {msg.content}")

    @transport.event_handler("on_client_connected")
    async def _on_connected(_t, _client):
        # Apertura obligatoria: identificación IA + petición de consentimiento.
        await task.queue_frame(TTSSpeakFrame(apertura(nombre)))

    @transport.event_handler("on_client_disconnected")
    async def _on_disconnected(_t, _client):
        await task.queue_frame(EndFrame())

    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)

    # ── Post-llamada: estructurar y emitir la ficha ──────────────────────────
    await aiohttp_session.close()
    await _finalizar_llamada(
        cfg=cfg, caso_id=caso_id, call_sid=call_sid,
        transcripcion="\n".join(turnos), duracion_seg=int(time.monotonic() - t0),
    )


async def _finalizar_llamada(cfg, caso_id, call_sid, transcripcion, duracion_seg):
    """Extrae la ficha de la transcripción y la emite al orquestador."""
    if not transcripcion.strip():
        logger.warning(f"[ana_bot] llamada {call_sid} sin transcripción; nada que emitir")
        return

    ficha_llm = await ficha_extractor.extraer_ficha(
        transcripcion=transcripcion,
        llm_base_url=cfg["llm_base_url"],
        llm_model=cfg["llm_model"],
        llm_api_key=cfg["llm_api_key"],
    )

    # Consentimiento de grabación: heurística sobre el inicio de la conversación.
    # (En producción, además se marca explícitamente al detectar el "sí" tras la
    #  apertura; aquí lo derivamos del texto para no perder la señal.)
    consentimiento = _consintio_grabacion(transcripcion)

    transcripcion_ref = f"{cfg['cases_dir']}/{caso_id}/transcript.txt"
    try:
        from pathlib import Path
        p = Path(transcripcion_ref)
        p.parent.mkdir(parents=True, exist_ok=True)
        # Solo se persiste el audio/transcript si hubo consentimiento (RGPD).
        if consentimiento:
            p.write_text(transcripcion, encoding="utf-8")
        else:
            transcripcion_ref = ""  # no se conserva
    except OSError as e:
        logger.error(f"[ana_bot] no se pudo guardar transcript: {e}")

    evento = ficha_extractor.construir_evento(
        caso_id=caso_id, ficha_llm=ficha_llm, transcripcion=transcripcion,
        consentimiento_grabacion=consentimiento, duracion_seg=duracion_seg,
        transcripcion_ref=transcripcion_ref,
    )
    ficha_extractor.guardar_evento(caso_id, cfg["cases_dir"], evento)
    await ficha_extractor.emitir_a_orquestador(evento, cfg["orchestrator_url"])
    logger.info(
        f"[ana_bot] caso {caso_id}: ficha emitida "
        f"(urgencia={evento['urgencia']}, pendientes={len(evento['datos_pendientes'])})"
    )


def _consintio_grabacion(transcripcion: str) -> bool:
    """Tras la apertura ('¿te parece bien que sigamos?'), un 'sí'/'vale'/'claro'
    cuenta como consentimiento verbal (Capa 1b). Un 'no' lo niega."""
    lineas = [l for l in transcripcion.splitlines() if l.startswith("Cliente:")]
    if not lineas:
        return False
    primera = lineas[0].lower()
    if any(p in primera for p in ("no ", "no,", "no.", "prefiero que no", "no quiero")):
        return False
    return any(p in primera for p in ("sí", "si", "vale", "claro", "adelante", "ok", "de acuerdo"))


def _config() -> dict:
    return {
        "twilio_sid": os.getenv("TWILIO_ACCOUNT_SID", ""),
        "twilio_token": os.getenv("TWILIO_AUTH_TOKEN", ""),
        "llm_base_url": os.getenv("LLM_BASE_URL", "http://localhost:8002/v1"),
        "llm_model": os.getenv("LLM_MODEL", "gemma-4-26B-A4B-it"),
        "llm_api_key": os.getenv("LLM_API_KEY", "not-needed"),
        "whisper_model": os.getenv("WHISPER_MODEL", "large-v3"),
        "whisper_device": os.getenv("WHISPER_DEVICE", "cuda"),
        "whisper_compute": os.getenv("WHISPER_COMPUTE_TYPE", "float16"),
        "xtts_base_url": os.getenv("XTTS_BASE_URL", "http://localhost:8010"),
        "xtts_voice": os.getenv("XTTS_VOICE", "Ana Florence"),
        "cases_dir": os.getenv("CASES_DIR", "/root/.hermes/profiles/centrum/cases"),
        "orchestrator_url": os.getenv("ORCHESTRATOR_EVENT_URL", ""),
    }
