"""
Admin endpoints — internal use only, protected by SECRET_KEY (x-admin-key header).

POST   /admin/barber-agent/run           — Trigger barber Instagram scraping agent
GET    /admin/barber-agent/status        — Check index stats

POST   /admin/referencias/upload         — Upload a curated reference photo (multipart)
GET    /admin/referencias/               — List all curated references
DELETE /admin/referencias/{ref_id}       — Remove a curated reference (json + file)
GET    /admin/referencias/imagen/{name}  — Serve a curated image (auth via header or ?key=)

POST   /admin/telegram-webhook           — Telegram bot webhook (validates chat_id allowlist)
"""

import asyncio
import json
import logging
import sys
import uuid
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, File, Form, Header, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)

KB_DIR = Path(__file__).parent.parent.parent.parent / "knowledge_base"
INDEX_PATH = KB_DIR / "barber_references" / "index.json"
ADMIN_REFS_PATH = KB_DIR / "barber_references" / "admin_refs.json"
CURATED_DIR = KB_DIR / "barber_references" / "curated"

ALLOWED_ANGLES = {"frontal", "perfil_izquierdo", "perfil_derecho"}

_running = False  # Simple lock — one agent run at a time


def _require_admin(x_admin_key: str = Header(...)):
    if x_admin_key != settings.SECRET_KEY:
        raise HTTPException(403, "Unauthorized")


# ---------------------------------------------------------------------------
# admin_refs.json helpers
# ---------------------------------------------------------------------------
def _load_admin_refs() -> dict:
    """Read admin_refs.json. Initialize empty structure if missing/corrupt."""
    if not ADMIN_REFS_PATH.exists():
        return {"updated_at": None, "total": 0, "references": []}
    try:
        return json.loads(ADMIN_REFS_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning("admin_refs.json parse error, reinitializing: %s", e)
        return {"updated_at": None, "total": 0, "references": []}


def _save_admin_refs(data: dict) -> None:
    """Write admin_refs.json atomically (write to tmp, then rename)."""
    ADMIN_REFS_PATH.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    data["total"] = len(data.get("references", []))
    tmp = ADMIN_REFS_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(ADMIN_REFS_PATH)


def _image_url(request: Request, filename: str) -> str:
    """
    Build a public URL for the image endpoint based on the incoming request.

    Uses FastAPI's url_for when possible (handles the full mount prefix, e.g.
    /api/v1/admin/...). Falls back to request.base_url + router.prefix.
    """
    try:
        return str(request.url_for("serve_reference_image", filename=filename))
    except Exception:
        base = str(request.base_url).rstrip("/")
        return f"{base}{router.prefix}/referencias/imagen/{filename}"


def _metrics_to_dict(metrics) -> dict:
    """Convert a dataclass (PhotoAnalysis) into a plain dict, or return {} on failure."""
    if metrics is None:
        return {}
    if is_dataclass(metrics):
        return asdict(metrics)
    if isinstance(metrics, dict):
        return metrics
    return {}


def _build_reference_entry(
    request: Request,
    ref_id: str,
    haircut_name: str,
    angle: str,
    notes: str,
    filename: str,
    face_detected: bool,
    metrics: dict,
) -> dict:
    return {
        "id": ref_id,
        "haircut_name": haircut_name,
        "angle": angle,
        "notes": notes or "",
        "filename": filename,
        "image_url": _image_url(request, filename),
        "face_detected": face_detected,
        "metrics": metrics,
        "added_at": datetime.now(timezone.utc).isoformat(),
    }


def _process_and_store(
    request: Request,
    raw_bytes: bytes,
    original_filename: str,
    haircut_name: str,
    angle: str,
    notes: str,
) -> dict:
    """
    Shared pipeline: validate → save → (optional) face analysis → index.
    Raises HTTPException(422) if validation fails. Returns the new entry dict.
    """
    from app.services import photo_service

    val_result, prepared = photo_service.validate_and_prepare_photo(
        raw_bytes, original_filename
    )
    if not val_result.valid or not prepared:
        raise HTTPException(422, val_result.error or "La foto no pasó la validación.")

    CURATED_DIR.mkdir(parents=True, exist_ok=True)
    ref_id = str(uuid.uuid4())[:8]
    filename = f"{ref_id}.jpg"
    target = CURATED_DIR / filename
    target.write_bytes(prepared)

    # Best-effort face analysis — non-fatal if it fails
    face_detected = False
    metrics: dict = {}
    try:
        from app.services import face_analysis
        # The closest documented API: analyze_single_photo (MediaPipe-backed).
        # Spec called it analyze_face — alias here if it ever lands.
        analyze_fn = getattr(face_analysis, "analyze_face", None) or getattr(
            face_analysis, "analyze_single_photo", None
        )
        if analyze_fn is not None:
            result = analyze_fn(prepared)
            metrics = _metrics_to_dict(result)
            face_detected = bool(metrics.get("face_detected", False))
    except Exception as e:
        logger.warning("Face analysis failed for ref %s (non-fatal): %s", ref_id, e)

    entry = _build_reference_entry(
        request=request,
        ref_id=ref_id,
        haircut_name=haircut_name,
        angle=angle,
        notes=notes,
        filename=filename,
        face_detected=face_detected,
        metrics=metrics,
    )

    data = _load_admin_refs()
    data.setdefault("references", []).append(entry)
    _save_admin_refs(data)

    logger.info("Stored reference %s (%s, %s)", ref_id, haircut_name, angle)
    return entry


# ---------------------------------------------------------------------------
# Existing endpoints — barber agent
# ---------------------------------------------------------------------------
class RunRequest(BaseModel):
    max_posts: int = 30
    accounts: list[str] = []
    save_images: bool = False


class RunResponse(BaseModel):
    status: str
    message: str


@router.post("/barber-agent/run", response_model=RunResponse)
async def run_barber_agent(
    body: RunRequest,
    x_admin_key: str = Header(...),
):
    """Trigger the barber Instagram scraping agent as a background task."""
    _require_admin(x_admin_key)

    global _running
    if _running:
        return RunResponse(status="already_running", message="Agent is already running.")

    cmd = [sys.executable, "-m", "scripts.barber_instagram_agent", "--max-posts", str(body.max_posts)]
    if body.accounts:
        cmd += ["--accounts"] + body.accounts
    if body.save_images:
        cmd.append("--save-images")

    async def _run():
        global _running
        _running = True
        try:
            logger.info("Barber agent starting: %s", " ".join(cmd))
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(Path(__file__).parent.parent.parent.parent),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            stdout, _ = await proc.communicate()
            output = stdout.decode(errors="replace")
            logger.info("Barber agent finished (exit=%d):\n%s", proc.returncode, output[-2000:])
        except Exception as e:
            logger.error("Barber agent error: %s", e)
        finally:
            _running = False

    asyncio.create_task(_run())

    accounts_desc = ", ".join(body.accounts) if body.accounts else "all from barber_accounts.json"
    return RunResponse(
        status="started",
        message=f"Agent started — {accounts_desc}, max {body.max_posts} posts/account. Check server logs.",
    )


@router.get("/barber-agent/status")
async def barber_agent_status(x_admin_key: str = Header(...)):
    """Return current index stats."""
    _require_admin(x_admin_key)

    if not INDEX_PATH.exists():
        return {"total": 0, "running": _running, "index_exists": False}

    try:
        data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        return {
            "total": data.get("total", 0),
            "updated_at": data.get("updated_at"),
            "running": _running,
            "index_exists": True,
        }
    except Exception:
        return {"total": 0, "running": _running, "index_exists": True, "error": "parse error"}


# ---------------------------------------------------------------------------
# Reference photo management
# ---------------------------------------------------------------------------
@router.post("/referencias/upload")
async def upload_reference(
    request: Request,
    photo: UploadFile = File(...),
    haircut_name: str = Form(...),
    angle: str = Form(...),
    notes: str = Form(""),
    x_admin_key: str = Header(...),
):
    """Upload a curated reference photo. Saves to disk + indexes in admin_refs.json."""
    _require_admin(x_admin_key)

    if angle not in ALLOWED_ANGLES:
        raise HTTPException(
            400,
            f"angle inválido. Permitidos: {', '.join(sorted(ALLOWED_ANGLES))}",
        )

    haircut_name = (haircut_name or "").strip()
    if not haircut_name:
        raise HTTPException(400, "haircut_name es obligatorio.")

    raw_bytes = await photo.read()
    entry = _process_and_store(
        request=request,
        raw_bytes=raw_bytes,
        original_filename=photo.filename or "upload.jpg",
        haircut_name=haircut_name,
        angle=angle,
        notes=notes,
    )
    return entry


@router.get("/referencias/")
async def list_references(x_admin_key: str = Header(...)):
    """Return all curated references."""
    _require_admin(x_admin_key)
    data = _load_admin_refs()
    refs = data.get("references", [])
    return {"total": len(refs), "references": refs}


@router.delete("/referencias/{ref_id}")
async def delete_reference(ref_id: str, x_admin_key: str = Header(...)):
    """Remove a reference from the index AND delete its image file."""
    _require_admin(x_admin_key)

    data = _load_admin_refs()
    refs = data.get("references", [])
    match = next((r for r in refs if r.get("id") == ref_id), None)
    if not match:
        raise HTTPException(404, f"Reference {ref_id} not found.")

    # Delete file (best-effort)
    filename = match.get("filename")
    if filename:
        img_path = CURATED_DIR / filename
        try:
            if img_path.exists():
                img_path.unlink()
        except Exception as e:
            logger.warning("Could not delete image %s: %s", img_path, e)

    data["references"] = [r for r in refs if r.get("id") != ref_id]
    _save_admin_refs(data)
    return {"status": "deleted", "id": ref_id}


@router.get("/referencias/imagen/{filename}", name="serve_reference_image")
async def serve_reference_image(
    filename: str,
    key: Optional[str] = Query(None),
    x_admin_key: Optional[str] = Header(None),
):
    """
    Serve a curated image. Accepts auth via:
      - x-admin-key header (preferred, used by JSON API clients)
      - ?key= query param (needed for <img src> embedding in the admin UI)
    """
    provided = x_admin_key or key
    if not provided or provided != settings.SECRET_KEY:
        raise HTTPException(403, "Unauthorized")

    # Prevent path traversal
    if "/" in filename or "\\" in filename or filename.startswith(".."):
        raise HTTPException(400, "Invalid filename.")

    img_path = CURATED_DIR / filename
    if not img_path.exists() or not img_path.is_file():
        raise HTTPException(404, "Image not found.")

    return FileResponse(str(img_path), media_type="image/jpeg")


# ---------------------------------------------------------------------------
# Telegram webhook — receive photos from the bot on Lucas's phone
# ---------------------------------------------------------------------------
def _allowed_telegram_chat_ids() -> set[str]:
    raw = settings.ADMIN_TELEGRAM_ALLOWED_CHAT_IDS or ""
    return {cid.strip() for cid in raw.split(",") if cid.strip()}


def _parse_caption(caption: str) -> tuple[str, str]:
    """
    Parse a Telegram caption into (haircut_name, angle).
    Accepted formats:
      "Skin Fade | frontal"
      "Skin Fade"            (angle defaults to 'frontal')
    """
    caption = (caption or "").strip()
    if not caption:
        return "", "frontal"
    if "|" in caption:
        name, _, angle = caption.partition("|")
        name = name.strip()
        angle = angle.strip().lower()
        if angle not in ALLOWED_ANGLES:
            angle = "frontal"
        return name, angle
    return caption, "frontal"


async def _telegram_send_message(chat_id: int | str, text: str) -> None:
    """Best-effort reply to Telegram. Silent if bot token missing."""
    token = settings.ADMIN_TELEGRAM_BOT_TOKEN
    if not token:
        logger.info("ADMIN_TELEGRAM_BOT_TOKEN empty — skipping reply.")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(url, json={"chat_id": chat_id, "text": text})
    except Exception as e:
        logger.warning("Telegram sendMessage failed: %s", e)


async def _telegram_download_photo(file_id: str) -> bytes:
    """Two-step Telegram file download. Raises on failure."""
    token = settings.ADMIN_TELEGRAM_BOT_TOKEN
    if not token:
        raise RuntimeError("ADMIN_TELEGRAM_BOT_TOKEN not configured.")

    async with httpx.AsyncClient(timeout=30.0) as client:
        r1 = await client.get(
            f"https://api.telegram.org/bot{token}/getFile",
            params={"file_id": file_id},
        )
        r1.raise_for_status()
        payload = r1.json()
        if not payload.get("ok"):
            raise RuntimeError(f"getFile failed: {payload}")
        file_path = payload["result"]["file_path"]

        r2 = await client.get(f"https://api.telegram.org/file/bot{token}/{file_path}")
        r2.raise_for_status()
        return r2.content


@router.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    """
    Telegram webhook. Validates chat_id against allowlist.

    Caption format: "Haircut Name | angle"  (angle is one of frontal / perfil_izquierdo / perfil_derecho)
    Defaults to angle=frontal if not specified.

    Always returns 200 so Telegram doesn't retry on partial failures.
    """
    try:
        update = await request.json()
    except Exception:
        return {"ok": True, "ignored": "invalid_json"}

    message = update.get("message") or update.get("edited_message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if chat_id is None:
        return {"ok": True, "ignored": "no_chat"}

    allowed = _allowed_telegram_chat_ids()
    if allowed and str(chat_id) not in allowed:
        logger.warning("Telegram webhook: chat_id %s not in allowlist.", chat_id)
        return {"ok": True, "ignored": "unauthorized_chat"}

    photos = message.get("photo")
    if not photos:
        await _telegram_send_message(
            chat_id,
            "Envía una foto con caption:\n"
            "  Nombre del corte | angulo\n"
            "Angulos válidos: frontal, perfil_izquierdo, perfil_derecho.\n"
            "Si omites el ángulo, se asume frontal.",
        )
        return {"ok": True, "ignored": "no_photo"}

    caption = message.get("caption") or ""
    haircut_name, angle = _parse_caption(caption)
    if not haircut_name:
        await _telegram_send_message(
            chat_id,
            "Falta el nombre del corte en el caption.\n"
            "Ejemplo: Skin Fade | frontal",
        )
        return {"ok": True, "ignored": "no_caption"}

    # Telegram delivers an array of size variants — take the largest.
    best = max(photos, key=lambda p: p.get("file_size") or p.get("width") or 0)
    file_id = best.get("file_id")
    if not file_id:
        await _telegram_send_message(chat_id, "No pude leer la foto, intenta de nuevo.")
        return {"ok": True, "ignored": "no_file_id"}

    try:
        raw_bytes = await _telegram_download_photo(file_id)
    except Exception as e:
        logger.error("Telegram photo download failed: %s", e)
        await _telegram_send_message(chat_id, f"Error descargando la foto: {e}")
        return {"ok": True, "ignored": "download_failed"}

    try:
        entry = _process_and_store(
            request=request,
            raw_bytes=raw_bytes,
            original_filename=f"telegram_{file_id}.jpg",
            haircut_name=haircut_name,
            angle=angle,
            notes=f"via Telegram (chat {chat_id})",
        )
    except HTTPException as e:
        await _telegram_send_message(chat_id, f"Foto rechazada: {e.detail}")
        return {"ok": True, "ignored": "validation_failed", "detail": e.detail}
    except Exception as e:
        logger.exception("Telegram reference store failed")
        await _telegram_send_message(chat_id, f"Error procesando la foto: {e}")
        return {"ok": True, "ignored": "internal_error"}

    await _telegram_send_message(
        chat_id,
        f"Guardado ✓\n  id: {entry['id']}\n  corte: {entry['haircut_name']}\n"
        f"  ángulo: {entry['angle']}\n  cara detectada: {entry['face_detected']}",
    )
    return {"ok": True, "stored": entry["id"]}
