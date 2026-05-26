from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path
from typing import Any

import structlog

from ..config import get_config

log = structlog.get_logger("centrum_studio.lipsync.latentsync")


def _find_latentsync() -> str | None:
    for name in ("latentsync", "latent-sync", "latentsync-cli"):
        p = shutil.which(name)
        if p:
            return p
    return None


async def _run_subprocess(args: list[str], cwd: str | None = None) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode or 0, stdout.decode(errors="ignore"), stderr.decode(errors="ignore")


async def run_latentsync(
    video_path: Path,
    audio_path: Path,
    out_path: Path | None = None,
) -> dict[str, Any]:
    cfg = get_config()
    if out_path is None:
        out_path = cfg.cache_dir / f"{video_path.stem}_synced.mp4"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    binary = _find_latentsync()
    if binary:
        rc, out, err = await _run_subprocess(
            [
                binary,
                "--video", str(video_path),
                "--audio", str(audio_path),
                "--output", str(out_path),
            ]
        )
        if rc == 0 and out_path.exists():
            return {"ok": True, "path": str(out_path), "engine": "latentsync"}
        log.warning("latentsync.failed", returncode=rc, stderr=err[:300])

    inference_script = os.environ.get("LATENTSYNC_INFERENCE_SCRIPT")
    if inference_script and Path(inference_script).exists():
        rc, out, err = await _run_subprocess(
            [
                "python", inference_script,
                "--unet_config_path", os.environ.get("LATENTSYNC_UNET_CONFIG", "configs/unet/stage2.yaml"),
                "--inference_ckpt_path", os.environ.get("LATENTSYNC_CKPT", "checkpoints/latentsync_unet.pt"),
                "--video_path", str(video_path),
                "--audio_path", str(audio_path),
                "--video_out_path", str(out_path),
                "--inference_steps", "20",
                "--guidance_scale", "1.5",
            ]
        )
        if rc == 0 and out_path.exists():
            return {"ok": True, "path": str(out_path), "engine": "latentsync_script"}
        log.warning("latentsync.script_failed", returncode=rc, stderr=err[:300])

    if shutil.which("ffmpeg"):
        rc, out, err = await _run_subprocess([
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-map", "0:v:0", "-map", "1:a:0",
            "-shortest",
            str(out_path),
        ])
        if rc == 0 and out_path.exists():
            return {
                "ok": True,
                "path": str(out_path),
                "engine": "ffmpeg_fallback",
                "warning": "LatentSync not found — audio muxed without real lipsync",
            }

    return {
        "ok": False,
        "error": "LatentSync unavailable and ffmpeg fallback failed",
        "error_code": "LIPSYNC_UNAVAILABLE",
    }
