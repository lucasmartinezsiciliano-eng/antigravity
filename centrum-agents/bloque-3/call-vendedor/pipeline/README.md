# Ana — pipeline de voz (call-vendedor) · runbook DGX Spark

Implementación de la **Opción B** (todo local salvo telefonía). Convierte a Ana
(definida en `../IDENTITY.md`) en una voz que conversa por teléfono en tiempo real.

```
Twilio (μ-law 8kHz) ─► Whisper Large v3 (STT, CUDA)
   ─► Gemma 4 26B-A4B (LLM, vLLM :8002)  ← persona Ana + contexto del caso
   ─► XTTS-v2 (TTS, :8010)               ← voz femenina española
   ─► Twilio ─► cliente
```
Objetivo: **< 1,5 s por turno**. Coste: €0 inferencia + Twilio (~€0,013/min ES).

---

## Archivos

| Archivo | Qué hace |
|---|---|
| `server.py` | FastAPI: lanza llamadas salientes (`/llamar`), sirve TwiML (`/twiml`), recibe el media stream (`/ws`) |
| `ana_bot.py` | El pipeline Pipecat (STT→LLM→TTS) + cierre y emisión de ficha |
| `ana_prompt.py` | System prompt de Ana + inyección de `ficha_parcial` del DM |
| `ficha_extractor.py` | Estructura la transcripción en el evento `call_ia_completada` |
| `requirements.txt` · `.env.example` | Dependencias y credenciales |

---

## 1. Prerequisitos en el DGX

- `vllm-start.sh` corriendo → Gemma 4 26B-A4B en `:8002` (lo verifica `curl localhost:8002/v1/models`).
- Python 3.11+ y un venv.
- GPU CUDA disponible (la usa Whisper; el TTS corre en su propio servidor).

## 2. Instalar

```bash
cd /root/centrum-agents/bloque-3/call-vendedor/pipeline
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # y rellenar credenciales Twilio + URLs
```

## 3. Levantar el servidor XTTS-v2 (TTS local, una vez)

XTTS corre como proceso aparte (Pipecat solo le habla por HTTP). Servidor oficial:

```bash
# Opción Docker (recomendada)
docker run -d --gpus all -p 8010:80 \
  -e COQUI_TOS_AGREED=1 \
  --name centrum-xtts \
  ghcr.io/coqui-ai/xtts-streaming-server:latest
```

- Voz por defecto: `Ana Florence` (femenina, español nativo) → ya configurada en `.env`.
- **Voz clonada** (recomendado para producción): subir 6–10 s de audio de referencia
  al servidor XTTS y usar su `speaker_id` en `XTTS_VOICE`. Decisión XTTS-v2 vs F5-TTS
  se valida en MiroFish (ver `../IDENTITY.md` y el vault).

## 4. Arrancar el pipeline

```bash
source .venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8090
```

## 5. Exponer a Twilio

Twilio necesita una URL pública (HTTPS + WSS) para `/twiml` y `/ws`:
- **Dev:** `ngrok http 8090` → pon la URL en `PUBLIC_WS_URL` (`wss://...ngrok.../ws`).
- **Prod:** dominio propio con TLS (reverse proxy) → `wss://centrum-call.<dominio>/ws`.

## 6. Lanzar una llamada (lo hace el orquestador)

```bash
curl -X POST http://localhost:8090/llamar \
  -H 'Content-Type: application/json' \
  -d '{"caso_id":"CTR-20260601-001","telefono":"+34600000000","nombre":"Juan"}'
```

Flujo: Twilio llama → al descolgar pide `/twiml` → conecta `/ws` → Ana abre con la
identificación IA + consentimiento de grabación → conversa → al colgar emite
`call_ia_completada` al orquestador (que dispara call-prep / call-scheduler y, si
hay urgencia, la escalación en caliente a Mariano por Telegram).

---

## Validación de latencia (el paso que confirma que "es rápido")

1. Llamada de prueba a tu propio móvil con `/llamar`.
2. En los logs de uvicorn, medir el delta entre fin de habla del cliente (VAD stop)
   y primer audio de Ana. Diana: **< 1,5 s**.
3. Si se pasa:
   - LLM lento → bajar `max_tokens` de las respuestas / subir prioridad vLLM.
   - TTS lento → confirmar que XTTS hace streaming (debe empezar audio < 400 ms).
   - STT lento → `WHISPER_COMPUTE_TYPE=float16` y modelo `large-v3` (no v3 sin turbo si va justo: probar `large-v3-turbo`).
4. Concurrencia: para Centrum, 1–3 llamadas simultáneas bastan al inicio. Load test antes de escalar.

## Notas RGPD / legales (heredadas de IDENTITY.md y skill legal-rgpd)

- Ana **se identifica como IA** en la apertura (AI Act art. 50) — pendiente de
  verificación legal por Lucas/abogado.
- La grabación solo se conserva **si hubo consentimiento verbal** (Capa 1b). Si el
  cliente dice "no", `transcripcion_ref` queda vacío y no se persiste el audio.
- Todo STT/LLM/TTS es **local en el DGX**; los datos del cliente no salen a APIs
  externas. Solo el transporte de voz (Twilio) es externo.
- Esto NO es la firma vinculante (Capa 2): eso se firma en la apertura de
  expediente, tras la consulta con Mariano. Ver vault `Legal y RGPD — Cuándo firma el cliente`.

---
*Pipeline v1 — 2026-06-01 — Mediterránea Firmax SL. Versiones de librerías pueden
cambiar; re-probar latencia tras cada subida de pipecat-ai.*
