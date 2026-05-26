from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import structlog
from fastmcp import FastMCP

from .assembly import assemble_video
from .comfy import get_comfy_client
from .config import configure_logging, get_config
from .errors import (
    CentrumStudioError,
    JobNotFoundError,
    SceneNotFoundError,
)
from .eval import get_evaluator
from .gpu import get_gpu_queue
from .lipsync import run_latentsync, synthesize_tts
from .plur import get_plur_bridge
from .soul import get_soul_loader
from .store import get_store, new_id
from .viral import (
    add_broll,
    add_hook_text,
    apply_captions_viral,
    apply_color_grade,
    apply_zoom_punch,
    cut_to_beat,
    trim_for_platform,
)

log = structlog.get_logger("centrum_studio.server")

mcp = FastMCP(
    name="centrum-studio",
    instructions=(
        "centrum-studio is an agent-first video production server. "
        "Soul File defines the character's permanent identity and is auto-injected. "
        "Jobs are async: tools that schedule GPU work return job_id; poll with get_job_status. "
        "All errors are structured with error_code, suggestion, recovery_action."
    ),
)


def _err(e: Exception) -> dict[str, Any]:
    if isinstance(e, CentrumStudioError):
        return e.to_dict()
    return {
        "error": True,
        "error_code": "INTERNAL_ERROR",
        "message": str(e),
        "suggestion": "Check logs for stack trace; retry idempotent operations.",
        "recovery_action": "retry",
    }


async def _produce_runner(
    job_id: str,
    scene_id: str,
    project_id: str,
    scene_description: str,
    duration_seconds: int,
    aspect_ratio: str,
    workflow_name: str = "produce_scene_wan22.json",
) -> dict[str, Any]:
    cfg = get_config()
    store = get_store()
    loader = get_soul_loader()
    comfy = get_comfy_client()

    soul, soul_root = loader.load_with_paths()
    full_prompt = loader.inject_into_prompt(soul, scene_description)

    width, height = {"9:16": (720, 1280), "16:9": (1280, 720), "1:1": (1024, 1024)}.get(
        aspect_ratio, (720, 1280)
    )
    fps = 16
    frames = max(16, int(duration_seconds * fps))

    workflow = comfy.load_workflow_template(workflow_name)
    workflow = comfy.inject_soul(
        workflow=workflow,
        soul=soul,
        soul_root=soul_root,
        prompt=full_prompt,
        width=width,
        height=height,
        frames=frames,
    )

    await store.update_job(job_id, status="running", progress_pct=5.0)
    prompt_id = await comfy.submit_prompt(workflow)
    await store.update_scene(scene_id, comfy_prompt_id=prompt_id, status="running")

    async def on_progress(p: dict[str, Any]) -> None:
        if p.get("type") == "progress" and p.get("max"):
            pct = 5.0 + (float(p["value"]) / float(p["max"])) * 85.0
            await store.update_job(job_id, progress_pct=min(pct, 90.0))

    history = await comfy.wait_for_completion(prompt_id, on_progress=on_progress, timeout_seconds=1800)
    outputs = comfy.find_video_outputs(history)
    if not outputs:
        await store.update_scene(scene_id, status="failed", error="No outputs from ComfyUI")
        raise CentrumStudioError(
            "ComfyUI returned no video outputs",
            error_code="COMFYUI_NO_OUTPUT",
            suggestion="Inspect workflow template and ComfyUI logs",
            recovery_action="regenerate_scene",
        )
    first = outputs[0]
    out_dir = cfg.renders_dir / project_id
    out_dir.mkdir(parents=True, exist_ok=True)
    final_path = out_dir / f"{scene_id}.mp4"
    await comfy.download_output(
        filename=first["filename"],
        subfolder=first.get("subfolder", ""),
        type_=first.get("type", "output"),
        dest=final_path,
    )
    await store.update_scene(
        scene_id,
        status="rendered",
        output_path=str(final_path),
        duration_seconds=duration_seconds,
    )
    return {"scene_id": scene_id, "output_path": str(final_path), "prompt_id": prompt_id}


@mcp.tool
async def produce_scene(
    scene_description: str,
    duration_seconds: int = 6,
    aspect_ratio: str = "9:16",
    project_id: str | None = None,
    priority: int = 5,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Generate one clip (4-12s) of the active Soul character in the described scene.

    Returns immediately with a job_id; poll with get_job_status. The Soul File
    (trigger token, LoRA, IP-Adapter, PuLID) is injected automatically.
    """
    try:
        store = get_store()
        queue = get_gpu_queue()
        if not (4 <= duration_seconds <= 12):
            return CentrumStudioError(
                f"duration_seconds must be 4..12 (got {duration_seconds})",
                error_code="INVALID_DURATION",
                suggestion="Pass duration_seconds between 4 and 12",
                recovery_action="adjust_params",
            ).to_dict()
        if aspect_ratio not in ("9:16", "16:9", "1:1"):
            return CentrumStudioError(
                f"aspect_ratio must be one of 9:16|16:9|1:1 (got {aspect_ratio})",
                error_code="INVALID_ASPECT_RATIO",
                recovery_action="adjust_params",
            ).to_dict()

        if idempotency_key:
            existing = await store.get_job_by_idempotency(idempotency_key)
            if existing:
                return {
                    "job_id": existing["job_id"],
                    "scene_id": existing.get("scene_id"),
                    "status": existing["status"],
                    "idempotent_hit": True,
                }

        proj_id = project_id or new_id("prj")
        existing_proj = await store.get_project(proj_id)
        if existing_proj is None:
            await store.create_project(proj_id, name=f"Project {proj_id[-6:]}")

        loader = get_soul_loader()
        soul = loader.load()
        scene_id = new_id("scn")
        await store.create_scene(
            scene_id=scene_id,
            project_id=proj_id,
            soul_id=soul.soul_id,
            scene_description=scene_description,
            duration_seconds=duration_seconds,
            params_used={"aspect_ratio": aspect_ratio},
        )
        job_id = new_id("job")
        await store.create_job(
            job_id=job_id,
            job_type="produce",
            scene_id=scene_id,
            project_id=proj_id,
            priority=priority,
            idempotency_key=idempotency_key,
            payload={
                "scene_description": scene_description,
                "duration_seconds": duration_seconds,
                "aspect_ratio": aspect_ratio,
            },
        )

        async def runner() -> dict[str, Any]:
            return await _produce_runner(
                job_id=job_id,
                scene_id=scene_id,
                project_id=proj_id,
                scene_description=scene_description,
                duration_seconds=duration_seconds,
                aspect_ratio=aspect_ratio,
            )

        result = await queue.enqueue(job_id, "produce", runner, priority=priority)
        result["scene_id"] = scene_id
        result["project_id"] = proj_id
        return result
    except Exception as e:
        log.exception("produce_scene.failed")
        return _err(e)


@mcp.tool
async def evaluate_scene(scene_id: str) -> dict[str, Any]:
    """Measure ArcFace + DOVER + MUSIQ + LPIPS for a rendered scene."""
    try:
        store = get_store()
        scene = await store.get_scene(scene_id)
        if scene is None:
            raise SceneNotFoundError(f"scene_id not found: {scene_id}")
        if not scene.get("output_path"):
            return CentrumStudioError(
                f"Scene {scene_id} has no output yet (status: {scene['status']})",
                error_code="SCENE_NOT_READY",
                suggestion="Wait for produce_scene job to complete (poll get_job_status)",
                recovery_action="poll_job_status",
            ).to_dict()

        loader = get_soul_loader()
        soul, soul_root = loader.load_with_paths()
        evaluator = get_evaluator(soul, soul_root)
        result = await evaluator.evaluate(Path(scene["output_path"]), lipsynced=False)
        await store.update_scene(
            scene_id,
            arcface_similarity=result.arcface_similarity,
            dover_score=result.dover_score,
            musiq_score=result.musiq_score,
            temporal_lpips=result.temporal_lpips,
            syncnet_lsec=result.syncnet_lsec,
            passed_thresholds=1 if result.passed else 0,
        )
        return {
            "scene_id": scene_id,
            "metrics": result.to_dict(),
            "passed": result.passed,
            "failures": result.failures,
        }
    except Exception as e:
        log.exception("evaluate_scene.failed", scene_id=scene_id)
        return _err(e)


@mcp.tool
async def regenerate_scene(scene_id: str, adjustments: dict[str, Any] | None = None) -> dict[str, Any]:
    """Retry rendering a scene with adjustments {strength_delta?, prompt_suffix?, cfg_delta?, steps_delta?}."""
    try:
        store = get_store()
        original = await store.get_scene(scene_id)
        if original is None:
            raise SceneNotFoundError(f"scene_id not found: {scene_id}")

        adjustments = adjustments or {}
        suffix = adjustments.get("prompt_suffix", "")
        new_description = original["scene_description"]
        if suffix:
            new_description = f"{new_description} {suffix}".strip()

        loader = get_soul_loader()
        soul = loader.load()
        new_scene_id = new_id("scn")
        params = original.get("params_used") or {}
        params["regenerated_from"] = scene_id
        params["adjustments"] = adjustments
        await store.create_scene(
            scene_id=new_scene_id,
            project_id=original["project_id"],
            soul_id=soul.soul_id,
            scene_description=new_description,
            duration_seconds=original.get("duration_seconds") or 6,
            params_used=params,
        )

        job_id = new_id("job")
        await store.create_job(
            job_id=job_id,
            job_type="produce",
            scene_id=new_scene_id,
            project_id=original["project_id"],
            priority=5,
            payload={"regenerated_from": scene_id, "adjustments": adjustments},
        )

        duration = int(original.get("duration_seconds") or 6)
        aspect = (original.get("params_used") or {}).get("aspect_ratio", "9:16")
        project_id_val = original["project_id"]

        async def runner() -> dict[str, Any]:
            return await _produce_runner(
                job_id=job_id,
                scene_id=new_scene_id,
                project_id=project_id_val,
                scene_description=new_description,
                duration_seconds=duration,
                aspect_ratio=aspect,
            )

        queue = get_gpu_queue()
        result = await queue.enqueue(job_id, "produce", runner, priority=5)
        result["scene_id"] = new_scene_id
        result["regenerated_from"] = scene_id
        return result
    except Exception as e:
        log.exception("regenerate_scene.failed", scene_id=scene_id)
        return _err(e)


@mcp.tool
async def lipsync_scene(scene_id: str, dialogue: str, voice_id: str | None = None) -> dict[str, Any]:
    """Generate TTS for dialogue then apply LatentSync to the scene video."""
    try:
        store = get_store()
        scene = await store.get_scene(scene_id)
        if scene is None:
            raise SceneNotFoundError(f"scene_id not found: {scene_id}")
        if not scene.get("output_path"):
            return CentrumStudioError(
                f"Scene {scene_id} has no output yet",
                error_code="SCENE_NOT_READY",
                recovery_action="poll_job_status",
            ).to_dict()

        loader = get_soul_loader()
        soul = loader.load()
        effective_voice = voice_id or soul.voice_id

        job_id = new_id("job")
        await store.create_job(
            job_id=job_id,
            job_type="lipsync",
            scene_id=scene_id,
            priority=5,
            payload={"dialogue": dialogue, "voice_id": effective_voice},
        )

        async def runner() -> dict[str, Any]:
            cfg = get_config()
            tts_out = cfg.cache_dir / f"{scene_id}_voice.wav"
            tts_res = await synthesize_tts(dialogue, effective_voice, tts_out)
            if not tts_res.get("ok"):
                raise CentrumStudioError(
                    tts_res.get("error") or "TTS failed",
                    error_code=tts_res.get("error_code") or "TTS_FAILED",
                    suggestion="Install chatterbox-tts or pre-render audio externally",
                    recovery_action="install_tts",
                )
            video_in = Path(scene["output_path"])
            synced_path = cfg.renders_dir / scene["project_id"] / f"{scene_id}_synced.mp4"
            sync_res = await run_latentsync(video_in, Path(tts_res["path"]), synced_path)
            if not sync_res.get("ok"):
                raise CentrumStudioError(
                    sync_res.get("error") or "LatentSync failed",
                    error_code=sync_res.get("error_code") or "LIPSYNC_FAILED",
                    recovery_action="install_latentsync",
                )
            await store.update_scene(scene_id, output_path=sync_res["path"], status="lipsynced")
            return {"scene_id": scene_id, "path": sync_res["path"], "engine": sync_res.get("engine")}

        queue = get_gpu_queue()
        return await queue.enqueue(job_id, "lipsync", runner, priority=5)
    except Exception as e:
        log.exception("lipsync_scene.failed", scene_id=scene_id)
        return _err(e)


@mcp.tool
async def assemble_video_tool(
    project_id: str,
    scene_ids: list[str],
    include_subtitles: bool = False,
    music_track: str | None = None,
    branding: bool = True,
) -> dict[str, Any]:
    """Concat scenes into the final MP4 for a project (with optional music & branding)."""
    try:
        store = get_store()
        project = await store.get_project(project_id)
        if project is None:
            await store.create_project(project_id, name=f"Project {project_id[-6:]}")

        scene_paths: list[Path] = []
        for sid in scene_ids:
            sc = await store.get_scene(sid)
            if sc is None:
                raise SceneNotFoundError(f"scene_id not found: {sid}")
            if not sc.get("output_path"):
                return CentrumStudioError(
                    f"Scene {sid} not yet rendered",
                    error_code="SCENE_NOT_READY",
                    recovery_action="poll_job_status",
                ).to_dict()
            scene_paths.append(Path(sc["output_path"]))

        music_path = Path(music_track) if music_track else None
        if music_path is not None and not music_path.is_absolute():
            music_path = get_config().music_dir / music_track  # type: ignore[arg-type]

        job_id = new_id("job")
        await store.create_job(
            job_id=job_id,
            job_type="assemble",
            project_id=project_id,
            priority=3,
            payload={"scene_ids": scene_ids, "music_track": music_track, "branding": branding},
        )

        async def runner() -> dict[str, Any]:
            res = await assemble_video(
                scene_paths=scene_paths,
                project_id=project_id,
                music_track=music_path,
                include_subtitles=include_subtitles,
                branding=branding,
            )
            if not res.get("ok"):
                raise CentrumStudioError(
                    res.get("error") or "Assembly failed",
                    error_code=res.get("error_code") or "ASSEMBLY_FAILED",
                )
            await store.update_project(
                project_id,
                status="assembly",
                scene_ids=scene_ids,
                final_video_path=res["path"],
            )
            return res

        queue = get_gpu_queue()
        return await queue.enqueue(job_id, "assemble", runner, priority=3)
    except Exception as e:
        log.exception("assemble_video.failed", project_id=project_id)
        return _err(e)


@mcp.tool
async def get_soul() -> dict[str, Any]:
    """Return the active Soul File manifest and its path on disk."""
    try:
        loader = get_soul_loader()
        soul, path = loader.load_with_paths()
        return {"soul": soul.to_dict(), "version_path": str(path), "name": soul.soul_id}
    except Exception as e:
        return _err(e)


@mcp.tool
async def list_renders(
    project_id: str | None = None,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    """List previous scene renders with their metrics. Use for review/recall."""
    try:
        store = get_store()
        scenes, total = await store.list_scenes(
            project_id=project_id, status=status, limit=limit, offset=offset
        )
        renders = []
        for s in scenes:
            renders.append({
                "scene_id": s["scene_id"],
                "project_id": s["project_id"],
                "status": s["status"],
                "scene_description": s.get("scene_description"),
                "output_path": s.get("output_path"),
                "metrics": {
                    "arcface_similarity": s.get("arcface_similarity"),
                    "dover_score": s.get("dover_score"),
                    "musiq_score": s.get("musiq_score"),
                    "temporal_lpips": s.get("temporal_lpips"),
                    "passed_thresholds": bool(s.get("passed_thresholds")),
                },
                "created_at": s.get("created_at"),
            })
        return {"renders": renders, "total": total, "limit": limit, "offset": offset}
    except Exception as e:
        return _err(e)


@mcp.tool
async def learn_from_render(
    scene_id: str,
    outcome: str,
    lesson: str,
    recommended_params: dict[str, Any] | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Save a learning engram to PLUR (or local fallback) about this render."""
    try:
        allowed = {"worked_great", "acceptable", "failed_identity", "failed_quality", "failed_lipsync"}
        if outcome not in allowed:
            return CentrumStudioError(
                f"outcome must be one of {sorted(allowed)} (got {outcome})",
                error_code="INVALID_OUTCOME",
                recovery_action="adjust_params",
            ).to_dict()
        strength = 2.0 if outcome.startswith("failed") else 1.0
        bridge = get_plur_bridge()
        return await bridge.save_engram(
            outcome=outcome,
            lesson=lesson,
            scene_id=scene_id,
            recommended_params=recommended_params,
            tags=tags,
            strength=strength,
        )
    except Exception as e:
        return _err(e)


@mcp.tool
async def recall_learnings(
    scene_description: str,
    tags_hint: list[str] | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """Retrieve engrams relevant to the given scene description before producing."""
    try:
        bridge = get_plur_bridge()
        engrams = await bridge.search(query=scene_description, tags_hint=tags_hint, limit=limit)
        return {"engrams": engrams, "count": len(engrams)}
    except Exception as e:
        return _err(e)


@mcp.tool
async def get_job_status(job_id: str) -> dict[str, Any]:
    """Poll a queued/running job's status and progress."""
    try:
        store = get_store()
        job = await store.get_job(job_id)
        if job is None:
            raise JobNotFoundError(f"job_id not found: {job_id}")
        return {
            "job_id": job["job_id"],
            "status": job["status"],
            "progress_pct": job.get("progress_pct") or 0.0,
            "eta_seconds": job.get("eta_seconds"),
            "result": job.get("result"),
            "error": job.get("error"),
            "error_code": job.get("error_code"),
            "job_type": job.get("job_type"),
            "scene_id": job.get("scene_id"),
            "project_id": job.get("project_id"),
        }
    except Exception as e:
        return _err(e)


@mcp.tool
async def cancel_job(job_id: str) -> dict[str, Any]:
    """Cancel a queued or running job and release its GPU slot."""
    try:
        store = get_store()
        job = await store.get_job(job_id)
        if job is None:
            raise JobNotFoundError(f"job_id not found: {job_id}")
        queue = get_gpu_queue()
        cancelled = await queue.cancel(job_id)
        return {"cancelled": cancelled, "job_id": job_id}
    except Exception as e:
        return _err(e)


# -------------------- Viral editing tools (12-18) --------------------

async def _scene_path(scene_id: str) -> Path:
    store = get_store()
    scene = await store.get_scene(scene_id)
    if scene is None:
        raise SceneNotFoundError(f"scene_id not found: {scene_id}")
    out = scene.get("output_path")
    if not out:
        raise CentrumStudioError(
            f"Scene {scene_id} has no output yet",
            error_code="SCENE_NOT_READY",
            recovery_action="poll_job_status",
        )
    return Path(out)


def _viral_enqueue(job_type: str, runner_coro):
    async def _wrap() -> dict[str, Any]:
        return await runner_coro
    return _wrap


@mcp.tool
async def apply_captions_viral_tool(scene_id: str, style: str = "default") -> dict[str, Any]:
    """Apply CapCut-style word-by-word captions (Whisper + ffmpeg drawtext)."""
    try:
        path = await _scene_path(scene_id)
        store = get_store()
        job_id = new_id("job")
        await store.create_job(
            job_id=job_id, job_type="viral_edit", scene_id=scene_id, priority=4,
            payload={"op": "captions", "style": style},
        )

        async def runner() -> dict[str, Any]:
            res = await apply_captions_viral(path, style=style)
            if not res.get("ok"):
                raise CentrumStudioError(res.get("error") or "Captions failed", error_code="CAPTIONS_FAILED")
            await store.update_scene(scene_id, output_path=res["path"])
            return res

        queue = get_gpu_queue()
        return await queue.enqueue(job_id, "viral_edit", runner, priority=4)
    except Exception as e:
        return _err(e)


@mcp.tool
async def cut_to_beat_tool(video_path: str, music_path: str) -> dict[str, Any]:
    """Auto-cut a video on music beats (Librosa BPM + ffmpeg)."""
    try:
        store = get_store()
        job_id = new_id("job")
        await store.create_job(
            job_id=job_id, job_type="viral_edit", priority=4,
            payload={"op": "beat_cut", "video": video_path, "music": music_path},
        )

        async def runner() -> dict[str, Any]:
            res = await cut_to_beat(Path(video_path), Path(music_path))
            if not res.get("ok"):
                raise CentrumStudioError(res.get("error") or "Beat-cut failed", error_code="BEAT_CUT_FAILED")
            return res

        queue = get_gpu_queue()
        return await queue.enqueue(job_id, "viral_edit", runner, priority=4)
    except Exception as e:
        return _err(e)


@mcp.tool
async def apply_zoom_punch_tool(scene_id: str, timestamp_seconds: float, zoom_factor: float = 1.15) -> dict[str, Any]:
    """Apply a zoom punch on a keyword moment."""
    try:
        path = await _scene_path(scene_id)
        store = get_store()
        job_id = new_id("job")
        await store.create_job(
            job_id=job_id, job_type="viral_edit", scene_id=scene_id, priority=4,
            payload={"op": "zoom_punch", "ts": timestamp_seconds, "zoom": zoom_factor},
        )

        async def runner() -> dict[str, Any]:
            res = await apply_zoom_punch(path, timestamp_seconds=timestamp_seconds, zoom_factor=zoom_factor)
            if not res.get("ok"):
                raise CentrumStudioError(res.get("error") or "Zoom-punch failed", error_code="ZOOM_FAILED")
            await store.update_scene(scene_id, output_path=res["path"])
            return res

        queue = get_gpu_queue()
        return await queue.enqueue(job_id, "viral_edit", runner, priority=4)
    except Exception as e:
        return _err(e)


@mcp.tool
async def add_hook_text_tool(
    scene_id: str,
    text: str,
    duration_seconds: float = 2.0,
    style: str = "default",
) -> dict[str, Any]:
    """Overlay large hook text on the first screen."""
    try:
        path = await _scene_path(scene_id)
        store = get_store()
        job_id = new_id("job")
        await store.create_job(
            job_id=job_id, job_type="viral_edit", scene_id=scene_id, priority=4,
            payload={"op": "hook_text", "text": text, "duration": duration_seconds, "style": style},
        )

        async def runner() -> dict[str, Any]:
            res = await add_hook_text(path, text=text, duration_seconds=duration_seconds, style=style)
            if not res.get("ok"):
                raise CentrumStudioError(res.get("error") or "Hook text failed", error_code="HOOK_TEXT_FAILED")
            await store.update_scene(scene_id, output_path=res["path"])
            return res

        queue = get_gpu_queue()
        return await queue.enqueue(job_id, "viral_edit", runner, priority=4)
    except Exception as e:
        return _err(e)


@mcp.tool
async def apply_color_grade_tool(scene_id: str, lut_name: str = "centrum_brand") -> dict[str, Any]:
    """Apply a brand LUT (3D color grade)."""
    try:
        path = await _scene_path(scene_id)
        store = get_store()
        job_id = new_id("job")
        await store.create_job(
            job_id=job_id, job_type="viral_edit", scene_id=scene_id, priority=4,
            payload={"op": "color_grade", "lut": lut_name},
        )

        async def runner() -> dict[str, Any]:
            res = await apply_color_grade(path, lut_name=lut_name)
            if not res.get("ok"):
                raise CentrumStudioError(res.get("error") or "Color grade failed", error_code="LUT_FAILED")
            await store.update_scene(scene_id, output_path=res["path"])
            return res

        queue = get_gpu_queue()
        return await queue.enqueue(job_id, "viral_edit", runner, priority=4)
    except Exception as e:
        return _err(e)


@mcp.tool
async def add_broll_tool(
    scene_id: str,
    broll_path: str,
    start_seconds: float,
    duration_seconds: float,
    opacity: float = 0.85,
) -> dict[str, Any]:
    """Overlay a B-roll clip on the scene (talking-head style)."""
    try:
        path = await _scene_path(scene_id)
        store = get_store()
        job_id = new_id("job")
        await store.create_job(
            job_id=job_id, job_type="viral_edit", scene_id=scene_id, priority=4,
            payload={"op": "broll", "broll": broll_path, "start": start_seconds, "duration": duration_seconds},
        )

        async def runner() -> dict[str, Any]:
            res = await add_broll(
                path,
                broll_path=Path(broll_path),
                start_seconds=start_seconds,
                duration_seconds=duration_seconds,
                opacity=opacity,
            )
            if not res.get("ok"):
                raise CentrumStudioError(res.get("error") or "B-roll failed", error_code="BROLL_FAILED")
            await store.update_scene(scene_id, output_path=res["path"])
            return res

        queue = get_gpu_queue()
        return await queue.enqueue(job_id, "viral_edit", runner, priority=4)
    except Exception as e:
        return _err(e)


@mcp.tool
async def trim_for_platform_tool(scene_id: str, platform: str) -> dict[str, Any]:
    """Conform scene to platform spec (tiktok|reels|shorts|youtube)."""
    try:
        path = await _scene_path(scene_id)
        store = get_store()
        job_id = new_id("job")
        await store.create_job(
            job_id=job_id, job_type="viral_edit", scene_id=scene_id, priority=4,
            payload={"op": "trim", "platform": platform},
        )

        async def runner() -> dict[str, Any]:
            res = await trim_for_platform(path, platform=platform)
            if not res.get("ok"):
                raise CentrumStudioError(res.get("error") or "Trim failed", error_code="TRIM_FAILED")
            await store.update_scene(scene_id, output_path=res["path"])
            return res

        queue = get_gpu_queue()
        return await queue.enqueue(job_id, "viral_edit", runner, priority=4)
    except Exception as e:
        return _err(e)


async def _startup() -> None:
    cfg = get_config()
    cfg.ensure_directories()
    store = get_store()
    await store.initialize()
    queue = get_gpu_queue()
    await queue.start()
    log.info("centrum_studio.started", data_dir=str(cfg.data_dir), gpu_mode=queue.mode.value)


def main() -> None:
    configure_logging()
    cfg = get_config()
    cfg.ensure_directories()

    async def _bootstrap() -> None:
        await _startup()

    try:
        asyncio.run(_bootstrap())
    except RuntimeError:
        pass

    mcp.run(transport=cfg.mcp_transport)


if __name__ == "__main__":
    main()
