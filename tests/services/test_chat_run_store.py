"""PostgreSQL-backed chat run store tests."""

from __future__ import annotations

import asyncio
import uuid

import pytest

from app.core.config import settings
from app.db import chat_queries as cq
from app.db.user_queries import _connect
from app.services.chat_run_store import ChatRunStore

_STALE_PROCESSING_SECONDS = cq._STALE_PROCESSING_SECONDS


@pytest.fixture
def require_db() -> None:
    if not settings.database_url:
        pytest.skip("OPENCLAW_DATABASE_URL not configured")


def test_begin_run_persists_user_message(require_db: None) -> None:
    async def _run() -> None:
        store = ChatRunStore()
        user_id = str(uuid.uuid4())
        session_key = str(uuid.uuid4())
        record = await store.begin_run(
            owner_user_id=user_id,
            session_key=session_key,
            user_text="分析黄金市场",
        )
        assert record.generation == 1
        messages = cq.list_messages_for_run(record.run_id or "")
        assert any(m["role"] == "user" and "黄金" in m["content"] for m in messages)

    asyncio.run(_run())


def test_begin_run_cancels_previous_same_session(require_db: None) -> None:
    async def _run() -> None:
        store = ChatRunStore()
        user_id = str(uuid.uuid4())
        session_key = str(uuid.uuid4())

        first = await store.begin_run(owner_user_id=user_id, session_key=session_key, user_text="a")
        second = await store.begin_run(owner_user_id=user_id, session_key=session_key, user_text="b")

        assert first.generation == 1
        assert second.generation == 2
        assert first.cancel_event.is_set()

    asyncio.run(_run())


def test_update_run_ignores_streaming_after_terminal(require_db: None) -> None:
    async def _run() -> None:
        store = ChatRunStore()
        user_id = str(uuid.uuid4())
        session_key = str(uuid.uuid4())
        await store.begin_run(owner_user_id=user_id, session_key=session_key, user_text="hi")

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


def test_get_run_recovers_from_db(require_db: None) -> None:
    async def _run() -> None:
        store = ChatRunStore()
        user_id = str(uuid.uuid4())
        session_key = str(uuid.uuid4())
        await store.begin_run(owner_user_id=user_id, session_key=session_key, user_text="hello")
        await store.update_run(
            owner_user_id=user_id,
            session_key=session_key,
            text="partial reply",
            done=False,
            status="streaming",
        )

        other_store = ChatRunStore()
        recovered = await other_store.get_run(owner_user_id=user_id, session_key=session_key)
        assert recovered is not None
        assert recovered.text == "partial reply"
        assert recovered.status == "streaming"

    asyncio.run(_run())


def test_is_user_busy_reclaims_stale_processing_run(require_db: None) -> None:
    async def _run() -> None:
        store = ChatRunStore()
        user_id = str(uuid.uuid4())
        session_key = str(uuid.uuid4())
        record = await store.begin_run(owner_user_id=user_id, session_key=session_key, user_text="x")

        with _connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE chat_runs
                SET updated_at = NOW() - (%s * INTERVAL '1 second')
                WHERE user_id = %s::uuid AND session_key = %s
                """,
                (_STALE_PROCESSING_SECONDS + 1, user_id, session_key),
            )
            conn.commit()

        assert await store.is_user_busy(user_id) is False
        current = await store.get_run(owner_user_id=user_id, session_key=session_key)
        assert current is not None
        assert current.done is True
        assert current.status == "timeout"

    asyncio.run(_run())
