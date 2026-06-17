from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Literal

from app.db import chat_queries as cq

ChatRunStatus = Literal[
    "processing",
    "streaming",
    "done",
    "error",
    "cancelled",
    "timeout",
]

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
    run_id: str | None = None


def _record_from_row(row: dict, cancel_event: asyncio.Event) -> ChatRunRecord:
    return ChatRunRecord(
        session_key=str(row["session_key"]),
        owner_user_id=str(row["user_id"]),
        status=row["status"],
        text=str(row.get("text") or ""),
        error=row.get("error"),
        done=bool(row.get("done")),
        updated_at=float(row.get("updated_at") or time.time()),
        cancel_event=cancel_event,
        generation=int(row.get("generation") or 1),
        run_id=str(row.get("run_id") or "") or None,
    )


class ChatRunStore:
    """PostgreSQL-backed chat turn state; cancel signals remain in-process only."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._cancel_events: dict[tuple[str, str], asyncio.Event] = {}

    def _event_key(self, owner_user_id: str, session_key: str) -> tuple[str, str]:
        return owner_user_id, session_key

    def _cancel_previous_locked(self, owner_user_id: str, session_key: str) -> asyncio.Event:
        key = self._event_key(owner_user_id, session_key)
        existing = self._cancel_events.get(key)
        if existing is not None:
            existing.set()
        event = asyncio.Event()
        self._cancel_events[key] = event
        return event

    def _release_cancel_locked(self, owner_user_id: str, session_key: str) -> None:
        key = self._event_key(owner_user_id, session_key)
        self._cancel_events.pop(key, None)

    async def begin_run(
        self,
        *,
        owner_user_id: str,
        session_key: str,
        user_text: str | None = None,
    ) -> ChatRunRecord:
        async with self._lock:
            if await asyncio.to_thread(cq.has_active_run, owner_user_id, except_session_key=session_key):
                raise RuntimeError("Another chat turn is already running for this user.")
            cancel_event = self._cancel_previous_locked(owner_user_id, session_key)
            row = await asyncio.to_thread(
                cq.begin_run,
                user_id=owner_user_id,
                session_key=session_key,
                user_text=user_text,
            )
            return _record_from_row(row, cancel_event)

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
        row = await asyncio.to_thread(
            cq.update_run,
            user_id=owner_user_id,
            session_key=session_key,
            text=text,
            done=done,
            status=status,
            error=error,
        )
        if row is None:
            return None
        async with self._lock:
            key = self._event_key(owner_user_id, session_key)
            cancel_event = self._cancel_events.get(key) or asyncio.Event()
            if done:
                self._release_cancel_locked(owner_user_id, session_key)
            return _record_from_row(row, cancel_event)

    async def get_run(self, *, owner_user_id: str, session_key: str) -> ChatRunRecord | None:
        row = await asyncio.to_thread(
            cq.get_run,
            user_id=owner_user_id,
            session_key=session_key,
        )
        if row is None:
            return None
        async with self._lock:
            key = self._event_key(owner_user_id, session_key)
            if not row["done"] and row["status"] in _STREAMING_STATUSES:
                cancel_event = self._cancel_events.get(key)
                if cancel_event is None:
                    cancel_event = asyncio.Event()
                    self._cancel_events[key] = cancel_event
            else:
                cancel_event = self._cancel_events.get(key) or asyncio.Event()
            return _record_from_row(row, cancel_event)

    async def list_active_for_user(self, owner_user_id: str) -> list[ChatRunRecord]:
        rows = await asyncio.to_thread(cq.list_active_for_user, owner_user_id)
        async with self._lock:
            records: list[ChatRunRecord] = []
            for row in rows:
                key = self._event_key(owner_user_id, str(row["session_key"]))
                cancel_event = self._cancel_events.get(key) or asyncio.Event()
                records.append(_record_from_row(row, cancel_event))
            return records

    async def request_cancel(self, *, owner_user_id: str, session_key: str) -> bool:
        row = await asyncio.to_thread(
            cq.get_run,
            user_id=owner_user_id,
            session_key=session_key,
        )
        if row is None or row["done"]:
            return False
        async with self._lock:
            key = self._event_key(owner_user_id, session_key)
            cancel_event = self._cancel_events.get(key)
            if cancel_event is None:
                cancel_event = asyncio.Event()
                self._cancel_events[key] = cancel_event
            cancel_event.set()
            return True

    async def is_user_busy(self, owner_user_id: str, *, except_session_key: str | None = None) -> bool:
        return await asyncio.to_thread(
            cq.has_active_run,
            owner_user_id,
            except_session_key=except_session_key,
        )


chat_run_store = ChatRunStore()
