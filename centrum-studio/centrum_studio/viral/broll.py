from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config import get_config
from ._ffmpeg import run_ffmpeg


async def add_broll(
    video_path: Path,
    broll_path: Path,
    start_seconds: float,
    duration_seconds: float,
    opacity: float = 0.85,
    out_path: Path | None = None,
) -> dict[str, Any]:
    cfg = get_config()
    if out_path is None:
        out_path = cfg.renders_dir / f"{video_path.stem}_broll.mp4"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not broll_path.exists():
        return {"ok": False, "error": f"B-roll missing: {broll_path}", "error_code": "BROLL_MISSING"}

    end = start_seconds + duration_seconds
    opacity = max(0.0, min(1.0, opacity))

    filter_complex = (
        f"[1:v]setpts=PTS-STARTPTS+{start_seconds:.3f}/TB,format=yuva420p,"
        f"colorchannelmixer=aa={opacity:.3f}[ov];"
        f"[0:v][ov]overlay=enable='between(t,{start_seconds:.3f},{end:.3f})':"
        f"x=(W-w)/2:y=(H-h)/2[v]"
    )
    res = await run_ffmpeg([
        "-i", str(video_path),
        "-i", str(broll_path),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "0:a?",
        "-c:v", "libx264", "-crf", "20",
        "-c:a", "copy",
        str(out_path),
    ])
    if not res["ok"]:
        return {"ok": False, "error": "ffmpeg overlay failed", "stderr": res["stderr"]}
    return {"ok": True, "path": str(out_path), "broll": str(broll_path)}
