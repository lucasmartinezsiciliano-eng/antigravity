from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import structlog

from ..soul.schema import Soul
from .arcface import arcface_similarity
from .dover import dover_score
from .lpips_temporal import temporal_lpips
from .musiq import musiq_score
from .syncnet import syncnet_lse_c

log = structlog.get_logger("centrum_studio.eval")


@dataclass
class EvaluationResult:
    arcface_similarity: float
    dover_score: float
    musiq_score: float
    temporal_lpips: float
    syncnet_lsec: float
    passed: bool
    failures: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "arcface_similarity": self.arcface_similarity,
            "dover_score": self.dover_score,
            "musiq_score": self.musiq_score,
            "temporal_lpips": self.temporal_lpips,
            "syncnet_lsec": self.syncnet_lsec,
            "passed_thresholds": self.passed,
            "failures": self.failures,
        }


class Evaluator:
    def __init__(self, soul: Soul, soul_root: Path) -> None:
        self.soul = soul
        self.soul_root = soul_root

    async def evaluate(self, video_path: Path, lipsynced: bool = False) -> EvaluationResult:
        arcface_emb = self.soul.assets.arcface_canonical
        canonical_path = (self.soul_root / arcface_emb) if arcface_emb else None

        arc = 0.0
        if canonical_path is not None and canonical_path.exists():
            arc = await arcface_similarity(video_path, canonical_path)
        dover = await dover_score(video_path)
        musiq = await musiq_score(video_path)
        lpips_v = await temporal_lpips(video_path)
        sync = await syncnet_lse_c(video_path) if lipsynced else 0.0

        thresholds = self.soul.evaluation
        failures: list[str] = []
        if arc < thresholds.min_arcface_similarity:
            failures.append(f"arcface_similarity {arc:.3f} < {thresholds.min_arcface_similarity}")
        if dover < thresholds.min_dover_score:
            failures.append(f"dover_score {dover:.3f} < {thresholds.min_dover_score}")
        if musiq < thresholds.min_musiq_score:
            failures.append(f"musiq_score {musiq:.2f} < {thresholds.min_musiq_score}")
        if lpips_v > thresholds.max_temporal_lpips:
            failures.append(f"temporal_lpips {lpips_v:.3f} > {thresholds.max_temporal_lpips}")
        if lipsynced and sync < thresholds.min_syncnet_lsec:
            failures.append(f"syncnet_lsec {sync:.2f} < {thresholds.min_syncnet_lsec}")

        return EvaluationResult(
            arcface_similarity=arc,
            dover_score=dover,
            musiq_score=musiq,
            temporal_lpips=lpips_v,
            syncnet_lsec=sync,
            passed=len(failures) == 0,
            failures=failures,
        )


def get_evaluator(soul: Soul, soul_root: Path) -> Evaluator:
    return Evaluator(soul, soul_root)
