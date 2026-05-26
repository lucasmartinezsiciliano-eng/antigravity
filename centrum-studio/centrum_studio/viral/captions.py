from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import structlog

from ..config import get_config
from ._ffmpeg import run_ffmpeg

log = structlog.get_logger("centrum_studio.viral.captions")


STYLES = {
    "default": {"font": "Sans-Bold", "size": 48, "color": "white", "border": "black", "border_w": 6},
    "bold": {"font": "Sans-Bold", "size": 72, "color": "white", "border": "black", "border_w": 10},
    "neon": {"font": "Sans-Bold", "size": 56, "color": "#39FF14", "border": "#FF00FF", "border_w": 6},
    "minimal": {"font": "Sans", "size": 40, "color": "white", "border": "black", "border_w": 3},
}


def _transcribe_words(audio_path: Path) -> list[dict[str, Any]]:
    try:
        import whisper
    except ImportError:
        log.warning("captions.whisper_unavailable")
        return []
    model = whisper.load_model("base")
    result = model.transcribe(str(audio_path), word_timestamps=True)
    words: list[dict[str, Any]] = []
    for seg in result.get("segments", []):
        for w in seg.get("words", []) or []:
            words.append({
                "word": (w.get("word") or "").strip(),
                "start": float(w.get("start", 0.0)),
                "end": float(w.get("end", 0.0)),
            })
    return words


def _build_drawtext_filters(words: list[dict[str, Any]], style: dict[str, Any]) -> str:
    parts: list[str] = []
    color = style["color"]
    border = style["border"]
    border_w = style["border_w"]
    size = style["size"]
    for w in words:
        text = w["word"].replace("'", "\\'").replace(":", r"\:").replace(",", r"\,")
        if not text:
            continue
        start = max(0.0, w["start"])
        end = max(start + 0.05, w["end"])
        filt = (
            f"drawtext=text='{text}':"
            f"fontsize={size}:fontcolor={color}:"
            f"bordercolor={border}:borderw={border_w}:"
            f"x=(w-text_w)/2:y=h*0.78:"
            f"enable='between(t,{start:.3f},{end:.3f})'"
        )
        parts.append(filt)
    return ",".join(parts)


async def apply_captions_viral(
    video_path: Path,
    style: str = "default",
    out_path: Path | None = None,
) -> dict[str, Any]:
    cfg = get_config()
    if out_path is None:
        out_path = cfg.renders_dir / f"{video_path.stem}_captioned.mp4"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    style_spec = STYLES.get(style, STYLES["default"])

    audio_tmp = cfg.cache_dir / f"{video_path.stem}_audio.wav"
    audio_tmp.parent.mkdir(parents=True, exist_ok=True)
    extract = await run_ffmpeg(["-i", str(video_path), "-vn", "-ac", "1", "-ar", "16000", str(audio_tmp)])
    if not extract["ok"]:
        return {"ok": False, "error": "Failed to extract audio", "stderr": extract["stderr"]}

    words = await asyncio.to_thread(_transcribe_words, audio_tmp)
    audio_tmp.unlink(missing_ok=True)

    if not words:
        return {"ok": False, "error": "No words transcribed", "error_code": "TRANSCRIPTION_EMPTY"}

    filters = _build_drawtext_filters(words, style_spec)
    res = await run_ffmpeg([
        "-i", str(video_path),
        "-vf", filters,
        "-c:v", "libx264", "-crf", "20",
        "-c:a", "copy",
        str(out_path),
    ])
    if not res["ok"]:
        return {"ok": False, "error": "ffmpeg drawtext failed", "stderr": res["stderr"]}
    return {"ok": True, "path": str(out_path), "word_count": len(words), "style": style}
