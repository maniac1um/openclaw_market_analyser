"""Sanitized error messages for public/admin portal responses."""

from __future__ import annotations


def public_error_detail(*, context: str = "operation") -> str:
    return f"{context} failed"


def sanitize_gateway_probe_detail(detail: str | None) -> str:
    if not detail:
        return "gateway check completed"
    lowered = detail.lower()
    if "connect.challenge" in lowered or "received" in lowered:
        return detail
    if "empty" in lowered:
        return detail
    return "gateway unreachable"


def sanitize_client_error(exc: BaseException) -> str:
    message = str(exc)
    lowered = message.lower()
    if "gateway" in lowered or "detail=" in lowered or "ws://" in lowered or "wss://" in lowered:
        return "OpenClaw Gateway 当前不可用，请稍后重试。"
    if len(message) > 200:
        return public_error_detail(context="request")
    return message
