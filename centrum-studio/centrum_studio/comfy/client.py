from __future__ import annotations

import asyncio
import copy
import json
import random
import uuid
from importlib import resources
from pathlib import Path
from typing import Any, Awaitable, Callable

import httpx
import structlog
import websockets

from ..config import get_config
from ..errors import ComfyUIUnavailableError
from ..soul.schema import Soul

log = structlog.get_logger("centrum_studio.comfy")

ProgressCallback = Callable[[dict[str, Any]], Awaitable[None]]


class ComfyClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or get_config().comfyui_url).rstrip("/")
        self.client_id = uuid.uuid4().hex
        self._http: httpx.AsyncClient | None = None

    async def _http_client(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0))
        return self._http

    async def close(self) -> None:
        if self._http is not None and not self._http.is_closed:
            await self._http.aclose()

    async def health(self) -> bool:
        try:
            client = await self._http_client()
            r = await client.get(f"{self.base_url}/system_stats")
            return r.status_code == 200
        except (httpx.HTTPError, OSError):
            return False

    async def submit_prompt(self, workflow: dict[str, Any]) -> str:
        client = await self._http_client()
        try:
            r = await client.post(
                f"{self.base_url}/prompt",
                json={"prompt": workflow, "client_id": self.client_id},
            )
        except httpx.HTTPError as e:
            raise ComfyUIUnavailableError(f"ComfyUI POST /prompt failed: {e}") from e
        if r.status_code != 200:
            raise ComfyUIUnavailableError(
                f"ComfyUI rejected prompt: HTTP {r.status_code} — {r.text[:300]}",
                details={"status": r.status_code},
            )
        data = r.json()
        prompt_id = data.get("prompt_id")
        if not prompt_id:
            raise ComfyUIUnavailableError(
                "ComfyUI did not return prompt_id",
                details={"response": data},
            )
        return prompt_id

    async def wait_for_completion(
        self,
        prompt_id: str,
        on_progress: ProgressCallback | None = None,
        timeout_seconds: float = 600.0,
    ) -> dict[str, Any]:
        ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/ws?clientId={self.client_id}"
        backoff = 1.0
        deadline = asyncio.get_event_loop().time() + timeout_seconds
        while True:
            now = asyncio.get_event_loop().time()
            if now >= deadline:
                raise ComfyUIUnavailableError(
                    f"Timeout waiting for ComfyUI prompt {prompt_id}",
                    error_code="COMFYUI_TIMEOUT",
                )
            try:
                async with websockets.connect(ws_url, max_size=2**24, ping_interval=20) as ws:
                    backoff = 1.0
                    while True:
                        remaining = deadline - asyncio.get_event_loop().time()
                        if remaining <= 0:
                            raise ComfyUIUnavailableError(
                                f"Timeout waiting for ComfyUI prompt {prompt_id}",
                                error_code="COMFYUI_TIMEOUT",
                            )
                        raw = await asyncio.wait_for(ws.recv(), timeout=min(remaining, 60.0))
                        if isinstance(raw, bytes):
                            continue
                        msg = json.loads(raw)
                        msg_type = msg.get("type")
                        data = msg.get("data", {})
                        if data.get("prompt_id") and data["prompt_id"] != prompt_id:
                            continue
                        if msg_type == "progress" and on_progress is not None:
                            await on_progress({
                                "type": "progress",
                                "value": data.get("value"),
                                "max": data.get("max"),
                            })
                        elif msg_type == "executing":
                            node = data.get("node")
                            if node is None and data.get("prompt_id") == prompt_id:
                                history = await self.get_history(prompt_id)
                                return history
                            if on_progress is not None:
                                await on_progress({"type": "executing", "node": node})
                        elif msg_type == "execution_error":
                            raise ComfyUIUnavailableError(
                                f"ComfyUI execution error: {data}",
                                error_code="COMFYUI_EXECUTION_ERROR",
                                details={"data": data},
                            )
            except (websockets.WebSocketException, OSError, asyncio.TimeoutError) as e:
                log.warning("comfy.ws_reconnect", error=str(e), backoff=backoff)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 15.0)
                continue

    async def get_history(self, prompt_id: str) -> dict[str, Any]:
        client = await self._http_client()
        r = await client.get(f"{self.base_url}/history/{prompt_id}")
        if r.status_code != 200:
            raise ComfyUIUnavailableError(
                f"ComfyUI GET /history failed: HTTP {r.status_code}",
                details={"status": r.status_code},
            )
        data = r.json()
        entry = data.get(prompt_id) or {}
        return entry

    async def download_output(
        self,
        filename: str,
        subfolder: str = "",
        type_: str = "output",
        dest: Path | None = None,
    ) -> Path:
        client = await self._http_client()
        params = {"filename": filename, "subfolder": subfolder, "type": type_}
        try:
            async with client.stream("GET", f"{self.base_url}/view", params=params) as r:
                if r.status_code != 200:
                    raise ComfyUIUnavailableError(
                        f"ComfyUI GET /view failed: HTTP {r.status_code}",
                        details={"params": params},
                    )
                cfg = get_config()
                dest_path = dest or (cfg.cache_dir / filename)
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                with dest_path.open("wb") as f:
                    async for chunk in r.aiter_bytes(chunk_size=1 << 20):
                        f.write(chunk)
                return dest_path
        except httpx.HTTPError as e:
            raise ComfyUIUnavailableError(f"ComfyUI download failed: {e}") from e

    def load_workflow_template(self, name: str) -> dict[str, Any]:
        candidates = [
            Path(__file__).parent / "workflows" / name,
            get_config().data_dir / "workflows" / name,
        ]
        for path in candidates:
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        try:
            with resources.files("centrum_studio.comfy.workflows").joinpath(name).open("r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, ModuleNotFoundError) as e:
            raise ComfyUIUnavailableError(
                f"Workflow template not found: {name}",
                error_code="WORKFLOW_NOT_FOUND",
                details={"candidates": [str(c) for c in candidates]},
            ) from e

    def inject_soul(
        self,
        workflow: dict[str, Any],
        soul: Soul,
        soul_root: Path,
        prompt: str,
        seed: int | None = None,
        width: int = 720,
        height: int = 1280,
        frames: int = 81,
    ) -> dict[str, Any]:
        wf = copy.deepcopy(workflow)
        if seed is None:
            seed = random.randint(0, 2**31 - 1)
        weights = soul.recommended_weights

        replacements = {
            "__PROMPT__": prompt,
            "__SEED__": seed,
            "__WIDTH__": width,
            "__HEIGHT__": height,
            "__FRAMES__": frames,
            "__LORA_HIGH__": soul.assets.lora_wan22_high or "",
            "__LORA_LOW__": soul.assets.lora_wan22_low or "",
            "__LORA_FLUX__": soul.assets.lora_flux or "",
            "__LORA_STRENGTH__": weights.lora_strength,
            "__IP_ADAPTER_REF__": str(soul_root / soul.assets.ip_adapter_ref) if soul.assets.ip_adapter_ref else "",
            "__IP_ADAPTER_WEIGHT__": weights.ip_adapter_weight,
            "__PULID_WEIGHT__": weights.pulid_weight,
            "__CONTROLNET_POSE_WEIGHT__": weights.controlnet_pose_weight,
            "__CFG__": weights.cfg,
            "__STEPS__": weights.steps,
            "__TRIGGER_TOKEN__": soul.trigger_token,
        }

        def _walk(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: _walk(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_walk(x) for x in obj]
            if isinstance(obj, str):
                if obj in replacements:
                    return replacements[obj]
                out = obj
                for placeholder, value in replacements.items():
                    if placeholder in out:
                        out = out.replace(placeholder, str(value))
                return out
            return obj

        return _walk(wf)

    def find_video_outputs(self, history: dict[str, Any]) -> list[dict[str, Any]]:
        outputs = history.get("outputs", {}) or {}
        videos: list[dict[str, Any]] = []
        for node_outputs in outputs.values():
            for key in ("gifs", "videos", "images", "files"):
                for item in node_outputs.get(key, []) or []:
                    if isinstance(item, dict) and "filename" in item:
                        videos.append(item)
        return videos


_client: ComfyClient | None = None


def get_comfy_client() -> ComfyClient:
    global _client
    if _client is None:
        _client = ComfyClient()
    return _client
