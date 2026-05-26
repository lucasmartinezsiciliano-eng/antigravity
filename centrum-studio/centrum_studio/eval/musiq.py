from __future__ import annotations

import asyncio
from pathlib import Path

import numpy as np
import structlog

log = structlog.get_logger("centrum_studio.eval.musiq")

_metric = None


def _ensure_metric():
    global _metric
    if _metric is not None:
        return _metric
    try:
        import pyiqa
        import torch
    except ImportError as e:
        raise RuntimeError("pyiqa + torch required") from e
    device = "cuda" if torch.cuda.is_available() else "cpu"
    _metric = pyiqa.create_metric("musiq", device=device)
    return _metric


def _measure_sync(video_path: Path, sample_count: int = 6) -> float:
    metric = _ensure_metric()
    try:
        import cv2
    except ImportError as e:
        raise RuntimeError("opencv-python-headless required") from e
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return 0.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if total <= 0:
        cap.release()
        return 0.0
    indices = np.linspace(0, total - 1, num=min(sample_count, total)).astype(int)
    scores: list[float] = []
    import tempfile
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ok, frame = cap.read()
        if not ok:
            continue
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            cv2.imwrite(tmp.name, frame)
            try:
                s = float(metric(tmp.name))
                scores.append(s)
            except Exception as e:
                log.warning("musiq.frame_failed", error=str(e))
            finally:
                Path(tmp.name).unlink(missing_ok=True)
    cap.release()
    if not scores:
        return 0.0
    return float(np.median(scores))


async def musiq_score(video_path: Path) -> float:
    try:
        return await asyncio.to_thread(_measure_sync, video_path)
    except RuntimeError as e:
        log.warning("musiq.unavailable", error=str(e))
        return 0.0
