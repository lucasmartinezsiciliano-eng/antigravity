from __future__ import annotations

from typing import Any


class CentrumStudioError(Exception):
    error_code: str = "UNKNOWN_ERROR"
    suggestion: str = ""
    recovery_action: str = "retry"

    def __init__(
        self,
        message: str,
        *,
        error_code: str | None = None,
        suggestion: str | None = None,
        recovery_action: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if error_code:
            self.error_code = error_code
        if suggestion:
            self.suggestion = suggestion
        if recovery_action:
            self.recovery_action = recovery_action
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        out = {
            "error": True,
            "error_code": self.error_code,
            "message": self.message,
            "suggestion": self.suggestion,
            "recovery_action": self.recovery_action,
        }
        if self.details:
            out["details"] = self.details
        return out


class SoulNotFoundError(CentrumStudioError):
    error_code = "SOUL_NOT_FOUND"
    suggestion = "Run: centrum-studio soul list — then activate with: centrum-studio soul activate <name> <version>"
    recovery_action = "check_soul_file"


class SoulInvalidError(CentrumStudioError):
    error_code = "SOUL_INVALID"
    suggestion = "Validate soul.json schema (see centrum_studio/soul/schema.py)"
    recovery_action = "fix_soul_manifest"


class ComfyUIUnavailableError(CentrumStudioError):
    error_code = "COMFYUI_UNAVAILABLE"
    suggestion = "Check ComfyUI is running: curl http://localhost:8188/system_stats"
    recovery_action = "start_comfyui"


class GPUPausedError(CentrumStudioError):
    error_code = "GPU_PAUSED"
    suggestion = "GPU is in agents mode (Mon-Fri). Jobs execute Saturday. Set /srv/centrum-studio/gpu_mode to saturday_video or saturday_images to override."
    recovery_action = "wait_for_gpu_window"


class JobNotFoundError(CentrumStudioError):
    error_code = "JOB_NOT_FOUND"
    suggestion = "List jobs: query DB jobs table"
    recovery_action = "verify_job_id"


class SceneNotFoundError(CentrumStudioError):
    error_code = "SCENE_NOT_FOUND"
    suggestion = "Use list_renders to find existing scene_ids"
    recovery_action = "verify_scene_id"


class EvaluationFailedError(CentrumStudioError):
    error_code = "EVALUATION_FAILED"
    suggestion = "Use regenerate_scene with adjustments (e.g. {'strength_delta': 0.05, 'cfg_delta': 0.5})"
    recovery_action = "regenerate_with_adjustments"


class PLURUnavailableError(CentrumStudioError):
    error_code = "PLUR_UNAVAILABLE"
    suggestion = "Falling back to local SQLite engrams store"
    recovery_action = "local_fallback"


class IdempotencyConflictError(CentrumStudioError):
    error_code = "IDEMPOTENCY_CONFLICT"
    suggestion = "Reuse the previous job_id returned by the original call"
    recovery_action = "use_existing_job"
