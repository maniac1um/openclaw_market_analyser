"""Gateway chat audit event persistence (openclaw_app database)."""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

from app.core.config import settings


def _connect():
    import psycopg

    if not settings.database_url:
        raise RuntimeError("database_url is not configured")
    return psycopg.connect(settings.database_url)


def ensure_audit_tables() -> None:
    if not settings.database_url:
        return
    sql = """
    CREATE TABLE IF NOT EXISTS gateway_audit_events (
      id BIGSERIAL PRIMARY KEY,
      user_id UUID NOT NULL,
      user_role TEXT NOT NULL,
      session_key TEXT,
      action TEXT NOT NULL,
      message_hash TEXT,
      message_length INT,
      decision TEXT NOT NULL,
      agent_id TEXT,
      gateway_device_role TEXT,
      latency_ms INT,
      error_redacted TEXT,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_gateway_audit_user_created
      ON gateway_audit_events (user_id, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_gateway_audit_decision
      ON gateway_audit_events (decision, created_at DESC);
    """
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(sql)
        conn.commit()


def hash_message(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def insert_gateway_audit_event(
    *,
    user_id: str,
    user_role: str,
    session_key: str | None,
    action: str,
    message: str | None = None,
    decision: str,
    agent_id: str | None = None,
    gateway_device_role: str | None = None,
    latency_ms: int | None = None,
    error_redacted: str | None = None,
) -> None:
    if not settings.database_url:
        return
    msg = message or ""
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO gateway_audit_events (
              user_id, user_role, session_key, action, message_hash, message_length,
              decision, agent_id, gateway_device_role, latency_ms, error_redacted
            ) VALUES (
              %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                user_id,
                user_role,
                session_key,
                action,
                hash_message(msg) if msg else None,
                len(msg) if msg else None,
                decision,
                agent_id,
                gateway_device_role,
                latency_ms,
                error_redacted,
            ),
        )
        conn.commit()


def list_gateway_audit_events(
    *,
    limit: int = 100,
    user_id: str | None = None,
) -> list[dict[str, Any]]:
    if not settings.database_url:
        return []
    cap = max(1, min(int(limit), 500))
    params: list[Any] = []
    where = ""
    if user_id:
        where = "WHERE user_id = %s::uuid"
        params.append(user_id)
    params.append(cap)
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT id, user_id::text, user_role, session_key, action, message_hash,
                   message_length, decision, agent_id, gateway_device_role,
                   latency_ms, error_redacted, created_at
            FROM gateway_audit_events
            {where}
            ORDER BY created_at DESC
            LIMIT %s
            """,
            params,
        )
        rows = cur.fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        created_at = row[12]
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        out.append(
            {
                "id": row[0],
                "user_id": row[1],
                "user_role": row[2],
                "session_key": row[3],
                "action": row[4],
                "message_hash": row[5],
                "message_length": row[6],
                "decision": row[7],
                "agent_id": row[8],
                "gateway_device_role": row[9],
                "latency_ms": row[10],
                "error_redacted": row[11],
                "created_at": created_at,
            }
        )
    return out
