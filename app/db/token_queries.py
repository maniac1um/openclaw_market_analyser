"""Token balance and usage persistence (openclaw_app database)."""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.db.token_grant_queries import (
    GRANT_SOURCE_BONUS,
    ensure_token_grant_tables,
    grant_tokens,
)
from app.db.user_queries import _connect, ensure_user_tables

TZ_SHANGHAI = ZoneInfo("Asia/Shanghai")
VALID_USAGE_RANGES = frozenset({"1h", "6h", "24h", "7d", "30d", "all"})

_RANGE_MS: dict[str, int | None] = {
    "1h": 3_600_000,
    "6h": 21_600_000,
    "24h": 86_400_000,
    "7d": 7 * 86_400_000,
    "30d": 30 * 86_400_000,
    "all": None,
}

_balance_cache: dict[str, tuple[dict[str, int], float]] = {}
_balance_cache_lock = Lock()


class InsufficientTokensError(Exception):
    """Raised when the user lacks tokens for an AI request."""

    def __str__(self) -> str:
        return "Insufficient tokens"


def ensure_token_tables() -> None:
    if not settings.database_url:
        return
    ensure_user_tables()
    sql = """
    CREATE TABLE IF NOT EXISTS token_usage (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      tokens_used BIGINT NOT NULL CHECK (tokens_used > 0),
      endpoint TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_token_usage_user_created
      ON token_usage (user_id, created_at DESC);

    ALTER TABLE token_usage
      ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::jsonb;
    """
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(sql)
        conn.commit()
    ensure_token_grant_tables()


def invalidate_balance_cache(user_id: str) -> None:
    with _balance_cache_lock:
        _balance_cache.pop(user_id, None)


def estimate_tokens(*texts: str) -> int:
    total_chars = sum(len(text) for text in texts if text)
    return max(1, (total_chars + 3) // 4)


def _sum_usage(cur, user_id: str) -> int:
    cur.execute(
        "SELECT COALESCE(SUM(tokens_used), 0) FROM token_usage WHERE user_id = %s::uuid",
        (user_id,),
    )
    return int(cur.fetchone()[0])


def _sum_grants(cur, user_id: str) -> int:
    cur.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM token_grants WHERE user_id = %s::uuid",
        (user_id,),
    )
    return int(cur.fetchone()[0])


def compute_balance_detail(cur, user_id: str) -> dict[str, int]:
    total_grants = _sum_grants(cur, user_id)
    total_usage = _sum_usage(cur, user_id)
    return {
        "balance": total_grants - total_usage,
        "total_grants": total_grants,
        "total_usage": total_usage,
    }


def compute_token_balance(cur, user_id: str) -> int:
    return compute_balance_detail(cur, user_id)["balance"]


def get_user_balance_detail(user_id: str, *, use_cache: bool = True) -> dict[str, int]:
    ttl = int(settings.token_balance_cache_seconds)
    if use_cache and ttl > 0:
        with _balance_cache_lock:
            cached = _balance_cache.get(user_id)
            if cached and time.monotonic() < cached[1]:
                return dict(cached[0])

    ensure_token_tables()
    with _connect() as conn, conn.cursor() as cur:
        detail = compute_balance_detail(cur, user_id)

    if ttl > 0:
        with _balance_cache_lock:
            _balance_cache[user_id] = (detail, time.monotonic() + ttl)
    return detail


def get_token_balance(user_id: str) -> int:
    return get_user_balance_detail(user_id)["balance"]


def set_token_balance(user_id: str, balance: int) -> None:
    """Test helper: reset ledger to a single bonus grant."""
    ensure_token_tables()
    target = max(0, int(balance))
    with _connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE id = %s::uuid FOR UPDATE", (user_id,))
        if not cur.fetchone():
            raise KeyError(f"user not found: {user_id}")
        cur.execute("DELETE FROM token_usage WHERE user_id = %s::uuid", (user_id,))
        cur.execute("DELETE FROM token_grants WHERE user_id = %s::uuid", (user_id,))
        if target > 0:
            grant_tokens(user_id, target, GRANT_SOURCE_BONUS, conn=conn, cur=cur)
        conn.commit()
    invalidate_balance_cache(user_id)


def consume_tokens(
    *,
    user_id: str,
    tokens_used: int,
    endpoint: str,
    metadata: dict[str, Any] | None = None,
) -> int:
    """Record usage when balance allows. Returns remaining balance."""
    ensure_token_tables()
    amount = max(1, int(tokens_used))
    usage_id = str(uuid.uuid4())
    meta_json = json.dumps(metadata or {}, ensure_ascii=False)
    with _connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE id = %s::uuid FOR UPDATE", (user_id,))
        if not cur.fetchone():
            conn.rollback()
            raise KeyError(f"user not found: {user_id}")
        balance = compute_token_balance(cur, user_id)
        if balance < amount:
            conn.rollback()
            raise InsufficientTokensError()
        cur.execute(
            """
            INSERT INTO token_usage (id, user_id, tokens_used, endpoint, metadata)
            VALUES (%s::uuid, %s::uuid, %s, %s, %s::jsonb)
            """,
            (usage_id, user_id, amount, endpoint[:256], meta_json),
        )
        conn.commit()
    invalidate_balance_cache(user_id)
    return balance - amount


def _normalize_range(range_key: str) -> str:
    return range_key if range_key in VALID_USAGE_RANGES else "7d"


def _bucket_floor(dt: datetime, *, hourly: bool) -> datetime:
    local = dt.astimezone(TZ_SHANGHAI)
    if hourly:
        return local.replace(minute=0, second=0, microsecond=0)
    return local.replace(hour=0, minute=0, second=0, microsecond=0)


def _fill_usage_series(
    rows: list[tuple],
    *,
    range_key: str,
    now: datetime,
    hourly: bool,
) -> list[dict[str, object]]:
    bucket_map: dict[str, int] = {}
    for bucket, tokens in rows:
        if bucket is None:
            continue
        b = bucket if isinstance(bucket, datetime) else datetime.fromisoformat(str(bucket))
        if b.tzinfo is None:
            b = b.replace(tzinfo=TZ_SHANGHAI)
        key = _bucket_floor(b, hourly=hourly).isoformat()
        bucket_map[key] = bucket_map.get(key, 0) + int(tokens)

    ms = _RANGE_MS[range_key]
    if ms is not None:
        start = _bucket_floor(now - timedelta(milliseconds=ms), hourly=hourly)
    elif bucket_map:
        earliest = min(datetime.fromisoformat(k) for k in bucket_map)
        start = _bucket_floor(earliest, hourly=hourly)
    else:
        start = _bucket_floor(now - timedelta(days=7), hourly=hourly)

    end = _bucket_floor(now, hourly=hourly)
    step = timedelta(hours=1) if hourly else timedelta(days=1)

    series: list[dict[str, object]] = []
    current = start
    while current <= end:
        key = current.isoformat()
        series.append({"bucket": key, "tokens": bucket_map.get(key, 0)})
        current += step
    return series


def get_usage_stats(user_id: str, *, range_key: str = "7d") -> dict[str, object]:
    """Aggregate token usage for charts and summary stats."""
    range_key = _normalize_range(range_key)
    ensure_token_tables()
    now = datetime.now(TZ_SHANGHAI)
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    hourly = range_key in {"1h", "6h", "24h"}
    trunc = "hour" if hourly else "day"
    ms = _RANGE_MS[range_key]
    range_start = None if ms is None else now - timedelta(milliseconds=ms)

    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT COALESCE(SUM(tokens_used), 0)
            FROM token_usage
            WHERE user_id = %s::uuid AND created_at >= %s
            """,
            (user_id, start_of_today.astimezone(timezone.utc)),
        )
        today = int(cur.fetchone()[0])

        cur.execute(
            "SELECT COALESCE(SUM(tokens_used), 0) FROM token_usage WHERE user_id = %s::uuid",
            (user_id,),
        )
        total = int(cur.fetchone()[0])

        if range_start is None:
            cur.execute(
                """
                SELECT date_trunc(%s, created_at AT TIME ZONE 'Asia/Shanghai') AS bucket,
                       COALESCE(SUM(tokens_used), 0)::bigint AS tokens
                FROM token_usage
                WHERE user_id = %s::uuid
                GROUP BY 1
                ORDER BY 1
                """,
                (trunc, user_id),
            )
        else:
            cur.execute(
                """
                SELECT date_trunc(%s, created_at AT TIME ZONE 'Asia/Shanghai') AS bucket,
                       COALESCE(SUM(tokens_used), 0)::bigint AS tokens
                FROM token_usage
                WHERE user_id = %s::uuid AND created_at >= %s
                GROUP BY 1
                ORDER BY 1
                """,
                (trunc, user_id, range_start.astimezone(timezone.utc)),
            )
        rows = cur.fetchall()

    series = _fill_usage_series(rows, range_key=range_key, now=now, hourly=hourly)
    range_total = sum(int(point["tokens"]) for point in series)

    return {
        "today": today,
        "total": total,
        "range": range_key,
        "range_total": range_total,
        "series": series,
    }


def list_usage_entries(
    user_id: str,
    *,
    range_key: str = "7d",
    limit: int = 100,
) -> list[dict[str, object]]:
    """Recent token usage rows with metadata for the usage activity feed."""
    range_key = _normalize_range(range_key)
    ensure_token_tables()
    limit = max(1, min(int(limit), 500))
    now = datetime.now(TZ_SHANGHAI)
    ms = _RANGE_MS[range_key]
    range_start = None if ms is None else now - timedelta(milliseconds=ms)

    with _connect() as conn, conn.cursor() as cur:
        if range_start is None:
            cur.execute(
                """
                SELECT id, tokens_used, endpoint, metadata, created_at
                FROM token_usage
                WHERE user_id = %s::uuid
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
        else:
            cur.execute(
                """
                SELECT id, tokens_used, endpoint, metadata, created_at
                FROM token_usage
                WHERE user_id = %s::uuid AND created_at >= %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (user_id, range_start.astimezone(timezone.utc), limit),
            )
        rows = cur.fetchall()

    entries: list[dict[str, object]] = []
    for row in rows:
        raw_meta = row[3]
        if isinstance(raw_meta, dict):
            metadata = raw_meta
        elif raw_meta:
            metadata = json.loads(raw_meta) if isinstance(raw_meta, str) else dict(raw_meta)
        else:
            metadata = {}
        created = row[4]
        if isinstance(created, datetime):
            created_iso = created.astimezone(timezone.utc).isoformat()
        else:
            created_iso = str(created)
        entries.append(
            {
                "id": str(row[0]),
                "tokens_used": int(row[1]),
                "endpoint": str(row[2]),
                "metadata": metadata,
                "created_at": created_iso,
            }
        )
    return entries
