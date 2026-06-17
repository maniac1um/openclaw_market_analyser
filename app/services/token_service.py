"""Unified token billing for AI and data-processing requests."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from app.core.config import settings
from app.core.rate_limit import acquire_token_rate_limits, check_token_rate_limits
from app.db import token_queries as tq
from app.db.query_context import ADMIN_ROLE
from app.db.token_queries import InsufficientTokensError
from app.services.notification_service import emit_token_low


class TokenRateLimitExceeded(Exception):
    """Raised when per-user token billing rate limits are exceeded."""

    def __str__(self) -> str:
        return "rate limit exceeded"

TOKEN_SOURCE_CHAT = "chat"

# Stored in token_usage.endpoint — one charge per operation.
BILLING_WORKFLOW_WITH_PUBLISH = "workflow_with_publish"
BILLING_WORKFLOW_ONLY = "workflow_only"
BILLING_REPORT_ONLY = "report_only"
BILLING_AGENT_WITH_PUBLISH = "agent_with_publish"
BILLING_AGENT_ONLY = "agent_only"

# Route discriminators passed from API handlers (not stored directly).
ROUTE_WORKFLOW = "workflow"
ROUTE_AGENT = "agent"

VALID_TOKEN_SOURCES = frozenset(
    {
        TOKEN_SOURCE_CHAT,
        BILLING_WORKFLOW_WITH_PUBLISH,
        BILLING_WORKFLOW_ONLY,
        BILLING_REPORT_ONLY,
        BILLING_AGENT_WITH_PUBLISH,
        BILLING_AGENT_ONLY,
    }
)

USAGE_TYPE_CHAT = "chat"
USAGE_TYPE_WORKFLOW = "workflow"
USAGE_TYPE_REPORT = "report"
USAGE_TYPE_AGENT = "agent"

USAGE_ACTION_ANALYSIS = "analysis"
USAGE_ACTION_PUBLISH = "publish"
USAGE_ACTION_INGEST = "ingest"


def estimate_tokens(*texts: str) -> int:
    return tq.estimate_tokens(*texts)


def resolve_analysis_billing_source(*, route: str, publish: bool) -> str:
    """Map API route + publish flag to a single billing source."""
    if route == ROUTE_WORKFLOW:
        return BILLING_WORKFLOW_WITH_PUBLISH if publish else BILLING_WORKFLOW_ONLY
    if route == ROUTE_AGENT:
        return BILLING_AGENT_WITH_PUBLISH if publish else BILLING_AGENT_ONLY
    raise ValueError(f"invalid billing route: {route}")


def fixed_cost_for_source(source: str) -> int:
    if source in {BILLING_WORKFLOW_WITH_PUBLISH, BILLING_WORKFLOW_ONLY}:
        return int(settings.token_workflow_cost)
    if source in {BILLING_AGENT_WITH_PUBLISH, BILLING_AGENT_ONLY}:
        return int(settings.token_agent_cost)
    if source == BILLING_REPORT_ONLY:
        return int(settings.token_report_cost)
    raise ValueError(f"no fixed cost for source: {source}")


def build_usage_metadata(
    *,
    usage_type: str,
    action: str,
    keyword: str | None = None,
) -> dict[str, str]:
    meta: dict[str, str] = {"type": usage_type, "action": action}
    kw = (keyword or "").strip()
    if kw:
        meta["keyword"] = kw[:200]
    return meta


def metadata_for_billing_source(source: str, *, keyword: str | None = None) -> dict[str, str]:
    if source == BILLING_WORKFLOW_WITH_PUBLISH:
        return build_usage_metadata(
            usage_type=USAGE_TYPE_WORKFLOW, action=USAGE_ACTION_PUBLISH, keyword=keyword
        )
    if source == BILLING_WORKFLOW_ONLY:
        return build_usage_metadata(
            usage_type=USAGE_TYPE_WORKFLOW, action=USAGE_ACTION_ANALYSIS, keyword=keyword
        )
    if source == BILLING_AGENT_WITH_PUBLISH:
        return build_usage_metadata(
            usage_type=USAGE_TYPE_AGENT, action=USAGE_ACTION_PUBLISH, keyword=keyword
        )
    if source == BILLING_AGENT_ONLY:
        return build_usage_metadata(
            usage_type=USAGE_TYPE_AGENT, action=USAGE_ACTION_ANALYSIS, keyword=keyword
        )
    if source == BILLING_REPORT_ONLY:
        return build_usage_metadata(
            usage_type=USAGE_TYPE_REPORT, action=USAGE_ACTION_INGEST, keyword=keyword
        )
    if source == TOKEN_SOURCE_CHAT:
        return build_usage_metadata(
            usage_type=USAGE_TYPE_CHAT, action=USAGE_ACTION_ANALYSIS, keyword=keyword
        )
    raise ValueError(f"unknown billing source for metadata: {source}")


def format_usage_label(metadata: dict[str, Any] | None, *, endpoint: str = "") -> str:
    """Human-readable description for a token usage row."""
    if not metadata:
        return _fallback_label(endpoint)

    if str(metadata.get("type") or "") == "credit":
        return "充值到账"

    usage_type = str(metadata.get("type") or "")
    action = str(metadata.get("action") or "")
    keyword = str(metadata.get("keyword") or "").strip()

    if usage_type == USAGE_TYPE_CHAT:
        if keyword:
            preview = keyword if len(keyword) <= 24 else keyword[:24] + "…"
            return f"AI 对话 · {preview}"
        return "AI 对话"

    if action == USAGE_ACTION_ANALYSIS and keyword:
        return f"分析{keyword}"
    if action == USAGE_ACTION_PUBLISH and keyword:
        return f"分析并发布 {keyword}"
    if action == USAGE_ACTION_INGEST and keyword:
        return f"生成报告 {keyword}"

    if action == USAGE_ACTION_ANALYSIS:
        return "市场分析"
    if action == USAGE_ACTION_PUBLISH:
        return "分析并发布报告"
    if action == USAGE_ACTION_INGEST:
        return "生成报告"

    return _fallback_label(endpoint)


def _fallback_label(endpoint: str) -> str:
    mapping = {
        BILLING_WORKFLOW_WITH_PUBLISH: "工作流分析并发布",
        BILLING_WORKFLOW_ONLY: "工作流分析",
        BILLING_AGENT_WITH_PUBLISH: "Agent 分析并发布",
        BILLING_AGENT_ONLY: "Agent 分析",
        BILLING_REPORT_ONLY: "报告入库",
        TOKEN_SOURCE_CHAT: "AI 对话",
    }
    return mapping.get(endpoint, "Token 消耗")


def _skip_billing(portal_role: str) -> bool:
    return portal_role == ADMIN_ROLE


def _check_token_rate_limit(*, user_id: str, amount: int, portal_role: str) -> None:
    if _skip_billing(portal_role) or not settings.token_rate_limit_enabled:
        return
    if not check_token_rate_limits(user_id, amount):
        raise TokenRateLimitExceeded()


def _acquire_token_rate_limit(*, user_id: str, amount: int, portal_role: str) -> None:
    if _skip_billing(portal_role) or not settings.token_rate_limit_enabled:
        return
    if not acquire_token_rate_limits(user_id, amount):
        raise TokenRateLimitExceeded()


def require_tokens(
    *,
    user_id: str,
    amount: int,
    source: str,
    portal_role: str = "USER",
) -> None:
    """Pre-check balance; raises InsufficientTokensError when funds are insufficient."""
    if _skip_billing(portal_role):
        return
    if source not in VALID_TOKEN_SOURCES:
        raise ValueError(f"invalid token source: {source}")
    amount = max(1, int(amount))
    balance = tq.get_token_balance(user_id)
    if balance < amount:
        emit_token_low(user_id, balance=balance, required=amount)
        raise InsufficientTokensError()
    _check_token_rate_limit(user_id=user_id, amount=amount, portal_role=portal_role)


def consume_tokens(
    *,
    user_id: str,
    amount: int,
    source: str,
    portal_role: str = "USER",
    metadata: dict[str, Any] | None = None,
) -> int | None:
    """Unified billing entry. Returns remaining balance, or None when admin bypass."""
    if _skip_billing(portal_role):
        return None
    if source not in VALID_TOKEN_SOURCES:
        raise ValueError(f"invalid token source: {source}")
    amount = max(1, int(amount))
    _acquire_token_rate_limit(user_id=user_id, amount=amount, portal_role=portal_role)
    meta = metadata or metadata_for_billing_source(source)
    return tq.consume_tokens(
        user_id=user_id,
        tokens_used=amount,
        endpoint=source,
        metadata=meta,
    )


def require_tokens_http(
    *,
    user_id: str,
    amount: int,
    source: str,
    portal_role: str = "USER",
) -> None:
    try:
        require_tokens(user_id=user_id, amount=amount, source=source, portal_role=portal_role)
    except InsufficientTokensError as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Insufficient tokens",
        ) from exc
    except TokenRateLimitExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="rate limit exceeded",
        ) from exc


def consume_tokens_http(
    *,
    user_id: str,
    amount: int,
    source: str,
    portal_role: str = "USER",
    metadata: dict[str, Any] | None = None,
) -> int | None:
    try:
        return consume_tokens(
            user_id=user_id,
            amount=amount,
            source=source,
            portal_role=portal_role,
            metadata=metadata,
        )
    except InsufficientTokensError as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Insufficient tokens",
        ) from exc
    except TokenRateLimitExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="rate limit exceeded",
        ) from exc


def require_chat_tokens(*, user_id: str, portal_role: str, user_text: str) -> None:
    required = estimate_tokens(user_text) + int(settings.token_response_reserve)
    require_tokens(user_id=user_id, amount=required, source=TOKEN_SOURCE_CHAT, portal_role=portal_role)


def consume_chat_turn(
    *,
    user_id: str,
    portal_role: str,
    user_text: str,
    assistant_text: str,
) -> int | None:
    preview = user_text.strip().split("\n", 1)[0][:40]
    tokens_used = estimate_tokens(user_text, assistant_text)
    return consume_tokens(
        user_id=user_id,
        amount=tokens_used,
        source=TOKEN_SOURCE_CHAT,
        portal_role=portal_role,
        metadata=build_usage_metadata(
            usage_type=USAGE_TYPE_CHAT,
            action=USAGE_ACTION_ANALYSIS,
            keyword=preview or None,
        ),
    )


def enrich_usage_entries(entries: list[dict[str, object]]) -> list[dict[str, object]]:
    enriched: list[dict[str, object]] = []
    for row in entries:
        meta = row.get("metadata")
        meta_dict = meta if isinstance(meta, dict) else {}
        endpoint = str(row.get("endpoint") or "")
        enriched.append(
            {
                **row,
                "label": format_usage_label(meta_dict, endpoint=endpoint),
            }
        )
    return enriched


__all__ = [
    "BILLING_AGENT_ONLY",
    "BILLING_AGENT_WITH_PUBLISH",
    "BILLING_REPORT_ONLY",
    "BILLING_WORKFLOW_ONLY",
    "BILLING_WORKFLOW_WITH_PUBLISH",
    "InsufficientTokensError",
    "TokenRateLimitExceeded",
    "ROUTE_AGENT",
    "ROUTE_WORKFLOW",
    "TOKEN_SOURCE_CHAT",
    "USAGE_ACTION_ANALYSIS",
    "USAGE_ACTION_INGEST",
    "USAGE_ACTION_PUBLISH",
    "VALID_TOKEN_SOURCES",
    "build_usage_metadata",
    "consume_chat_turn",
    "consume_tokens",
    "consume_tokens_http",
    "enrich_usage_entries",
    "estimate_tokens",
    "fixed_cost_for_source",
    "format_usage_label",
    "metadata_for_billing_source",
    "require_chat_tokens",
    "require_tokens",
    "require_tokens_http",
    "resolve_analysis_billing_source",
]
