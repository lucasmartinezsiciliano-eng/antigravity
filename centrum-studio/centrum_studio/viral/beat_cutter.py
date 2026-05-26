from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import structlog

from ..config import get_config
from ._ffmpeg import probe_duration, run_ffmpeg

log = structlog.get_logger("centrum_studio.viral.beat")


def _detect_beats_sync(music_path: Path) -> tuple[float, list[float]]:
    try:
        import librosa
        import numpy as np
    except ImportError:
        return 0.0, []
    y, sr = librosa.load(str(music_path), sr=None, mono=True)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    return float(tempo), [float(t) for t in beat_times]


async def cut_to_beat(video_path: Path, music_path: Path, out_path: Path | None = None) -> dict[str, Any]:
    cfg = get_config()
    if out_path is None:
        out_path = cfg.renders_dir / f"{video_path.stem}_beatcut.mp4"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    bpm, beats = await asyncio.to_thread(_detect_beats_sync, music_path)
    if not beats:
        return {"ok": False, "error": "No beats detected (librosa unavailable?)", "error_code": "NO_BEATS"}

    video_duration = await probe_duration(video_path)
    if video_duration <= 0:
        return {"ok": False, "error": "Cannot probe video duration", "error_code": "PROBE_FAILED"}

    cut_points = [b for b in beats if b < video_duration]
    if len(cut_points) < 2:
        cut_points = [0.0, video_duration]

    segments_dir = cfg.cache_dir / f"beat_{video_path.stem}"
    segments_dir.mkdir(parents=True, exist_ok=True)
    segment_paths: list[Path] = []
    for i in range(len(cut_points) - 1):
        start = cut_points[i]
        end = min(cut_points[i + 1], video_duration)
        seg_path = segments_dir / f"seg_{i:04d}.mp4"
        r = await run_ffmpeg([
            "-ss", f"{start:.3f}",
            "-i", str(video_path),
            "-to", f"{end - start:.3f}",
            "-c:v", "libx264", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            str(seg_path),
        ])
        if r["ok"] and seg_path.exists():
            segment_paths.append(seg_path)

    if not segment_paths:
        return {"ok": False, "error": "No segments produced", "error_code": "SEGMENTATION_FAILED"}

    concat_file = segments_dir / "concat.txt"
    concat_file.write_text(
        "\n".join(f"file '{p.as_posix()}'" for p in segment_paths),
        encoding="utf-8",
    )
    final = await run_ffmpeg([
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-i", str(music_path),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(out_path),
    ])
    if not final["ok"]:
        return {"ok": False, "error": "Concat failed", "stderr": final["stderr"]}

    for p in segment_paths:
        p.unlink(missing_ok=True)
    concat_file.unlink(missing_ok=True)
    try:
        segments_dir.rmdir()
    except OSError:
        pass

    return {"ok": True, "path": str(out_path), "bpm": bpm, "cuts": len(cut_points) - 1}
