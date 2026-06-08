"""Shared rate limiting: PostgreSQL when database_url is set, else in-process memory."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from app.core.config import settings

_table_ready = False
_table_lock = threading.Lock()
_memory_hits: dict[str, deque[float]] = defaultdict(deque)
_memory_lock = threading.Lock()


def _ensure_table() -> None:
    global _table_ready
    if _table_ready or not settings.database_url:
        return
    with _table_lock:
        if _table_ready:
            return
        import psycopg

        sql = """
        CREATE TABLE IF NOT EXISTS rate_limit_hits (
          bucket_key TEXT NOT NULL,
          hit_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_rate_limit_hits_bucket_hit
          ON rate_limit_hits (bucket_key, hit_at DESC);
        """
        with psycopg.connect(settings.database_url) as conn, conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()
        _table_ready = True


def _allow_memory(bucket_key: str, *, limit: int, window_seconds: float) -> bool:
    with _memory_lock:
        now = time.monotonic()
        bucket = _memory_hits[bucket_key]
        while bucket and bucket[0] < now - window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True


def _allow_postgres(bucket_key: str, *, limit: int, window_seconds: float) -> bool:
    import psycopg

    _ensure_table()
    window_seconds = max(1.0, float(window_seconds))
    with psycopg.connect(settings.database_url) as conn, conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM rate_limit_hits
            WHERE bucket_key = %s AND hit_at < NOW() - (%s * INTERVAL '1 second')
            """,
            (bucket_key, window_seconds),
        )
        cur.execute(
            "SELECT COUNT(*) FROM rate_limit_hits WHERE bucket_key = %s",
            (bucket_key,),
        )
        count = int(cur.fetchone()[0] or 0)
        if count >= limit:
            conn.commit()
            return False
        cur.execute(
            "INSERT INTO rate_limit_hits (bucket_key) VALUES (%s)",
            (bucket_key,),
        )
        conn.commit()
    return True


def allow(bucket_key: str, *, limit: int, window_seconds: float = 60.0) -> bool:
    cap = max(1, int(limit))
    if settings.database_url:
        return _allow_postgres(bucket_key, limit=cap, window_seconds=window_seconds)
    return _allow_memory(bucket_key, limit=cap, window_seconds=window_seconds)


def count(bucket_key: str, *, window_seconds: float = 60.0) -> int:
    window_seconds = max(1.0, float(window_seconds))
    if settings.database_url:
        _ensure_table()
        import psycopg

        with psycopg.connect(settings.database_url) as conn, conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM rate_limit_hits
                WHERE bucket_key = %s AND hit_at < NOW() - (%s * INTERVAL '1 second')
                """,
                (bucket_key, window_seconds),
            )
            cur.execute(
                "SELECT COUNT(*) FROM rate_limit_hits WHERE bucket_key = %s",
                (bucket_key,),
            )
            row = cur.fetchone()
            conn.commit()
        return int(row[0] or 0) if row else 0

    with _memory_lock:
        now = time.monotonic()
        bucket = _memory_hits[bucket_key]
        while bucket and bucket[0] < now - window_seconds:
            bucket.popleft()
        return len(bucket)


def record(bucket_key: str, *, window_seconds: float = 60.0) -> None:
    allow(bucket_key, limit=10**9, window_seconds=window_seconds)
