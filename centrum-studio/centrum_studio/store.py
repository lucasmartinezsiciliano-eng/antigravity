from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite

from .config import get_config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS scenes (
    scene_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    soul_id TEXT NOT NULL,
    scene_description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    comfy_prompt_id TEXT,
    output_path TEXT,
    duration_seconds REAL,
    arcface_similarity REAL,
    dover_score REAL,
    musiq_score REAL,
    temporal_lpips REAL,
    syncnet_lsec REAL,
    passed_thresholds INTEGER DEFAULT 0,
    params_used TEXT,
    error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_scenes_project ON scenes(project_id);
CREATE INDEX IF NOT EXISTS idx_scenes_status ON scenes(status);

CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    job_type TEXT NOT NULL,
    scene_id TEXT,
    project_id TEXT,
    status TEXT NOT NULL DEFAULT 'queued',
    priority INTEGER DEFAULT 5,
    progress_pct REAL DEFAULT 0,
    eta_seconds INTEGER,
    result TEXT,
    error TEXT,
    error_code TEXT,
    idempotency_key TEXT UNIQUE,
    payload TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_scene ON jobs(scene_id);

CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'briefed',
    scene_ids TEXT,
    final_video_path TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS engrams_cache (
    engram_id TEXT PRIMARY KEY,
    scene_id TEXT,
    outcome TEXT NOT NULL,
    lesson TEXT NOT NULL,
    recommended_params TEXT,
    tags TEXT,
    strength REAL DEFAULT 1.0,
    synced_to_plur INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_engrams_outcome ON engrams_cache(outcome);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class Store:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or get_config().db_path
        self._initialized = False

    async def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(_SCHEMA)
            await db.commit()
        self._initialized = True

    async def _conn(self) -> aiosqlite.Connection:
        if not self._initialized:
            await self.initialize()
        conn = await aiosqlite.connect(self.db_path)
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA foreign_keys=ON")
        await conn.execute("PRAGMA journal_mode=WAL")
        return conn

    async def create_scene(
        self,
        scene_id: str,
        project_id: str,
        soul_id: str,
        scene_description: str,
        params_used: dict[str, Any] | None = None,
        duration_seconds: float | None = None,
    ) -> dict[str, Any]:
        now = _now()
        async with await self._conn() as db:
            await db.execute(
                """INSERT INTO scenes(scene_id, project_id, soul_id, scene_description,
                                       status, params_used, duration_seconds, created_at, updated_at)
                   VALUES (?, ?, ?, ?, 'queued', ?, ?, ?, ?)""",
                (
                    scene_id,
                    project_id,
                    soul_id,
                    scene_description,
                    json.dumps(params_used or {}),
                    duration_seconds,
                    now,
                    now,
                ),
            )
            await db.commit()
        return await self.get_scene(scene_id)

    async def get_scene(self, scene_id: str) -> dict[str, Any] | None:
        async with await self._conn() as db:
            row = await (await db.execute(
                "SELECT * FROM scenes WHERE scene_id = ?", (scene_id,)
            )).fetchone()
        return _row_to_dict(row)

    async def update_scene(self, scene_id: str, **fields: Any) -> None:
        if not fields:
            return
        fields["updated_at"] = _now()
        keys = list(fields.keys())
        values = [json.dumps(v) if isinstance(v, (dict, list)) else v for v in fields.values()]
        set_clause = ", ".join(f"{k} = ?" for k in keys)
        async with await self._conn() as db:
            await db.execute(
                f"UPDATE scenes SET {set_clause} WHERE scene_id = ?",
                (*values, scene_id),
            )
            await db.commit()

    async def list_scenes(
        self,
        project_id: str | None = None,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        clauses: list[str] = []
        params: list[Any] = []
        if project_id:
            clauses.append("project_id = ?")
            params.append(project_id)
        if status:
            clauses.append("status = ?")
            params.append(status)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        async with await self._conn() as db:
            total = (await (await db.execute(
                f"SELECT COUNT(*) AS c FROM scenes {where}", params
            )).fetchone())["c"]
            rows = await (await db.execute(
                f"SELECT * FROM scenes {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (*params, limit, offset),
            )).fetchall()
        return [_row_to_dict(r) for r in rows], total

    async def create_job(
        self,
        job_id: str,
        job_type: str,
        priority: int = 5,
        scene_id: str | None = None,
        project_id: str | None = None,
        idempotency_key: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        now = _now()
        async with await self._conn() as db:
            try:
                await db.execute(
                    """INSERT INTO jobs(job_id, job_type, scene_id, project_id, status, priority,
                                         idempotency_key, payload, created_at, updated_at)
                       VALUES (?, ?, ?, ?, 'queued', ?, ?, ?, ?, ?)""",
                    (
                        job_id,
                        job_type,
                        scene_id,
                        project_id,
                        priority,
                        idempotency_key,
                        json.dumps(payload or {}),
                        now,
                        now,
                    ),
                )
                await db.commit()
            except aiosqlite.IntegrityError:
                if idempotency_key:
                    existing = await (await db.execute(
                        "SELECT * FROM jobs WHERE idempotency_key = ?", (idempotency_key,)
                    )).fetchone()
                    if existing:
                        return _row_to_dict(existing)
                raise
        return await self.get_job(job_id)

    async def get_job(self, job_id: str) -> dict[str, Any] | None:
        async with await self._conn() as db:
            row = await (await db.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            )).fetchone()
        return _row_to_dict(row)

    async def get_job_by_idempotency(self, key: str) -> dict[str, Any] | None:
        async with await self._conn() as db:
            row = await (await db.execute(
                "SELECT * FROM jobs WHERE idempotency_key = ?", (key,)
            )).fetchone()
        return _row_to_dict(row)

    async def update_job(self, job_id: str, **fields: Any) -> None:
        if not fields:
            return
        fields["updated_at"] = _now()
        keys = list(fields.keys())
        values = [json.dumps(v) if isinstance(v, (dict, list)) else v for v in fields.values()]
        set_clause = ", ".join(f"{k} = ?" for k in keys)
        async with await self._conn() as db:
            await db.execute(
                f"UPDATE jobs SET {set_clause} WHERE job_id = ?",
                (*values, job_id),
            )
            await db.commit()

    async def create_project(self, project_id: str, name: str) -> dict[str, Any]:
        now = _now()
        async with await self._conn() as db:
            await db.execute(
                """INSERT INTO projects(project_id, name, scene_ids, created_at, updated_at)
                   VALUES (?, ?, '[]', ?, ?)""",
                (project_id, name, now, now),
            )
            await db.commit()
        return await self.get_project(project_id)

    async def get_project(self, project_id: str) -> dict[str, Any] | None:
        async with await self._conn() as db:
            row = await (await db.execute(
                "SELECT * FROM projects WHERE project_id = ?", (project_id,)
            )).fetchone()
        return _row_to_dict(row)

    async def update_project(self, project_id: str, **fields: Any) -> None:
        if not fields:
            return
        fields["updated_at"] = _now()
        keys = list(fields.keys())
        values = [json.dumps(v) if isinstance(v, (dict, list)) else v for v in fields.values()]
        set_clause = ", ".join(f"{k} = ?" for k in keys)
        async with await self._conn() as db:
            await db.execute(
                f"UPDATE projects SET {set_clause} WHERE project_id = ?",
                (*values, project_id),
            )
            await db.commit()

    async def list_projects(self, limit: int = 50) -> list[dict[str, Any]]:
        async with await self._conn() as db:
            rows = await (await db.execute(
                "SELECT * FROM projects ORDER BY created_at DESC LIMIT ?", (limit,)
            )).fetchall()
        return [_row_to_dict(r) for r in rows]

    async def save_engram(
        self,
        engram_id: str,
        outcome: str,
        lesson: str,
        scene_id: str | None = None,
        recommended_params: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        strength: float = 1.0,
        synced_to_plur: bool = False,
    ) -> dict[str, Any]:
        async with await self._conn() as db:
            await db.execute(
                """INSERT INTO engrams_cache(engram_id, scene_id, outcome, lesson,
                                              recommended_params, tags, strength,
                                              synced_to_plur, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    engram_id,
                    scene_id,
                    outcome,
                    lesson,
                    json.dumps(recommended_params or {}),
                    json.dumps(tags or []),
                    strength,
                    1 if synced_to_plur else 0,
                    _now(),
                ),
            )
            await db.commit()
        return {"engram_id": engram_id, "saved": True}

    async def search_engrams_local(
        self,
        query: str,
        tags_hint: list[str] | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        terms = [t.lower() for t in query.split() if len(t) > 2]
        async with await self._conn() as db:
            rows = await (await db.execute(
                "SELECT * FROM engrams_cache ORDER BY strength DESC, created_at DESC LIMIT 200"
            )).fetchall()
        scored: list[tuple[float, dict[str, Any]]] = []
        tag_hint_set = {t.lower() for t in (tags_hint or [])}
        for r in rows:
            d = _row_to_dict(r)
            text = (d.get("lesson") or "").lower()
            score = sum(1.0 for t in terms if t in text)
            tags = json.loads(d.get("tags") or "[]")
            tag_overlap = len(tag_hint_set & {t.lower() for t in tags})
            score += tag_overlap * 1.5
            score += d.get("strength", 1.0) * 0.5
            if score > 0:
                d["relevance_score"] = round(score, 3)
                try:
                    d["recommended_params"] = json.loads(d.get("recommended_params") or "{}")
                except Exception:
                    pass
                try:
                    d["tags"] = tags
                except Exception:
                    pass
                scored.append((score, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [d for _, d in scored[:limit]]


def _row_to_dict(row: Any) -> dict[str, Any] | None:
    if row is None:
        return None
    d = dict(row)
    for json_field in ("params_used", "result", "payload", "scene_ids", "recommended_params", "tags"):
        if json_field in d and isinstance(d[json_field], str):
            try:
                d[json_field] = json.loads(d[json_field])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


_store: Store | None = None


def get_store() -> Store:
    global _store
    if _store is None:
        _store = Store()
    return _store
