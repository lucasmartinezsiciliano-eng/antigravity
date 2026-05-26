from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config import get_config
from ._ffmpeg import probe_duration, run_ffmpeg


async def apply_zoom_punch(
    video_path: Path,
    timestamp_seconds: float,
    zoom_factor: float = 1.15,
    out_path: Path | None = None,
) -> dict[str, Any]:
    cfg = get_config()
    if out_path is None:
        out_path = cfg.renders_dir / f"{video_path.stem}_zoom.mp4"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    duration = await probe_duration(video_path)
    if duration <= 0:
        return {"ok": False, "error": "Probe failed", "error_code": "PROBE_FAILED"}

    punch_duration = 0.35
    start = max(0.0, timestamp_seconds)
    end = min(duration, start + punch_duration)

    expr_zoom = (
        f"if(between(t,{start:.3f},{end:.3f}),"
        f"1+({zoom_factor - 1})*sin((t-{start:.3f})/{punch_duration:.3f}*PI),1)"
    )
    vf = (
        f"zoompan=z='{expr_zoom}':"
        f"x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2':"
        f"d=1:fps=30:s=iw*ih"
    )
    res = await run_ffmpeg([
        "-i", str(video_path),
        "-vf", vf,
        "-c:v", "libx264", "-crf", "20",
        "-c:a", "copy",
        str(out_path),
    ])
    if not res["ok"]:
        return {"ok": False, "error": "ffmpeg zoom failed", "stderr": res["stderr"]}
    return {"ok": True, "path": str(out_path), "timestamp": start, "zoom_factor": zoom_factor}
