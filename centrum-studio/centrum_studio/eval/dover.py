from __future__ import annotations

import asyncio
from pathlib import Path

import structlog

log = structlog.get_logger("centrum_studio.eval.dover")

_metric = None


def _ensure_metric():
    global _metric
    if _metric is not None:
        return _metric
    try:
        import pyiqa
        import torch
    except ImportError as e:
        raise RuntimeError("pyiqa + torch required — pip install pyiqa torch") from e
    device = "cuda" if torch.cuda.is_available() else "cpu"
    _metric = pyiqa.create_metric("dover", device=device)
    return _metric


def _measure_sync(video_path: Path) -> float:
    metric = _ensure_metric()
    try:
        score = float(metric(str(video_path)))
    except Exception as e:
        log.warning("dover.failed", error=str(e), path=str(video_path))
        return 0.0
    if score > 1.5:
        score = score / 100.0
    return max(0.0, min(1.0, score))


async def dover_score(video_path: Path) -> float:
    try:
        return await asyncio.to_thread(_measure_sync, video_path)
    except RuntimeError as e:
        log.warning("dover.unavailable", error=str(e))
        return 0.0
