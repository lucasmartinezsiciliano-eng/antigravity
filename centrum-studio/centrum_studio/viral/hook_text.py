from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config import get_config
from ._ffmpeg import run_ffmpeg

STYLES = {
    "default": {"font_size": 96, "color": "white", "border": "black", "border_w": 8},
    "bold": {"font_size": 120, "color": "white", "border": "black", "border_w": 12},
    "neon": {"font_size": 100, "color": "#39FF14", "border": "#FF00FF", "border_w": 8},
    "minimal": {"font_size": 72, "color": "white", "border": "black", "border_w": 4},
}


async def add_hook_text(
    video_path: Path,
    text: str,
    duration_seconds: float = 2.0,
    style: str = "default",
    out_path: Path | None = None,
) -> dict[str, Any]:
    cfg = get_config()
    if out_path is None:
        out_path = cfg.renders_dir / f"{video_path.stem}_hook.mp4"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    s = STYLES.get(style, STYLES["default"])
    safe_text = text.replace("'", r"\'").replace(":", r"\:").replace(",", r"\,")
    vf = (
        f"drawtext=text='{safe_text}':"
        f"fontsize={s['font_size']}:fontcolor={s['color']}:"
        f"bordercolor={s['border']}:borderw={s['border_w']}:"
        f"x=(w-text_w)/2:y=h*0.3:"
        f"enable='lt(t,{duration_seconds:.3f})'"
    )
    res = await run_ffmpeg([
        "-i", str(video_path),
        "-vf", vf,
        "-c:v", "libx264", "-crf", "20",
        "-c:a", "copy",
        str(out_path),
    ])
    if not res["ok"]:
        return {"ok": False, "error": "ffmpeg drawtext failed", "stderr": res["stderr"]}
    return {"ok": True, "path": str(out_path), "text": text, "duration": duration_seconds}
