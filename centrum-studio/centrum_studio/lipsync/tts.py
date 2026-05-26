from __future__ import annotations

import asyncio
import shutil
import subprocess
from pathlib import Path
from typing import Any

import structlog

from ..config import get_config

log = structlog.get_logger("centrum_studio.lipsync.tts")


class ChatterboxTTS:
    """Wrapper around Chatterbox TTS.

    Tries the Python library `chatterbox_tts` first, falling back to a CLI
    `chatterbox-tts` binary, and finally a graceful failure that returns the
    error in a structured way for the agent to handle.
    """

    def __init__(self, voice_id: str | None = None) -> None:
        self.voice_id = voice_id
        self._model = None

    def _ensure_model(self):
        if self._model is not None:
            return self._model
        try:
            from chatterbox.tts import ChatterboxTTS as _CT
        except ImportError:
            try:
                from chatterbox_tts import ChatterboxTTS as _CT  # type: ignore
            except ImportError:
                self._model = None
                return None
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            device = "cpu"
        try:
            self._model = _CT.from_pretrained(device=device)
        except Exception as e:
            log.warning("chatterbox.from_pretrained_failed", error=str(e))
            self._model = None
        return self._model

    def _synthesize_lib(self, text: str, out_path: Path) -> bool:
        model = self._ensure_model()
        if model is None:
            return False
        try:
            audio = model.generate(text, audio_prompt_path=self.voice_id) if self.voice_id else model.generate(text)
            import torchaudio
            torchaudio.save(str(out_path), audio, getattr(model, "sr", 24000))
            return True
        except Exception as e:
            log.warning("chatterbox.generate_failed", error=str(e))
            return False

    def _synthesize_cli(self, text: str, out_path: Path) -> bool:
        bin_path = shutil.which("chatterbox-tts") or shutil.which("chatterbox")
        if not bin_path:
            return False
        args = [bin_path, "--text", text, "--out", str(out_path)]
        if self.voice_id:
            args += ["--voice", self.voice_id]
        try:
            r = subprocess.run(args, capture_output=True, text=True, timeout=120)
            return r.returncode == 0 and out_path.exists()
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            log.warning("chatterbox.cli_failed", error=str(e))
            return False

    def synthesize_sync(self, text: str, out_path: Path) -> dict[str, Any]:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if self._synthesize_lib(text, out_path):
            return {"ok": True, "path": str(out_path), "engine": "chatterbox_lib"}
        if self._synthesize_cli(text, out_path):
            return {"ok": True, "path": str(out_path), "engine": "chatterbox_cli"}
        return {
            "ok": False,
            "error": "Chatterbox TTS not available — install chatterbox-tts python package or CLI",
            "error_code": "TTS_UNAVAILABLE",
        }

    async def synthesize(self, text: str, out_path: Path) -> dict[str, Any]:
        return await asyncio.to_thread(self.synthesize_sync, text, out_path)


async def synthesize_tts(text: str, voice_id: str | None, out_path: Path | None = None) -> dict[str, Any]:
    cfg = get_config()
    if out_path is None:
        out_path = cfg.cache_dir / f"tts_{abs(hash(text)) % 10**10}.wav"
    tts = ChatterboxTTS(voice_id=voice_id)
    return await tts.synthesize(text, out_path)
