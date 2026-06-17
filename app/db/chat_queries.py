"""PostgreSQL persistence for portal chat runs and messages."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.db.user_queries import _connect, ensure_user_tables

TERMINAL_STATUSES = frozenset({"done", "error", "cancelled", "timeout"})
STREAMING_STATUSES = frozenset({"processing", "streaming"})
_STALE_PROCESSING_SECONDS = 660.0


def _require_db() -> None:
    if not settings.database_url:
        raise RuntimeError("OPENCLAW_DATABASE_URL is required for chat persistence")


def ensure_chat_tables() -> None:
    if not settings.database_url:
        return
    ensure_user_tables()
    sql = """
    CREATE TABLE IF NOT EXISTS chat_runs (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      session_key TEXT NOT NULL,
      status TEXT NOT NULL,
      generation INT NOT NULL DEFAULT 1,
      error TEXT,
      assistant_text TEXT NOT NULL DEFAULT '',
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE (user_id, session_key)
    );
    CREATE INDEX IF NOT EXISTS idx_chat_runs_user_updated
      ON chat_runs (user_id, updated_at DESC);
    CREATE INDEX IF NOT EXISTS idx_chat_runs_user_status
      ON chat_runs (user_id, status);

    CREATE TABLE IF NOT EXISTS chat_messages (
      id BIGSERIAL PRIMARY KEY,
      run_id UUID NOT NULL REFERENCES chat_runs(id) ON DELETE CASCADE,
      role TEXT NOT NULL,
      content TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_chat_messages_run_created
      ON chat_messages (run_id, created_at);
    """
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(sql)
        conn.commit()


def _row_to_run(row: tuple) -> dict[str, Any]:
    updated_at = row[7]
    if isinstance(updated_at, datetime):
        updated_ts = updated_at.timestamp()
    else:
        updated_ts = datetime.now(timezone.utc).timestamp()
    status = str(row[3])
    return {
        "run_id": str(row[0]),
        "user_id": str(row[1]),
        "session_key": str(row[2]),
        "status": status,
        "generation": int(row[4]),
        "error": row[5],
        "text": str(row[6] or ""),
        "done": status in TERMINAL_STATUSES,
        "updated_at": updated_ts,
    }


def _insert_message(cur, run_id: str, role: str, content: str) -> None:
    text = (content or "").strip()
    if not text:
        return
    cur.execute(
        """
        INSERT INTO chat_messages (run_id, role, content)
        VALUES (%s::uuid, %s, %s)
        """,
        (run_id, role[:32], text[:16000]),
    )


def begin_run(
    *,
    user_id: str,
    session_key: str,
    user_text: str | None = None,
) -> dict[str, Any]:
    _require_db()
    ensure_chat_tables()
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO chat_runs (user_id, session_key, status, generation, assistant_text, error)
            VALUES (%s::uuid, %s, 'processing', 1, '', NULL)
            ON CONFLICT (user_id, session_key) DO UPDATE SET
              generation = chat_runs.generation + 1,
              status = 'processing',
              assistant_text = '',
              error = NULL,
              updated_at = NOW()
            RETURNING id, user_id, session_key, status, generation, error, assistant_text, updated_at
            """,
            (user_id, session_key),
        )
        row = cur.fetchone()
        if not row:
            raise RuntimeError("failed to begin chat run")
        run_id = str(row[0])
        if user_text:
            _insert_message(cur, run_id, "user", user_text)
        conn.commit()
    return _row_to_run(row)


def update_run(
    *,
    user_id: str,
    session_key: str,
    text: str,
    done: bool,
    status: str,
    error: str | None = None,
) -> dict[str, Any] | None:
    _require_db()
    ensure_chat_tables()
    normalized_status = status.strip()
    if done and normalized_status in STREAMING_STATUSES:
        normalized_status = "done"

    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, user_id, session_key, status, generation, error, assistant_text, updated_at
            FROM chat_runs
            WHERE user_id = %s::uuid AND session_key = %s
            FOR UPDATE
            """,
            (user_id, session_key),
        )
        row = cur.fetchone()
        if not row:
            return None
        current_status = str(row[3])
        if current_status in TERMINAL_STATUSES and normalized_status in STREAMING_STATUSES:
            return _row_to_run(row)

        cur.execute(
            """
            UPDATE chat_runs
            SET assistant_text = %s,
                status = %s,
                error = %s,
                updated_at = NOW()
            WHERE user_id = %s::uuid AND session_key = %s
            RETURNING id, user_id, session_key, status, generation, error, assistant_text, updated_at
            """,
            (text, normalized_status, error, user_id, session_key),
        )
        updated = cur.fetchone()
        if updated and done and normalized_status in TERMINAL_STATUSES:
            _insert_message(cur, str(updated[0]), "assistant", text)
        conn.commit()
    return _row_to_run(updated) if updated else None


def get_run(*, user_id: str, session_key: str) -> dict[str, Any] | None:
    _require_db()
    ensure_chat_tables()
    reclaim_stale_run(user_id=user_id, session_key=session_key)
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, user_id, session_key, status, generation, error, assistant_text, updated_at
            FROM chat_runs
            WHERE user_id = %s::uuid AND session_key = %s
            """,
            (user_id, session_key),
        )
        row = cur.fetchone()
    return _row_to_run(row) if row else None


def list_active_for_user(user_id: str) -> list[dict[str, Any]]:
    _require_db()
    ensure_chat_tables()
    reclaim_stale_runs_for_user(user_id)
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, user_id, session_key, status, generation, error, assistant_text, updated_at
            FROM chat_runs
            WHERE user_id = %s::uuid AND status IN ('processing', 'streaming')
            ORDER BY updated_at DESC
            """,
            (user_id,),
        )
        rows = cur.fetchall()
    return [_row_to_run(row) for row in rows]


def has_active_run(user_id: str, *, except_session_key: str | None = None) -> bool:
    _require_db()
    ensure_chat_tables()
    reclaim_stale_runs_for_user(user_id)
    with _connect() as conn, conn.cursor() as cur:
        if except_session_key:
            cur.execute(
                """
                SELECT 1 FROM chat_runs
                WHERE user_id = %s::uuid
                  AND status IN ('processing', 'streaming')
                  AND session_key <> %s
                LIMIT 1
                """,
                (user_id, except_session_key),
            )
        else:
            cur.execute(
                """
                SELECT 1 FROM chat_runs
                WHERE user_id = %s::uuid AND status IN ('processing', 'streaming')
                LIMIT 1
                """,
                (user_id,),
            )
        return cur.fetchone() is not None


def reclaim_stale_run(*, user_id: str, session_key: str) -> bool:
    _require_db()
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE chat_runs
            SET status = 'timeout',
                error = 'stale run reclaimed',
                updated_at = NOW()
            WHERE user_id = %s::uuid
              AND session_key = %s
              AND status IN ('processing', 'streaming')
              AND updated_at < NOW() - (%s * INTERVAL '1 second')
            """,
            (user_id, session_key, _STALE_PROCESSING_SECONDS),
        )
        changed = cur.rowcount > 0
        conn.commit()
    return changed


def reclaim_stale_runs_for_user(user_id: str) -> int:
    _require_db()
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE chat_runs
            SET status = 'timeout',
                error = 'stale run reclaimed',
                updated_at = NOW()
            WHERE user_id = %s::uuid
              AND status IN ('processing', 'streaming')
              AND updated_at < NOW() - (%s * INTERVAL '1 second')
            """,
            (user_id, _STALE_PROCESSING_SECONDS),
        )
        count = cur.rowcount
        conn.commit()
    return int(count)


def list_messages_for_run(run_id: str, *, limit: int = 200) -> list[dict[str, Any]]:
    _require_db()
    ensure_chat_tables()
    capped = max(1, min(int(limit), 500))
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, role, content, created_at
            FROM chat_messages
            WHERE run_id = %s::uuid
            ORDER BY created_at ASC
            LIMIT %s
            """,
            (run_id, capped),
        )
        rows = cur.fetchall()
    items: list[dict[str, Any]] = []
    for row in rows:
        created = row[3]
        created_iso = created.isoformat() if isinstance(created, datetime) else None
        items.append(
            {
                "id": int(row[0]),
                "role": str(row[1]),
                "content": str(row[2]),
                "timestamp": created_iso,
            }
        )
    return items
