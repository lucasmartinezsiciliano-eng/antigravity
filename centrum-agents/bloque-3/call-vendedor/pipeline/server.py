"""
server.py
═════════════════════════════════════════════════════════════════════════════
Servidor del pipeline de voz de Ana. Tres responsabilidades:

  1. POST /llamar          → el orquestador pide una llamada SALIENTE a un lead.
                             Lanza la llamada vía Twilio REST apuntando a /twiml.
  2. POST /twiml           → Twilio pide el TwiML; respondemos con <Connect><Stream>
                             hacia /ws, pasando caso_id y nombre.
  3. WEBSOCKET /ws         → Twilio abre el media stream; aquí corre run_ana().

Arrancar en el DGX:
    uvicorn server:app --host 0.0.0.0 --port 8090

RGPD: los datos del cliente solo se tocan en local (CASES_DIR). Lo único que
sale del DGX es el audio por Twilio (transporte telefónico).
"""

import json
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse
from loguru import logger
from twilio.rest import Client as TwilioClient

import ana_bot

load_dotenv()

app = FastAPI(title="Centrum · Ana call-vendedor")

PUBLIC_WS_URL = os.getenv("PUBLIC_WS_URL", "wss://localhost:8090/ws")
PUBLIC_BASE = os.getenv("PUBLIC_BASE_URL", PUBLIC_WS_URL.rsplit("/ws", 1)[0].replace("wss://", "https://"))


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ana-call-vendedor"}


@app.post("/llamar")
async def llamar(request: Request):
    """El orquestador lanza una llamada saliente.
    Body: {"caso_id": "...", "telefono": "+34...", "nombre": "..."}"""
    body = await request.json()
    caso_id = body.get("caso_id", "")
    telefono = body.get("telefono", "")
    nombre = body.get("nombre", "")
    if not (caso_id and telefono):
        return JSONResponse({"error": "faltan caso_id o telefono"}, status_code=400)

    client = TwilioClient(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    # El TwiML callback lleva caso_id y nombre como query para inyectar contexto.
    twiml_url = f"{PUBLIC_BASE}/twiml?caso_id={caso_id}&nombre={nombre}"
    call = client.calls.create(
        to=telefono,
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        url=twiml_url,
    )
    logger.info(f"[server] llamada saliente lanzada caso={caso_id} sid={call.sid}")
    return {"call_sid": call.sid, "caso_id": caso_id}


@app.post("/twiml")
async def twiml(request: Request):
    """Twilio pide instrucciones. Conectamos el audio al websocket /ws.
    Pasamos caso_id y nombre como parámetros del <Stream> (llegan en el evento 'start')."""
    caso_id = request.query_params.get("caso_id", "")
    nombre = request.query_params.get("nombre", "")
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <Stream url="{PUBLIC_WS_URL}">
      <Parameter name="caso_id" value="{caso_id}" />
      <Parameter name="nombre" value="{nombre}" />
    </Stream>
  </Connect>
</Response>"""
    return HTMLResponse(content=xml, media_type="application/xml")


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    """Media stream de Twilio. Leemos los 2 primeros mensajes ('connected' y
    'start') para sacar stream_sid, call_sid y los Parameters, y arrancamos Ana."""
    await websocket.accept()

    # Mensaje 1: 'connected'. Mensaje 2: 'start' (trae los SIDs y custom params).
    await websocket.receive_text()  # connected
    start_raw = await websocket.receive_text()
    start = json.loads(start_raw)
    start_data = start.get("start", {})
    stream_sid = start_data.get("streamSid", "")
    call_sid = start_data.get("callSid", "")
    params = start_data.get("customParameters", {}) or {}
    caso_id = params.get("caso_id", "")
    nombre = params.get("nombre", "")

    logger.info(f"[server] media stream iniciado caso={caso_id} call={call_sid}")
    await ana_bot.run_ana(
        websocket=websocket,
        stream_sid=stream_sid,
        call_sid=call_sid,
        caso_id=caso_id,
        nombre=nombre,
    )
