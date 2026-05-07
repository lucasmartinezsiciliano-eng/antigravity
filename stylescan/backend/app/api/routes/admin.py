"""
Admin endpoints — internal use only, protected by SECRET_KEY.

POST /admin/barber-agent/run   — Trigger barber Instagram scraping agent
GET  /admin/barber-agent/status — Check index stats
"""

import asyncio
import logging
import sys
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)

KB_DIR = Path(__file__).parent.parent.parent.parent / "knowledge_base"
INDEX_PATH = KB_DIR / "barber_references" / "index.json"

_running = False  # Simple lock — one agent run at a time


def _require_admin(x_admin_key: str = Header(...)):
    if x_admin_key != settings.SECRET_KEY:
        raise HTTPException(403, "Unauthorized")


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

    import json
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
