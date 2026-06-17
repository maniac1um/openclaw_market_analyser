"""User subscription plans (openclaw_app database)."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import settings
from app.db.subscription_models import Subscription
from app.db.user_queries import _connect, ensure_user_tables

PLAN_FREE = "free"
PLAN_PRO = "pro"
STATUS_ACTIVE = "active"
STATUS_CANCELLED = "cancelled"

_VALID_PLANS = frozenset({PLAN_FREE, PLAN_PRO})
_VALID_STATUSES = frozenset({STATUS_ACTIVE, STATUS_CANCELLED})


def ensure_subscription_tables() -> None:
    if not settings.database_url:
        return
    ensure_user_tables()
    sql = """
    CREATE TABLE IF NOT EXISTS subscriptions (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
      plan TEXT NOT NULL CHECK (plan IN ('free', 'pro')),
      status TEXT NOT NULL CHECK (status IN ('active', 'cancelled')),
      current_period_end TIMESTAMPTZ,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions (user_id);
    """
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(sql)
        cur.execute(
            """
            INSERT INTO subscriptions (user_id, plan, status)
            SELECT u.id, %s, %s
            FROM users u
            WHERE NOT EXISTS (
              SELECT 1 FROM subscriptions s WHERE s.user_id = u.id
            )
            """,
            (PLAN_FREE, STATUS_ACTIVE),
        )
        period_days = int(settings.subscription_grant_period_days)
        cur.execute(
            """
            UPDATE subscriptions
            SET current_period_end = NOW() + make_interval(days => %s)
            WHERE current_period_end IS NULL
            """,
            (period_days,),
        )
        conn.commit()


def _row_to_subscription(row: tuple) -> Subscription:
    return Subscription(
        id=str(row[0]),
        user_id=str(row[1]),
        plan=str(row[2]),
        status=str(row[3]),
        current_period_end=row[4],
        created_at=row[5],
    )


def subscription_to_dict(sub: Subscription) -> dict[str, Any]:
    period_end = sub.current_period_end
    created = sub.created_at
    return {
        "id": sub.id,
        "user_id": sub.user_id,
        "plan": sub.plan,
        "status": sub.status,
        "current_period_end": period_end.isoformat() if period_end else None,
        "created_at": created.isoformat() if created else None,
    }


def monthly_tokens_for_plan(plan: str) -> int:
    if plan == PLAN_PRO:
        return int(settings.subscription_monthly_tokens_pro)
    return int(settings.subscription_monthly_tokens_free)


def _initial_period_end() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=int(settings.subscription_grant_period_days))


def process_due_subscription_grants() -> dict[str, object]:
    """Grant monthly tokens for active subscriptions whose period has ended."""
    from app.db.token_grant_queries import GRANT_SOURCE_SUBSCRIPTION, grant_tokens
    from app.db.token_queries import ensure_token_tables

    ensure_subscription_tables()
    ensure_token_tables()
    now = datetime.now(timezone.utc)
    period_days = int(settings.subscription_grant_period_days)
    grants: list[dict[str, object]] = []

    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, user_id, plan, status, current_period_end, created_at
            FROM subscriptions
            WHERE status = %s
              AND (current_period_end IS NULL OR current_period_end <= %s)
            ORDER BY created_at
            FOR UPDATE
            """,
            (STATUS_ACTIVE, now),
        )
        rows = cur.fetchall()
        for row in rows:
            sub = _row_to_subscription(row)
            amount = monthly_tokens_for_plan(sub.plan)
            new_period_end = now + timedelta(days=period_days)
            grant_tokens(
                sub.user_id,
                amount,
                GRANT_SOURCE_SUBSCRIPTION,
                conn=conn,
                cur=cur,
            )
            cur.execute(
                """
                UPDATE subscriptions
                SET current_period_end = %s
                WHERE id = %s::uuid
                """,
                (new_period_end, sub.id),
            )
            grants.append(
                {
                    "user_id": sub.user_id,
                    "plan": sub.plan,
                    "amount": amount,
                    "current_period_end": new_period_end.isoformat(),
                }
            )
        conn.commit()

    return {"granted_count": len(grants), "grants": grants}


def create_default_subscription(user_id: str, *, conn=None, cur=None) -> Subscription:
    """Create a free active subscription for a new user."""
    ensure_subscription_tables()
    sub_id = str(uuid.uuid4())
    period_end = _initial_period_end()
    if conn is not None and cur is not None:
        cur.execute(
            """
            INSERT INTO subscriptions (id, user_id, plan, status, current_period_end)
            VALUES (%s::uuid, %s::uuid, %s, %s, %s)
            ON CONFLICT (user_id) DO NOTHING
            RETURNING id, user_id, plan, status, current_period_end, created_at
            """,
            (sub_id, user_id, PLAN_FREE, STATUS_ACTIVE, period_end),
        )
        row = cur.fetchone()
        if row:
            return _row_to_subscription(row)
        cur.execute(
            """
            SELECT id, user_id, plan, status, current_period_end, created_at
            FROM subscriptions WHERE user_id = %s::uuid
            """,
            (user_id,),
        )
        existing = cur.fetchone()
        if existing:
            return _row_to_subscription(existing)
        raise RuntimeError("Failed to create default subscription")

    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO subscriptions (id, user_id, plan, status, current_period_end)
            VALUES (%s::uuid, %s::uuid, %s, %s, %s)
            ON CONFLICT (user_id) DO NOTHING
            RETURNING id, user_id, plan, status, current_period_end, created_at
            """,
            (sub_id, user_id, PLAN_FREE, STATUS_ACTIVE, period_end),
        )
        row = cur.fetchone()
        if not row:
            cur.execute(
                """
                SELECT id, user_id, plan, status, current_period_end, created_at
                FROM subscriptions WHERE user_id = %s::uuid
                """,
                (user_id,),
            )
            row = cur.fetchone()
        conn.commit()
    if not row:
        raise RuntimeError("Failed to create default subscription")
    return _row_to_subscription(row)


def get_subscription(user_id: str) -> Subscription | None:
    ensure_subscription_tables()
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, user_id, plan, status, current_period_end, created_at
            FROM subscriptions
            WHERE user_id = %s::uuid
            """,
            (user_id,),
        )
        row = cur.fetchone()
    return _row_to_subscription(row) if row else None


def get_or_create_subscription(user_id: str) -> Subscription:
    sub = get_subscription(user_id)
    if sub:
        return sub
    return create_default_subscription(user_id)


def upgrade_subscription(user_id: str) -> Subscription:
    ensure_subscription_tables()
    period_end = _initial_period_end()
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO subscriptions (user_id, plan, status, current_period_end)
            VALUES (%s::uuid, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE
            SET plan = EXCLUDED.plan,
                status = EXCLUDED.status,
                current_period_end = EXCLUDED.current_period_end
            RETURNING id, user_id, plan, status, current_period_end, created_at
            """,
            (user_id, PLAN_PRO, STATUS_ACTIVE, period_end),
        )
        row = cur.fetchone()
        conn.commit()
    if not row:
        raise RuntimeError("Failed to upgrade subscription")
    return _row_to_subscription(row)


def cancel_subscription(user_id: str) -> Subscription:
    ensure_subscription_tables()
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE subscriptions
            SET status = %s
            WHERE user_id = %s::uuid
            RETURNING id, user_id, plan, status, current_period_end, created_at
            """,
            (STATUS_CANCELLED, user_id),
        )
        row = cur.fetchone()
        conn.commit()
    if not row:
        raise KeyError("subscription not found")
    return _row_to_subscription(row)
