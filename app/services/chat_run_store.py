from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Literal

ChatRunStatus = Literal[
    "processing",
    "streaming",
    "done",
    "error",
    "cancelled",
    "timeout",
]

_RUN_TTL_SECONDS = 3600.0
# Reclaim orphaned in-memory runs (e.g. after cancel races or lost WS tasks).
_STALE_PROCESSING_SECONDS = 660.0
_STREAMING_STATUSES = frozenset({"processing", "streaming"})


@dataclass
class ChatRunRecord:
    session_key: str
    owner_user_id: str
    status: ChatRunStatus
    text: str = ""
    error: str | None = None
    done: bool = False
    updated_at: float = field(default_factory=time.time)
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    generation: int = 1


class ChatRunStore:
    """In-memory chat turn state for portal background runs and poll recovery."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._runs: dict[tuple[str, str], ChatRunRecord] = {}
        self._active_by_user: dict[str, str] = {}

    async def _prune_locked(self) -> None:
        cutoff = time.time() - _RUN_TTL_SECONDS
        stale: list[tuple[str, str]] = []
        for key, record in self._runs.items():
            if record.done and record.updated_at < cutoff:
                stale.append(key)
        for key in stale:
            record = self._runs.pop(key, None)
            if record and self._active_by_user.get(record.owner_user_id) == record.session_key:
                self._active_by_user.pop(record.owner_user_id, None)

    async def _reclaim_stale_locked(self, record: ChatRunRecord) -> None:
        if record.done or record.status not in _STREAMING_STATUSES:
            return
        if (time.time() - record.updated_at) < _STALE_PROCESSING_SECONDS:
            return
        record.cancel_event.set()
        record.text = (record.text or "").rstrip()
        record.done = True
        record.status = "timeout"
        record.error = "stale run reclaimed"
        record.updated_at = time.time()
        if self._active_by_user.get(record.owner_user_id) == record.session_key:
            self._active_by_user.pop(record.owner_user_id, None)

    async def begin_run(self, *, owner_user_id: str, session_key: str) -> ChatRunRecord:
        async with self._lock:
            await self._prune_locked()
            existing = self._runs.get((owner_user_id, session_key))
            if existing is not None and not existing.done:
                existing.cancel_event.set()
            if self._active_by_user.get(owner_user_id) not in (None, session_key):
                other_key = self._active_by_user[owner_user_id]
                other = self._runs.get((owner_user_id, other_key))
                if other is not None:
                    await self._reclaim_stale_locked(other)
                if other is not None and not other.done:
                    raise RuntimeError("Another chat turn is already running for this user.")
            next_generation = (existing.generation + 1) if existing is not None else 1
            record = ChatRunRecord(
                session_key=session_key,
                owner_user_id=owner_user_id,
                status="processing",
                generation=next_generation,
            )
            self._runs[(owner_user_id, session_key)] = record
            self._active_by_user[owner_user_id] = session_key
            return record

    async def update_run(
        self,
        *,
        owner_user_id: str,
        session_key: str,
        text: str,
        done: bool,
        status: ChatRunStatus,
        error: str | None = None,
    ) -> ChatRunRecord | None:
        async with self._lock:
            record = self._runs.get((owner_user_id, session_key))
            if record is None:
                return None
            if record.done and status in _STREAMING_STATUSES:
                return record
            record.text = text
            record.done = done
            record.status = status
            record.error = error
            record.updated_at = time.time()
            if done:
                self._active_by_user.pop(owner_user_id, None)
            return record

    async def get_run(self, *, owner_user_id: str, session_key: str) -> ChatRunRecord | None:
        async with self._lock:
            await self._prune_locked()
            return self._runs.get((owner_user_id, session_key))

    async def list_active_for_user(self, owner_user_id: str) -> list[ChatRunRecord]:
        async with self._lock:
            await self._prune_locked()
            active_key = self._active_by_user.get(owner_user_id)
            if not active_key:
                return []
            record = self._runs.get((owner_user_id, active_key))
            return [record] if record and not record.done else []

    async def request_cancel(self, *, owner_user_id: str, session_key: str) -> bool:
        async with self._lock:
            record = self._runs.get((owner_user_id, session_key))
            if record is None or record.done:
                return False
            record.cancel_event.set()
            return True

    async def is_user_busy(self, owner_user_id: str, *, except_session_key: str | None = None) -> bool:
        async with self._lock:
            active_key = self._active_by_user.get(owner_user_id)
            if not active_key:
                return False
            record = self._runs.get((owner_user_id, active_key))
            if record is None:
                return False
            await self._reclaim_stale_locked(record)
            if record.done:
                return False
            if except_session_key and active_key == except_session_key:
                return False
            return True


chat_run_store = ChatRunStore()
