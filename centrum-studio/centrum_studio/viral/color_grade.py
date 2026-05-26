from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config import get_config
from ._ffmpeg import run_ffmpeg


async def apply_color_grade(
    video_path: Path,
    lut_name: str = "centrum_brand",
    out_path: Path | None = None,
) -> dict[str, Any]:
    cfg = get_config()
    if out_path is None:
        out_path = cfg.renders_dir / f"{video_path.stem}_graded.mp4"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    candidates = [
        cfg.luts_dir / f"{lut_name}.cube",
        Path(__file__).parent.parent.parent / "luts" / f"{lut_name}.cube",
    ]
    lut_path = next((c for c in candidates if c.exists()), None)
    if lut_path is None:
        return {
            "ok": False,
            "error": f"LUT not found: {lut_name}.cube",
            "error_code": "LUT_NOT_FOUND",
            "searched": [str(c) for c in candidates],
        }

    vf = f"lut3d=file={lut_path.as_posix()}"
    res = await run_ffmpeg([
        "-i", str(video_path),
        "-vf", vf,
        "-c:v", "libx264", "-crf", "20",
        "-c:a", "copy",
        str(out_path),
    ])
    if not res["ok"]:
        return {"ok": False, "error": "ffmpeg lut3d failed", "stderr": res["stderr"]}
    return {"ok": True, "path": str(out_path), "lut": str(lut_path)}
