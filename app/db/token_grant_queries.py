"""Token grant ledger (openclaw_app database)."""

from __future__ import annotations

import uuid

from app.core.config import settings
from app.db.user_queries import _connect, ensure_user_tables

GRANT_SOURCE_SUBSCRIPTION = "subscription"
GRANT_SOURCE_PAYMENT = "payment"
GRANT_SOURCE_BONUS = "bonus"

_VALID_SOURCES = frozenset(
    {GRANT_SOURCE_SUBSCRIPTION, GRANT_SOURCE_PAYMENT, GRANT_SOURCE_BONUS}
)


def ensure_token_grant_tables() -> None:
    if not settings.database_url:
        return
    ensure_user_tables()
    sql = """
    CREATE TABLE IF NOT EXISTS token_grants (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      amount BIGINT NOT NULL CHECK (amount > 0),
      source TEXT NOT NULL CHECK (source IN ('subscription', 'payment', 'bonus')),
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_token_grants_user_created
      ON token_grants (user_id, created_at DESC);
    """
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(sql)
        cur.execute("DELETE FROM token_usage WHERE endpoint = 'payment'")
        cur.execute(
            """
            INSERT INTO token_grants (user_id, amount, source)
            SELECT u.id, u.token_balance, %s
            FROM users u
            WHERE u.token_balance > 0
              AND NOT EXISTS (
                SELECT 1 FROM token_grants g WHERE g.user_id = u.id
              )
            """,
            (GRANT_SOURCE_BONUS,),
        )
        conn.commit()


def _validate_source(source: str) -> str:
    value = (source or "").strip().lower()
    if value not in _VALID_SOURCES:
        raise ValueError(f"invalid grant source: {source}")
    return value


def grant_tokens(
    user_id: str,
    amount: int,
    source: str,
    *,
    conn=None,
    cur=None,
) -> str:
    """Record a token grant. Returns grant id."""
    from app.db.token_queries import invalidate_balance_cache

    ensure_token_grant_tables()
    grant_source = _validate_source(source)
    grant_amount = max(1, int(amount))
    grant_id = str(uuid.uuid4())

    if conn is not None and cur is not None:
        cur.execute(
            """
            INSERT INTO token_grants (id, user_id, amount, source)
            VALUES (%s::uuid, %s::uuid, %s, %s)
            """,
            (grant_id, user_id, grant_amount, grant_source),
        )
        invalidate_balance_cache(user_id)
        return grant_id

    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO token_grants (id, user_id, amount, source)
            VALUES (%s::uuid, %s::uuid, %s, %s)
            """,
            (grant_id, user_id, grant_amount, grant_source),
        )
        conn.commit()
    invalidate_balance_cache(user_id)
    return grant_id


def sum_grants(user_id: str, *, cur=None) -> int:
    if cur is not None:
        cur.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM token_grants WHERE user_id = %s::uuid",
            (user_id,),
        )
        return int(cur.fetchone()[0])

    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM token_grants WHERE user_id = %s::uuid",
            (user_id,),
        )
        row = cur.fetchone()
    return int(row[0]) if row else 0
