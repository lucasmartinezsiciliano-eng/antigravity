from __future__ import annotations

import asyncio
from pathlib import Path

import numpy as np
import structlog

log = structlog.get_logger("centrum_studio.eval.lpips")

_model = None
_torch = None


def _ensure_model():
    global _model, _torch
    if _model is not None:
        return _model, _torch
    try:
        import lpips
        import torch
    except ImportError as e:
        raise RuntimeError("lpips + torch required — pip install lpips torch") from e
    _torch = torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = lpips.LPIPS(net="alex").to(device).eval()
    _model = (model, device)
    return _model, _torch


def _frame_to_tensor(frame_bgr: np.ndarray, torch):
    img = frame_bgr[:, :, ::-1].astype(np.float32) / 255.0
    img = (img - 0.5) * 2.0
    return torch.from_numpy(img.transpose(2, 0, 1)).unsqueeze(0)


def _measure_sync(video_path: Path, sample_count: int = 16) -> float:
    (model, device), torch = _ensure_model()
    try:
        import cv2
    except ImportError as e:
        raise RuntimeError("opencv-python-headless required") from e
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return 1.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if total < 2:
        cap.release()
        return 0.0
    indices = np.linspace(0, total - 1, num=min(sample_count, total)).astype(int)
    frames: list[np.ndarray] = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ok, frame = cap.read()
        if ok:
            frames.append(frame)
    cap.release()
    if len(frames) < 2:
        return 0.0
    distances: list[float] = []
    with torch.no_grad():
        prev = _frame_to_tensor(frames[0], torch).to(device)
        for frame in frames[1:]:
            cur = _frame_to_tensor(frame, torch).to(device)
            d = float(model(prev, cur).item())
            distances.append(d)
            prev = cur
    return float(np.mean(distances)) if distances else 0.0


async def temporal_lpips(video_path: Path) -> float:
    try:
        return await asyncio.to_thread(_measure_sync, video_path)
    except RuntimeError as e:
        log.warning("lpips.unavailable", error=str(e))
        return 0.0
