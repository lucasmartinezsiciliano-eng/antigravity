from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config import get_config
from ._ffmpeg import probe_duration, run_ffmpeg


PLATFORM_SPECS = {
    "tiktok":  {"aspect": "9:16", "max_seconds": 180, "width": 1080, "height": 1920, "fps": 30, "v_bitrate": "8M"},
    "reels":   {"aspect": "9:16", "max_seconds": 90,  "width": 1080, "height": 1920, "fps": 30, "v_bitrate": "8M"},
    "shorts":  {"aspect": "9:16", "max_seconds": 60,  "width": 1080, "height": 1920, "fps": 30, "v_bitrate": "8M"},
    "youtube": {"aspect": "16:9", "max_seconds": 600, "width": 1920, "height": 1080, "fps": 30, "v_bitrate": "12M"},
}


async def trim_for_platform(
    video_path: Path,
    platform: str,
    out_path: Path | None = None,
) -> dict[str, Any]:
    cfg = get_config()
    spec = PLATFORM_SPECS.get(platform.lower())
    if spec is None:
        return {
            "ok": False,
            "error": f"Unknown platform: {platform}",
            "error_code": "UNKNOWN_PLATFORM",
            "supported": list(PLATFORM_SPECS.keys()),
        }
    if out_path is None:
        out_path = cfg.renders_dir / f"{video_path.stem}_{platform}.mp4"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    duration = await probe_duration(video_path)
    if duration <= 0:
        return {"ok": False, "error": "Probe failed", "error_code": "PROBE_FAILED"}

    target_seconds = min(duration, spec["max_seconds"])
    w, h = spec["width"], spec["height"]
    vf = (
        f"scale={w}:{h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h},"
        f"fps={spec['fps']}"
    )
    res = await run_ffmpeg([
        "-t", f"{target_seconds:.3f}",
        "-i", str(video_path),
        "-vf", vf,
        "-c:v", "libx264",
        "-b:v", spec["v_bitrate"],
        "-pix_fmt", "yuv420p",
        "-profile:v", "high",
        "-level", "4.0",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart",
        str(out_path),
    ])
    if not res["ok"]:
        return {"ok": False, "error": "ffmpeg trim failed", "stderr": res["stderr"]}
    return {
        "ok": True,
        "path": str(out_path),
        "platform": platform,
        "duration": target_seconds,
        "resolution": f"{w}x{h}",
    }
