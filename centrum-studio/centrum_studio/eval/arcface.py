from __future__ import annotations

import asyncio
from pathlib import Path

import numpy as np
import structlog

log = structlog.get_logger("centrum_studio.eval.arcface")

_app = None


def _ensure_app():
    global _app
    if _app is not None:
        return _app
    try:
        from insightface.app import FaceAnalysis
    except ImportError as e:
        raise RuntimeError(
            "insightface not available — install with: pip install insightface onnxruntime-gpu"
        ) from e
    app = FaceAnalysis(name="buffalo_l", providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
    app.prepare(ctx_id=0, det_size=(640, 640))
    _app = app
    return _app


def _read_video_frames(path: Path, sample_count: int = 8) -> list[np.ndarray]:
    try:
        import cv2
    except ImportError as e:
        raise RuntimeError("opencv-python-headless required") from e
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {path}")
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    frames: list[np.ndarray] = []
    if total <= 0:
        ok, frame = cap.read()
        if ok:
            frames.append(frame)
        cap.release()
        return frames
    indices = np.linspace(0, max(total - 1, 0), num=min(sample_count, total)).astype(int)
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ok, frame = cap.read()
        if ok:
            frames.append(frame)
    cap.release()
    return frames


def _embedding_for_image(img_bgr: np.ndarray) -> np.ndarray | None:
    app = _ensure_app()
    faces = app.get(img_bgr)
    if not faces:
        return None
    return max(faces, key=lambda f: float(f.det_score)).normed_embedding


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    a = a / (np.linalg.norm(a) + 1e-8)
    b = b / (np.linalg.norm(b) + 1e-8)
    return float(np.clip(np.dot(a, b), -1.0, 1.0))


def _measure_sync(video_path: Path, canonical_embedding_path: Path) -> float:
    try:
        canonical = np.load(canonical_embedding_path)
    except Exception as e:
        log.warning("arcface.canonical_load_failed", error=str(e), path=str(canonical_embedding_path))
        return 0.0
    frames = _read_video_frames(video_path)
    if not frames:
        return 0.0
    sims: list[float] = []
    for f in frames:
        emb = _embedding_for_image(f)
        if emb is not None:
            sims.append(_cosine(canonical, emb))
    if not sims:
        return 0.0
    sims_arr = np.array(sims, dtype=np.float32)
    return float(np.median(sims_arr))


async def arcface_similarity(video_path: Path, canonical_embedding_path: Path) -> float:
    try:
        return await asyncio.to_thread(_measure_sync, video_path, canonical_embedding_path)
    except RuntimeError as e:
        log.warning("arcface.unavailable", error=str(e))
        return 0.0
