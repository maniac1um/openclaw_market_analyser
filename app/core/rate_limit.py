"""Shared rate limiting: PostgreSQL when database_url is set, else in-process memory."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from app.core.config import settings

_table_ready = False
_table_lock = threading.Lock()
# bucket_key -> deque of (monotonic_ts, weight)
_memory_hits: dict[str, deque[tuple[float, int]]] = defaultdict(deque)
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
        ALTER TABLE rate_limit_hits
          ADD COLUMN IF NOT EXISTS weight BIGINT NOT NULL DEFAULT 1;
        """
        with psycopg.connect(settings.database_url) as conn, conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()
        _table_ready = True


def _purge_memory(bucket: deque[tuple[float, int]], *, now: float, window_seconds: float) -> None:
    while bucket and bucket[0][0] < now - window_seconds:
        bucket.popleft()


def _sum_memory(bucket_key: str, *, window_seconds: float) -> int:
    with _memory_lock:
        now = time.monotonic()
        bucket = _memory_hits[bucket_key]
        _purge_memory(bucket, now=now, window_seconds=window_seconds)
        return sum(weight for _, weight in bucket)


def _record_memory(bucket_key: str, *, weight: int, window_seconds: float) -> None:
    with _memory_lock:
        now = time.monotonic()
        bucket = _memory_hits[bucket_key]
        _purge_memory(bucket, now=now, window_seconds=window_seconds)
        bucket.append((now, max(1, int(weight))))


def _purge_postgres(cur, bucket_key: str, *, window_seconds: float) -> None:
    cur.execute(
        """
        DELETE FROM rate_limit_hits
        WHERE bucket_key = %s AND hit_at < NOW() - (%s * INTERVAL '1 second')
        """,
        (bucket_key, window_seconds),
    )


def _sum_postgres(cur, bucket_key: str) -> int:
    cur.execute(
        """
        SELECT COALESCE(SUM(weight), 0)
        FROM rate_limit_hits
        WHERE bucket_key = %s
        """,
        (bucket_key,),
    )
    row = cur.fetchone()
    return int(row[0] or 0) if row else 0


def _allow_memory(bucket_key: str, *, limit: int, window_seconds: float) -> bool:
    with _memory_lock:
        now = time.monotonic()
        bucket = _memory_hits[bucket_key]
        _purge_memory(bucket, now=now, window_seconds=window_seconds)
        total = sum(weight for _, weight in bucket)
        if total >= limit:
            return False
        bucket.append((now, 1))
        return True


def _allow_postgres(bucket_key: str, *, limit: int, window_seconds: float) -> bool:
    import psycopg

    _ensure_table()
    window_seconds = max(1.0, float(window_seconds))
    with psycopg.connect(settings.database_url) as conn, conn.cursor() as cur:
        _purge_postgres(cur, bucket_key, window_seconds=window_seconds)
        total = _sum_postgres(cur, bucket_key)
        if total >= limit:
            conn.commit()
            return False
        cur.execute(
            "INSERT INTO rate_limit_hits (bucket_key, weight) VALUES (%s, 1)",
            (bucket_key,),
        )
        conn.commit()
    return True


def allow(bucket_key: str, *, limit: int, window_seconds: float = 60.0) -> bool:
    cap = max(1, int(limit))
    if settings.database_url:
        return _allow_postgres(bucket_key, limit=cap, window_seconds=window_seconds)
    return _allow_memory(bucket_key, limit=cap, window_seconds=window_seconds)


def sum_weight(bucket_key: str, *, window_seconds: float = 60.0) -> int:
    window_seconds = max(1.0, float(window_seconds))
    if settings.database_url:
        _ensure_table()
        import psycopg

        with psycopg.connect(settings.database_url) as conn, conn.cursor() as cur:
            _purge_postgres(cur, bucket_key, window_seconds=window_seconds)
            total = _sum_postgres(cur, bucket_key)
            conn.commit()
        return total
    return _sum_memory(bucket_key, window_seconds=window_seconds)


def record_weight(bucket_key: str, *, weight: int = 1, window_seconds: float = 60.0) -> None:
    amount = max(1, int(weight))
    window_seconds = max(1.0, float(window_seconds))
    if settings.database_url:
        _ensure_table()
        import psycopg

        with psycopg.connect(settings.database_url) as conn, conn.cursor() as cur:
            _purge_postgres(cur, bucket_key, window_seconds=window_seconds)
            cur.execute(
                "INSERT INTO rate_limit_hits (bucket_key, weight) VALUES (%s, %s)",
                (bucket_key, amount),
            )
            conn.commit()
        return
    _record_memory(bucket_key, weight=amount, window_seconds=window_seconds)


def count(bucket_key: str, *, window_seconds: float = 60.0) -> int:
    return sum_weight(bucket_key, window_seconds=window_seconds)


def record(bucket_key: str, *, window_seconds: float = 60.0) -> None:
    record_weight(bucket_key, weight=1, window_seconds=window_seconds)


def _token_bucket_keys(user_id: str) -> tuple[str, str]:
    return f"token-req:{user_id}", f"token-spend:{user_id}"


def check_token_rate_limits(
    user_id: str,
    amount: int,
    *,
    window_seconds: float = 60.0,
) -> bool:
    """Return True when the user may consume `amount` tokens under current limits."""
    if not settings.token_rate_limit_enabled:
        return True
    req_key, spend_key = _token_bucket_keys(user_id)
    req_limit = max(1, int(settings.token_requests_per_minute))
    spend_limit = max(1, int(settings.token_spend_per_minute))
    tokens = max(1, int(amount))
    window_seconds = max(1.0, float(window_seconds))

    req_used = sum_weight(req_key, window_seconds=window_seconds)
    spend_used = sum_weight(spend_key, window_seconds=window_seconds)
    return req_used < req_limit and spend_used + tokens <= spend_limit


def acquire_token_rate_limits(
    user_id: str,
    amount: int,
    *,
    window_seconds: float = 60.0,
) -> bool:
    """Atomically check and record one billing request + token spend."""
    if not settings.token_rate_limit_enabled:
        return True
    req_key, spend_key = _token_bucket_keys(user_id)
    req_limit = max(1, int(settings.token_requests_per_minute))
    spend_limit = max(1, int(settings.token_spend_per_minute))
    tokens = max(1, int(amount))
    window_seconds = max(1.0, float(window_seconds))

    if settings.database_url:
        _ensure_table()
        import psycopg

        with psycopg.connect(settings.database_url) as conn, conn.cursor() as cur:
            _purge_postgres(cur, req_key, window_seconds=window_seconds)
            _purge_postgres(cur, spend_key, window_seconds=window_seconds)
            req_used = _sum_postgres(cur, req_key)
            spend_used = _sum_postgres(cur, spend_key)
            if req_used >= req_limit or spend_used + tokens > spend_limit:
                conn.commit()
                return False
            cur.execute(
                "INSERT INTO rate_limit_hits (bucket_key, weight) VALUES (%s, 1)",
                (req_key,),
            )
            cur.execute(
                "INSERT INTO rate_limit_hits (bucket_key, weight) VALUES (%s, %s)",
                (spend_key, tokens),
            )
            conn.commit()
        return True

    with _memory_lock:
        now = time.monotonic()
        req_bucket = _memory_hits[req_key]
        spend_bucket = _memory_hits[spend_key]
        _purge_memory(req_bucket, now=now, window_seconds=window_seconds)
        _purge_memory(spend_bucket, now=now, window_seconds=window_seconds)
        req_used = sum(weight for _, weight in req_bucket)
        spend_used = sum(weight for _, weight in spend_bucket)
        if req_used >= req_limit or spend_used + tokens > spend_limit:
            return False
        req_bucket.append((now, 1))
        spend_bucket.append((now, tokens))
        return True
