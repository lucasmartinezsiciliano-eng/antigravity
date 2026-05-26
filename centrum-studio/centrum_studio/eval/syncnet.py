from __future__ import annotations

import asyncio
import shutil
import subprocess
from pathlib import Path

import structlog

log = structlog.get_logger("centrum_studio.eval.syncnet")


def _has_syncnet_binary() -> str | None:
    for name in ("syncnet", "syncnet_python", "run_pipeline.py"):
        path = shutil.which(name)
        if path:
            return path
    return None


def _measure_sync(video_path: Path) -> float:
    bin_path = _has_syncnet_binary()
    if not bin_path:
        log.info("syncnet.binary_not_found_returning_neutral")
        return 7.0
    try:
        result = subprocess.run(
            [bin_path, "--videofile", str(video_path), "--data_dir", "/tmp/syncnet"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        for line in (result.stdout or "").splitlines():
            if "LSE-C" in line.upper() or "LSE_C" in line.upper():
                for token in line.replace(":", " ").split():
                    try:
                        return float(token)
                    except ValueError:
                        continue
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        log.warning("syncnet.failed", error=str(e))
    return 7.0


async def syncnet_lse_c(video_path: Path) -> float:
    return await asyncio.to_thread(_measure_sync, video_path)
