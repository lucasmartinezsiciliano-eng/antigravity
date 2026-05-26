from __future__ import annotations

from typing import Any

import httpx
import structlog

from ..config import get_config
from ..store import get_store, new_id

log = structlog.get_logger("centrum_studio.plur")


class PLURBridge:
    def __init__(self, base_url: str | None = None, scope: str | None = None) -> None:
        cfg = get_config()
        self.base_url = (base_url or cfg.plur_url).rstrip("/")
        self.scope = scope or cfg.plur_scope
        self._client: httpx.AsyncClient | None = None
        self._available: bool | None = None

    async def _http(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=2.5))
        return self._client

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()

    async def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            client = await self._http()
            r = await client.get(f"{self.base_url}/health")
            self._available = r.status_code == 200
        except (httpx.HTTPError, OSError):
            self._available = False
        return self._available

    async def save_engram(
        self,
        outcome: str,
        lesson: str,
        scene_id: str | None = None,
        recommended_params: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        strength: float = 1.0,
    ) -> dict[str, Any]:
        engram_id = new_id("eng")
        body = {
            "engram_id": engram_id,
            "scope": self.scope,
            "outcome": outcome,
            "lesson": lesson,
            "scene_id": scene_id,
            "recommended_params": recommended_params or {},
            "tags": tags or [],
            "strength": strength,
        }
        synced = False
        if await self.is_available():
            try:
                client = await self._http()
                r = await client.post(f"{self.base_url}/engrams", json=body)
                if 200 <= r.status_code < 300:
                    synced = True
            except (httpx.HTTPError, OSError) as e:
                log.warning("plur.save_failed_fallback_local", error=str(e))
                self._available = False

        store = get_store()
        await store.save_engram(
            engram_id=engram_id,
            outcome=outcome,
            lesson=lesson,
            scene_id=scene_id,
            recommended_params=recommended_params,
            tags=tags,
            strength=strength,
            synced_to_plur=synced,
        )
        return {"engram_id": engram_id, "saved": True, "synced_to_plur": synced}

    async def search(
        self,
        query: str,
        tags_hint: list[str] | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        if await self.is_available():
            try:
                client = await self._http()
                params: dict[str, Any] = {"query": query, "scope": self.scope, "limit": limit}
                if tags_hint:
                    params["tags"] = ",".join(tags_hint)
                r = await client.get(f"{self.base_url}/engrams/search", params=params)
                if r.status_code == 200:
                    data = r.json()
                    engrams = data.get("engrams") or data.get("results") or []
                    if engrams:
                        return engrams[:limit]
            except (httpx.HTTPError, OSError) as e:
                log.warning("plur.search_failed_fallback_local", error=str(e))
                self._available = False

        store = get_store()
        return await store.search_engrams_local(query=query, tags_hint=tags_hint, limit=limit)


_bridge: PLURBridge | None = None


def get_plur_bridge() -> PLURBridge:
    global _bridge
    if _bridge is None:
        _bridge = PLURBridge()
    return _bridge
