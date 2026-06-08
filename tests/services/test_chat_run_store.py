"""In-memory chat run store concurrency and stale-run recovery."""

from __future__ import annotations

import asyncio
import time
import uuid

from app.services.chat_run_store import ChatRunStore, _STALE_PROCESSING_SECONDS


def test_begin_run_cancels_previous_same_session() -> None:
    async def _run() -> None:
        store = ChatRunStore()
        user_id = str(uuid.uuid4())
        session_key = str(uuid.uuid4())

        first = await store.begin_run(owner_user_id=user_id, session_key=session_key)
        second = await store.begin_run(owner_user_id=user_id, session_key=session_key)

        assert first.generation == 1
        assert second.generation == 2
        assert first.cancel_event.is_set()

    asyncio.run(_run())


def test_update_run_ignores_streaming_after_terminal() -> None:
    async def _run() -> None:
        store = ChatRunStore()
        user_id = str(uuid.uuid4())
        session_key = str(uuid.uuid4())
        await store.begin_run(owner_user_id=user_id, session_key=session_key)

        await store.update_run(
            owner_user_id=user_id,
            session_key=session_key,
            text="done",
            done=True,
            status="cancelled",
        )
        late = await store.update_run(
            owner_user_id=user_id,
            session_key=session_key,
            text="stale",
            done=False,
            status="streaming",
        )

        assert late is not None
        assert late.done is True
        assert late.status == "cancelled"
        assert late.text == "done"

    asyncio.run(_run())


def test_is_user_busy_reclaims_stale_processing_run() -> None:
    async def _run() -> None:
        store = ChatRunStore()
        user_id = str(uuid.uuid4())
        session_key = str(uuid.uuid4())
        record = await store.begin_run(owner_user_id=user_id, session_key=session_key)
        record.updated_at = time.time() - _STALE_PROCESSING_SECONDS - 1

        assert await store.is_user_busy(user_id) is False
        current = await store.get_run(owner_user_id=user_id, session_key=session_key)
        assert current is not None
        assert current.done is True
        assert current.status == "timeout"

    asyncio.run(_run())
