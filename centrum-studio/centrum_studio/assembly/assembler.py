from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import structlog

from ..config import get_config

log = structlog.get_logger("centrum_studio.assembly")


def _assemble_sync(
    scene_paths: list[Path],
    out_path: Path,
    music_track: Path | None,
    include_subtitles: bool,
    branding: bool,
) -> dict[str, Any]:
    try:
        from moviepy.editor import (
            AudioFileClip,
            CompositeAudioClip,
            CompositeVideoClip,
            TextClip,
            VideoFileClip,
            concatenate_videoclips,
            afx,
        )
    except ImportError as e:
        return {"ok": False, "error": f"moviepy required: {e}", "error_code": "MOVIEPY_MISSING"}

    if not scene_paths:
        return {"ok": False, "error": "No scenes provided", "error_code": "EMPTY_SCENE_LIST"}

    clips = []
    try:
        for p in scene_paths:
            if not p.exists():
                return {
                    "ok": False,
                    "error": f"Scene file missing: {p}",
                    "error_code": "SCENE_FILE_MISSING",
                }
            clips.append(VideoFileClip(str(p)))
        final = concatenate_videoclips(clips, method="compose")

        if music_track and music_track.exists():
            music = AudioFileClip(str(music_track)).fx(afx.audio_loop, duration=final.duration).volumex(0.25)
            if final.audio is not None:
                final = final.set_audio(CompositeAudioClip([final.audio, music]))
            else:
                final = final.set_audio(music)

        overlays = []
        if branding:
            try:
                brand = TextClip(
                    "centrum.studio",
                    fontsize=28,
                    color="white",
                    method="label",
                    stroke_color="black",
                    stroke_width=1,
                ).set_duration(final.duration).set_position(("right", "bottom")).margin(right=24, bottom=24, opacity=0)
                overlays.append(brand)
            except Exception as e:
                log.warning("assembly.branding_skipped", error=str(e))

        if include_subtitles:
            log.info("assembly.subtitles_requested_no_op")

        if overlays:
            final = CompositeVideoClip([final, *overlays])

        out_path.parent.mkdir(parents=True, exist_ok=True)
        final.write_videofile(
            str(out_path),
            codec="libx264",
            audio_codec="aac",
            fps=final.fps or 24,
            preset="medium",
            threads=4,
            logger=None,
        )
        return {"ok": True, "path": str(out_path), "duration": final.duration}
    except Exception as e:
        log.exception("assembly.failed")
        return {"ok": False, "error": str(e), "error_code": "ASSEMBLY_FAILED"}
    finally:
        for c in clips:
            try:
                c.close()
            except Exception:
                pass


async def assemble_video(
    scene_paths: list[Path],
    project_id: str,
    music_track: Path | None = None,
    include_subtitles: bool = False,
    branding: bool = True,
) -> dict[str, Any]:
    cfg = get_config()
    out_path = cfg.renders_dir / f"{project_id}_final.mp4"
    return await asyncio.to_thread(
        _assemble_sync, scene_paths, out_path, music_track, include_subtitles, branding
    )
