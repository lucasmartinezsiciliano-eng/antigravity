from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..config import configure_logging, get_config
from ..gpu import GPUMode, get_gpu_queue
from ..soul import get_soul_loader
from ..store import get_store

app = FastAPI(title="centrum-studio UI", version="0.1.0")

_templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))


@app.on_event("startup")
async def _startup() -> None:
    configure_logging()
    cfg = get_config()
    cfg.ensure_directories()
    await get_store().initialize()
    await get_gpu_queue().start()
    renders_dir = cfg.renders_dir
    if renders_dir.exists():
        app.mount("/files", StaticFiles(directory=str(renders_dir)), name="files")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    store = get_store()
    projects = await store.list_projects(limit=20)
    scenes, total = await store.list_scenes(limit=20)
    cfg = get_config()
    gpu_mode = cfg.gpu_mode_file.read_text(encoding="utf-8").strip() if cfg.gpu_mode_file.exists() else "agents"
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "projects": projects,
            "scenes": scenes,
            "total_scenes": total,
            "gpu_mode": gpu_mode,
        },
    )


@app.get("/souls", response_class=HTMLResponse)
async def souls_page(request: Request) -> HTMLResponse:
    loader = get_soul_loader()
    souls = loader.list_souls()
    try:
        active, active_path = loader.load_with_paths()
        active_dict = active.to_dict()
        active_path_str = str(active_path)
    except Exception:
        active_dict = None
        active_path_str = None
    return templates.TemplateResponse(
        "souls.html",
        {
            "request": request,
            "souls": souls,
            "active": active_dict,
            "active_path": active_path_str,
        },
    )


@app.post("/souls/{name}/upload")
async def upload_soul_asset(
    name: str,
    asset_type: str = Form(...),
    version: str = Form("v1"),
    file: UploadFile = File(...),
) -> JSONResponse:
    loader = get_soul_loader()
    cfg = get_config()
    cfg.ensure_directories()
    soul_dir = loader.souls_dir / name / (version if version.startswith("v") else f"v{version}")
    valid = {
        "lora_high": ("lora", ".safetensors"),
        "lora_low": ("lora", ".safetensors"),
        "lora_flux": ("lora", ".safetensors"),
        "ip_adapter": ("ip_adapter", ".png"),
        "arcface": ("embeddings", ".npy"),
        "soul_manifest": (".", ".json"),
    }
    if asset_type not in valid:
        raise HTTPException(400, f"unknown asset_type: {asset_type}, valid: {sorted(valid)}")
    subdir, default_ext = valid[asset_type]
    target_dir = soul_dir / subdir if subdir != "." else soul_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = file.filename or f"{asset_type}{default_ext}"
    if asset_type == "soul_manifest":
        filename = "soul.json"
    target_path = target_dir / filename
    with target_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return JSONResponse({
        "ok": True,
        "asset_type": asset_type,
        "path": str(target_path),
        "soul": name,
        "version": version,
    })


@app.post("/souls/{name}/activate")
async def activate_soul(name: str, version: str = Form(...)) -> JSONResponse:
    loader = get_soul_loader()
    try:
        target = loader.activate(name, version)
    except Exception as e:
        raise HTTPException(400, str(e)) from e
    return JSONResponse({"ok": True, "active": str(target)})


@app.post("/souls/create")
async def create_soul(
    name: str = Form(...),
    version: str = Form("v1"),
    character_name: str | None = Form(None),
    trigger_token: str | None = Form(None),
    notes: str | None = Form(None),
) -> JSONResponse:
    loader = get_soul_loader()
    try:
        path = loader.create_soul(
            name=name,
            version=version,
            character_name=character_name,
            trigger_token=trigger_token,
            notes=notes,
        )
    except Exception as e:
        raise HTTPException(400, str(e)) from e
    return JSONResponse({"ok": True, "path": str(path)})


@app.get("/projects/{project_id}", response_class=HTMLResponse)
async def approve_page(request: Request, project_id: str) -> HTMLResponse:
    store = get_store()
    project = await store.get_project(project_id)
    if project is None:
        raise HTTPException(404, "project not found")
    scenes, _ = await store.list_scenes(project_id=project_id, limit=100)
    return templates.TemplateResponse(
        "approve.html",
        {"request": request, "project": project, "scenes": scenes},
    )


@app.post("/projects/{project_id}/approve")
async def approve_project(project_id: str) -> JSONResponse:
    store = get_store()
    if not await store.get_project(project_id):
        raise HTTPException(404, "project not found")
    await store.update_project(project_id, status="approved")
    return JSONResponse({"ok": True, "project_id": project_id, "status": "approved"})


@app.post("/projects/{project_id}/reject")
async def reject_project(project_id: str, reason: str = Form("")) -> JSONResponse:
    store = get_store()
    if not await store.get_project(project_id):
        raise HTTPException(404, "project not found")
    await store.update_project(project_id, status="review_lucas")
    from ..plur import get_plur_bridge
    bridge = get_plur_bridge()
    if reason.strip():
        await bridge.save_engram(
            outcome="failed_quality",
            lesson=f"[Lucas reject] project {project_id}: {reason}",
            tags=["lucas", "rejection", project_id],
            strength=2.0,
        )
    return JSONResponse({"ok": True, "project_id": project_id, "reason": reason})


@app.post("/gpu_mode")
async def set_gpu_mode(mode: str = Form(...)) -> JSONResponse:
    cfg = get_config()
    if mode not in {m.value for m in GPUMode}:
        raise HTTPException(400, f"invalid mode: {mode}")
    cfg.gpu_mode_file.write_text(f"{mode}\n", encoding="utf-8")
    return JSONResponse({"ok": True, "mode": mode})


@app.get("/api/jobs/{job_id}")
async def api_job(job_id: str) -> dict[str, Any]:
    store = get_store()
    job = await store.get_job(job_id)
    if job is None:
        raise HTTPException(404, "job not found")
    return job


@app.get("/api/scenes")
async def api_scenes(project_id: str | None = None, status: str | None = None, limit: int = 20) -> dict[str, Any]:
    store = get_store()
    rows, total = await store.list_scenes(project_id=project_id, status=status, limit=limit)
    return {"scenes": rows, "total": total}


@app.get("/api/health")
async def api_health() -> dict[str, Any]:
    cfg = get_config()
    queue = get_gpu_queue()
    return {
        "ok": True,
        "data_dir": str(cfg.data_dir),
        "gpu_mode": queue.mode.value,
    }


@app.get("/files/{project_id}/{filename}")
async def serve_file(project_id: str, filename: str):
    cfg = get_config()
    path = cfg.renders_dir / project_id / filename
    if not path.exists():
        raise HTTPException(404, "file not found")
    return FileResponse(str(path))


def main() -> None:
    import uvicorn
    cfg = get_config()
    uvicorn.run(
        "centrum_studio.ui.app:app",
        host=cfg.ui_host,
        port=cfg.ui_port,
        log_level=cfg.log_level.lower(),
    )


if __name__ == "__main__":
    main()
