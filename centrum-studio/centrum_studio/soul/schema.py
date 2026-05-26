from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SoulAssets(BaseModel):
    model_config = ConfigDict(extra="allow")

    lora_wan22_high: str | None = None
    lora_wan22_low: str | None = None
    lora_flux: str | None = None
    ip_adapter_ref: str | None = None
    arcface_canonical: str | None = None
    pulid_ref: str | None = None


class SoulWeights(BaseModel):
    model_config = ConfigDict(extra="allow")

    lora_strength: float = 0.8
    ip_adapter_weight: float = 0.7
    pulid_weight: float = 0.6
    controlnet_pose_weight: float = 0.85
    cfg: float = 4.5
    steps: int = 28


class SoulEvaluation(BaseModel):
    model_config = ConfigDict(extra="allow")

    min_arcface_similarity: float = 0.62
    min_dover_score: float = 0.55
    min_musiq_score: float = 55.0
    max_temporal_lpips: float = 0.18
    min_syncnet_lsec: float = 6.5


class Soul(BaseModel):
    model_config = ConfigDict(extra="allow")

    soul_id: str
    version: str
    character_name: str
    trigger_token: str
    assets: SoulAssets = Field(default_factory=SoulAssets)
    recommended_weights: SoulWeights = Field(default_factory=SoulWeights)
    evaluation: SoulEvaluation = Field(default_factory=SoulEvaluation)
    voice_id: str | None = None
    created_at: str | datetime | None = None
    notes: str | None = None

    def asset_path(self, root: str, key: str) -> str | None:
        rel = getattr(self.assets, key, None)
        if not rel:
            return None
        return f"{root.rstrip('/')}/{rel}"

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=False)
