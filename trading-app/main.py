"""
FastAPI webhook receiver — entry point for TradingView alerts.
Validates API key, queues signal to Redis, returns immediately.
"""

import json
import logging
import os

import redis
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware

from models import Signal

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

app = FastAPI(title="IFVG Trading Bot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

_redis: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
    return _redis


@app.post("/webhook")
async def receive_signal(
    signal: Signal,
    x_api_key: str = Header(None),
):
    """
    TradingView sends POST here with the alert JSON payload.
    Header: X-Api-Key: <WEBHOOK_API_KEY>
    """
    expected_key = os.getenv("WEBHOOK_API_KEY")
    if expected_key and x_api_key != expected_key:
        raise HTTPException(status_code=403, detail="Unauthorized")

    payload = signal.model_dump()
    get_redis().publish("signals", json.dumps(payload))

    log.info(f"[WEBHOOK] Queued: {signal.action} {signal.symbol} @ {signal.close}")
    return {"status": "queued", "action": signal.action, "symbol": signal.symbol}


@app.get("/status")
async def status():
    """Health check — TradingView can test webhook connectivity here."""
    try:
        get_redis().ping()
        redis_ok = True
    except Exception:
        redis_ok = False

    return {
        "status": "online",
        "redis": "ok" if redis_ok else "error",
        "version": "1.0.0",
    }


@app.get("/")
async def root():
    return {"msg": "IFVG Trading Bot — use POST /webhook or GET /status"}
