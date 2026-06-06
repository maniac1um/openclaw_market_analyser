"""Structured audit logging for Gateway proxy operations."""

from __future__ import annotations

import logging

from app.db import audit_queries as aq

logger = logging.getLogger(__name__)


def log_gateway_event(
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
    """Persist audit row and emit structured log (message body never logged)."""
    try:
        aq.insert_gateway_audit_event(
            user_id=user_id,
            user_role=user_role,
            session_key=session_key,
            action=action,
            message=message,
            decision=decision,
            agent_id=agent_id,
            gateway_device_role=gateway_device_role,
            latency_ms=latency_ms,
            error_redacted=error_redacted,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("gateway audit insert failed user_id=%s action=%s: %s", user_id, action, exc)

    msg_hash = aq.hash_message(message)[:16] if message else "-"
    logger.info(
        "gateway_audit user_id=%s role=%s action=%s decision=%s agent=%s device_role=%s "
        "session=%s msg_hash=%s latency_ms=%s",
        user_id,
        user_role,
        action,
        decision,
        agent_id or "-",
        gateway_device_role or "-",
        (session_key or "-")[:36],
        msg_hash,
        latency_ms if latency_ms is not None else "-",
    )
