from __future__ import annotations

import asyncio
import itertools
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Awaitable, Callable

import structlog

from ..config import get_config
from ..store import get_store

log = structlog.get_logger("centrum_studio.gpu")


class GPUMode(str, Enum):
    AGENTS = "agents"
    SATURDAY_IMAGES = "saturday_images"
    SATURDAY_VIDEO = "saturday_video"

    @classmethod
    def parse(cls, raw: str) -> GPUMode:
        v = (raw or "").strip().lower()
        try:
            return cls(v)
        except ValueError:
            return cls.AGENTS

    @property
    def is_active(self) -> bool:
        return self in (GPUMode.SATURDAY_IMAGES, GPUMode.SATURDAY_VIDEO)


@dataclass(order=True)
class _QueueItem:
    priority: int
    seq: int
    job_id: str = field(compare=False)
    job_type: str = field(compare=False)
    run: Callable[[], Awaitable[Any]] = field(compare=False)
    enqueued_at: float = field(default_factory=time.monotonic, compare=False)


class GPUQueue:
    def __init__(self, gpu_mode_file: Path | None = None, poll_seconds: int | None = None) -> None:
        cfg = get_config()
        self.gpu_mode_file = gpu_mode_file or cfg.gpu_mode_file
        self.poll_seconds = poll_seconds or cfg.gpu_mode_poll_seconds
        self._queue: asyncio.PriorityQueue[_QueueItem] = asyncio.PriorityQueue()
        self._mode: GPUMode = GPUMode.AGENTS
        self._mode_lock = asyncio.Lock()
        self._worker_task: asyncio.Task[None] | None = None
        self._mode_poller_task: asyncio.Task[None] | None = None
        self._stopped = asyncio.Event()
        self._counter = itertools.count()
        self._running: dict[str, asyncio.Task[Any]] = {}

    @property
    def mode(self) -> GPUMode:
        return self._mode

    async def start(self) -> None:
        await self._read_mode()
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._worker_loop(), name="gpu-worker")
        if self._mode_poller_task is None:
            self._mode_poller_task = asyncio.create_task(self._mode_poller(), name="gpu-mode-poller")
        log.info("gpu_queue.started", mode=self._mode.value, poll_seconds=self.poll_seconds)

    async def stop(self) -> None:
        self._stopped.set()
        for task in (self._worker_task, self._mode_poller_task):
            if task is not None:
                task.cancel()
        for task in self._running.values():
            task.cancel()
        self._running.clear()

    async def enqueue(
        self,
        job_id: str,
        job_type: str,
        runner: Callable[[], Awaitable[Any]],
        priority: int = 5,
    ) -> dict[str, Any]:
        item = _QueueItem(
            priority=max(1, min(10, priority)),
            seq=next(self._counter),
            job_id=job_id,
            job_type=job_type,
            run=runner,
        )
        await self._queue.put(item)
        store = get_store()
        eta = await self._estimate_eta(job_type)
        await store.update_job(
            job_id,
            status="queued",
            priority=item.priority,
            eta_seconds=eta,
        )
        message = (
            "GPU in agents mode (Mon-Fri). Job will execute Saturday."
            if not self._mode.is_active
            else "Job queued for GPU execution."
        )
        return {
            "job_id": job_id,
            "status": "queued",
            "priority": item.priority,
            "eta_seconds": eta,
            "gpu_mode": self._mode.value,
            "message": message,
        }

    async def cancel(self, job_id: str) -> bool:
        store = get_store()
        running = self._running.pop(job_id, None)
        if running is not None:
            running.cancel()
            await store.update_job(job_id, status="cancelled")
            return True
        new_queue: asyncio.PriorityQueue[_QueueItem] = asyncio.PriorityQueue()
        found = False
        while not self._queue.empty():
            item = self._queue.get_nowait()
            if item.job_id == job_id:
                found = True
                continue
            await new_queue.put(item)
        self._queue = new_queue
        if found:
            await store.update_job(job_id, status="cancelled")
        return found

    async def _read_mode(self) -> None:
        try:
            raw = self.gpu_mode_file.read_text(encoding="utf-8").strip()
        except OSError:
            raw = "agents"
        async with self._mode_lock:
            new_mode = GPUMode.parse(raw)
            if new_mode != self._mode:
                log.info("gpu_mode.changed", from_mode=self._mode.value, to=new_mode.value)
            self._mode = new_mode

    async def _mode_poller(self) -> None:
        try:
            while not self._stopped.is_set():
                await self._read_mode()
                try:
                    await asyncio.wait_for(self._stopped.wait(), timeout=self.poll_seconds)
                except asyncio.TimeoutError:
                    continue
        except asyncio.CancelledError:
            return

    async def _worker_loop(self) -> None:
        store = get_store()
        try:
            while not self._stopped.is_set():
                if not self._mode.is_active:
                    try:
                        await asyncio.wait_for(self._stopped.wait(), timeout=5.0)
                        if self._stopped.is_set():
                            return
                    except asyncio.TimeoutError:
                        continue
                try:
                    item = await asyncio.wait_for(self._queue.get(), timeout=2.0)
                except asyncio.TimeoutError:
                    continue
                if not self._mode.is_active:
                    await self._queue.put(item)
                    await asyncio.sleep(2.0)
                    continue
                await store.update_job(item.job_id, status="running", progress_pct=0.0)
                task = asyncio.create_task(self._execute(item), name=f"gpu-job-{item.job_id}")
                self._running[item.job_id] = task
        except asyncio.CancelledError:
            return

    async def _execute(self, item: _QueueItem) -> None:
        store = get_store()
        try:
            result = await item.run()
            await store.update_job(
                item.job_id,
                status="done",
                progress_pct=100.0,
                result=result if isinstance(result, dict) else {"value": result},
            )
        except asyncio.CancelledError:
            await store.update_job(item.job_id, status="cancelled")
        except Exception as e:
            log.exception("gpu_job.failed", job_id=item.job_id, job_type=item.job_type)
            await store.update_job(
                item.job_id,
                status="failed",
                error=str(e),
                error_code=getattr(e, "error_code", "GPU_JOB_FAILED"),
            )
        finally:
            self._running.pop(item.job_id, None)

    async def _estimate_eta(self, job_type: str) -> int:
        base = {
            "produce": 60,
            "lipsync": 45,
            "assemble": 20,
            "evaluate": 10,
            "viral_edit": 8,
        }.get(job_type, 30)
        depth = self._queue.qsize()
        return int(base * max(1, depth))


_queue: GPUQueue | None = None


def get_gpu_queue() -> GPUQueue:
    global _queue
    if _queue is None:
        _queue = GPUQueue()
    return _queue
