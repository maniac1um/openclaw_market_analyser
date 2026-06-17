"""Payment orders and token credit on success (openclaw_app database)."""

from __future__ import annotations

import uuid
from typing import Any

from app.core.config import settings
from app.db.token_grant_queries import GRANT_SOURCE_PAYMENT, grant_tokens
from app.db.token_queries import compute_token_balance, ensure_token_tables, get_token_balance
from app.db.user_queries import _connect, ensure_user_tables

PAYMENT_STATUS_PENDING = "pending"
PAYMENT_STATUS_SUCCESS = "success"
PAYMENT_STATUS_FAILED = "failed"


def ensure_payment_tables() -> None:
    if not settings.database_url:
        return
    ensure_user_tables()
    sql = """
    CREATE TABLE IF NOT EXISTS payments (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      amount BIGINT NOT NULL CHECK (amount > 0),
      status TEXT NOT NULL CHECK (status IN ('pending', 'success', 'failed')),
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_payments_user_created
      ON payments (user_id, created_at DESC);

    ALTER TABLE payments ADD COLUMN IF NOT EXISTS tokens BIGINT;
    UPDATE payments SET tokens = amount WHERE tokens IS NULL;
    UPDATE payments SET status = 'success' WHERE status = 'completed';

    ALTER TABLE payments DROP CONSTRAINT IF EXISTS payments_status_check;
    ALTER TABLE payments
      ADD CONSTRAINT payments_status_check
      CHECK (status IN ('pending', 'success', 'failed'));
    """
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(sql)
        conn.commit()


def _row_to_payment(row: tuple) -> dict[str, Any]:
    created_at = row[5]
    return {
        "id": str(row[0]),
        "user_id": str(row[1]),
        "amount": int(row[2]),
        "tokens": int(row[3]),
        "status": str(row[4]),
        "created_at": created_at.isoformat() if created_at else None,
    }


def create_payment(
    user_id: str,
    *,
    tokens: int | None = None,
    amount: int | None = None,
) -> dict[str, Any]:
    """Create a pending payment order (no token credit until confirmed)."""
    ensure_payment_tables()
    token_credit = max(1, int(tokens if tokens is not None else settings.simulated_recharge_amount))
    pay_amount = max(1, int(amount if amount is not None else token_credit))
    payment_id = str(uuid.uuid4())

    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO payments (id, user_id, amount, tokens, status)
            VALUES (%s::uuid, %s::uuid, %s, %s, %s)
            RETURNING id, user_id, amount, tokens, status, created_at
            """,
            (payment_id, user_id, pay_amount, token_credit, PAYMENT_STATUS_PENDING),
        )
        row = cur.fetchone()
        conn.commit()
    if not row:
        raise RuntimeError("Failed to create payment order")
    return _row_to_payment(row)


def get_payment(payment_id: str, user_id: str) -> dict[str, Any] | None:
    ensure_payment_tables()
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, user_id, amount, tokens, status, created_at
            FROM payments
            WHERE id = %s::uuid AND user_id = %s::uuid
            """,
            (payment_id, user_id),
        )
        row = cur.fetchone()
    return _row_to_payment(row) if row else None


def confirm_payment(payment_id: str, user_id: str) -> dict[str, Any]:
    """Mark payment success and credit tokens (idempotent if already success)."""
    ensure_payment_tables()
    ensure_token_tables()

    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, user_id, amount, tokens, status, created_at
            FROM payments
            WHERE id = %s::uuid AND user_id = %s::uuid
            FOR UPDATE
            """,
            (payment_id, user_id),
        )
        row = cur.fetchone()
        if not row:
            raise KeyError("payment not found")

        status = str(row[4])
        if status == PAYMENT_STATUS_FAILED:
            raise ValueError("payment already failed")
        if status == PAYMENT_STATUS_SUCCESS:
            conn.commit()
            payment = _row_to_payment(row)
            payment["token_balance"] = get_token_balance(user_id)
            return payment

        token_credit = int(row[3])
        grant_tokens(
            user_id,
            token_credit,
            GRANT_SOURCE_PAYMENT,
            conn=conn,
            cur=cur,
        )
        cur.execute(
            """
            UPDATE payments
            SET status = %s
            WHERE id = %s::uuid
            RETURNING id, user_id, amount, tokens, status, created_at
            """,
            (PAYMENT_STATUS_SUCCESS, payment_id),
        )
        updated = cur.fetchone()
        balance = compute_token_balance(cur, user_id)
        conn.commit()

    if not updated:
        raise RuntimeError("Failed to confirm payment")
    payment = _row_to_payment(updated)
    payment["token_balance"] = balance
    return payment


def fail_payment(payment_id: str, user_id: str) -> dict[str, Any]:
    ensure_payment_tables()
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE payments
            SET status = %s
            WHERE id = %s::uuid AND user_id = %s::uuid AND status = %s
            RETURNING id, user_id, amount, tokens, status, created_at
            """,
            (PAYMENT_STATUS_FAILED, payment_id, user_id, PAYMENT_STATUS_PENDING),
        )
        row = cur.fetchone()
        conn.commit()
    if not row:
        raise KeyError("payment not found or not pending")
    payment = _row_to_payment(row)
    payment["token_balance"] = get_token_balance(user_id)
    return payment
