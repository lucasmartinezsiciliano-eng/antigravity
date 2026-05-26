from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from typing import Any


def ffmpeg_bin() -> str:
    return shutil.which("ffmpeg") or "ffmpeg"


def ffprobe_bin() -> str:
    return shutil.which("ffprobe") or "ffprobe"


async def run_ffmpeg(args: list[str]) -> dict[str, Any]:
    cmd = [ffmpeg_bin(), "-y", "-hide_banner", "-loglevel", "error", *args]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return {
        "ok": (proc.returncode or 0) == 0,
        "returncode": proc.returncode,
        "stdout": stdout.decode(errors="ignore"),
        "stderr": stderr.decode(errors="ignore"),
    }


async def probe_duration(path: Path) -> float:
    proc = await asyncio.create_subprocess_exec(
        ffprobe_bin(),
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, _ = await proc.communicate()
    try:
        return float(out.decode().strip())
    except (ValueError, AttributeError):
        return 0.0
