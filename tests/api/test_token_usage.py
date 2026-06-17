"""Token balance and usage billing tests."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.db import token_queries as tq
from app.db import user_queries as uq
from app.services.token_service import (
    InsufficientTokensError,
    BILLING_AGENT_ONLY,
    BILLING_AGENT_WITH_PUBLISH,
    BILLING_REPORT_ONLY,
    BILLING_WORKFLOW_ONLY,
    BILLING_WORKFLOW_WITH_PUBLISH,
    TOKEN_SOURCE_CHAT,
    ROUTE_AGENT,
    ROUTE_WORKFLOW,
    consume_chat_turn,
    consume_tokens,
    consume_tokens_http,
    estimate_tokens,
    fixed_cost_for_source,
    require_chat_tokens,
    require_tokens,
    require_tokens_http,
    resolve_analysis_billing_source,
)
from tests.api.conftest import _create_test_user, login_access_token

TZ_SHANGHAI = ZoneInfo("Asia/Shanghai")


@pytest.fixture
def require_db() -> None:
    if not settings.database_url:
        pytest.skip("OPENCLAW_DATABASE_URL not configured")


def test_estimate_tokens_counts_characters() -> None:
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("a" * 8) == 2
    assert estimate_tokens("hello", "world") == 3


def test_fill_usage_series_generates_daily_buckets() -> None:
    now = datetime(2026, 6, 17, 15, 30, tzinfo=TZ_SHANGHAI)
    rows = [
        (datetime(2026, 6, 15, 10, 0, tzinfo=TZ_SHANGHAI), 100),
        (datetime(2026, 6, 17, 9, 0, tzinfo=TZ_SHANGHAI), 50),
    ]
    series = tq._fill_usage_series(rows, range_key="7d", now=now, hourly=False)
    assert len(series) == 8
    by_day = {point["bucket"][:10]: int(point["tokens"]) for point in series}
    assert by_day["2026-06-15"] == 100
    assert by_day["2026-06-17"] == 50
    assert sum(int(p["tokens"]) for p in series) == 150


def test_normalize_range_defaults_invalid() -> None:
    assert tq._normalize_range("invalid") == "7d"


def test_resolve_analysis_billing_source() -> None:
    assert resolve_analysis_billing_source(route=ROUTE_WORKFLOW, publish=True) == BILLING_WORKFLOW_WITH_PUBLISH
    assert resolve_analysis_billing_source(route=ROUTE_WORKFLOW, publish=False) == BILLING_WORKFLOW_ONLY
    assert resolve_analysis_billing_source(route=ROUTE_AGENT, publish=True) == BILLING_AGENT_WITH_PUBLISH
    assert resolve_analysis_billing_source(route=ROUTE_AGENT, publish=False) == BILLING_AGENT_ONLY


def test_workflow_with_publish_same_cost_as_workflow_only() -> None:
    assert fixed_cost_for_source(BILLING_WORKFLOW_WITH_PUBLISH) == fixed_cost_for_source(BILLING_WORKFLOW_ONLY)


def test_format_usage_label() -> None:
    from app.services.token_service import format_usage_label

    assert format_usage_label({"type": "workflow", "action": "analysis", "keyword": "黄金"}) == "分析黄金"
    assert (
        format_usage_label({"type": "workflow", "action": "publish", "keyword": "黄金"})
        == "分析并发布 黄金"
    )
    assert format_usage_label({"type": "report", "action": "ingest", "keyword": "原油"}) == "生成报告 原油"
    assert format_usage_label({"type": "chat", "action": "analysis"}) == "AI 对话"
    assert format_usage_label({"type": "chat", "action": "analysis", "keyword": "帮我分析黄金"}) == (
        "AI 对话 · 帮我分析黄金"
    )


def test_metadata_for_billing_source() -> None:
    from app.services.token_service import metadata_for_billing_source

    meta = metadata_for_billing_source(BILLING_WORKFLOW_WITH_PUBLISH, keyword="黄金")
    assert meta == {"type": "workflow", "action": "publish", "keyword": "黄金"}


def test_consume_tokens_deducts_balance_and_records_usage(require_db: None) -> None:
    user = _create_test_user()
    tq.set_token_balance(user.user_id, 100)

    remaining = consume_tokens(
        user_id=user.user_id,
        amount=25,
        source=BILLING_WORKFLOW_ONLY,
        metadata={"type": "workflow", "action": "analysis", "keyword": "test"},
    )
    assert remaining == 75
    assert tq.get_token_balance(user.user_id) == 75

    with pytest.raises(InsufficientTokensError):
        consume_tokens(user_id=user.user_id, amount=100, source=BILLING_WORKFLOW_ONLY)


def test_consume_tokens_records_source_as_endpoint(require_db: None) -> None:
    user = _create_test_user()
    tq.set_token_balance(user.user_id, 1000)
    consume_tokens(
        user_id=user.user_id,
        amount=10,
        source=BILLING_REPORT_ONLY,
        metadata={"type": "report", "action": "ingest", "keyword": "黄金"},
    )
    entries = tq.list_usage_entries(user.user_id, range_key="7d", limit=1)
    assert entries[0]["metadata"]["keyword"] == "黄金"
    assert entries[0]["tokens_used"] == 10


def test_require_tokens_blocks_low_balance(require_db: None) -> None:
    user = _create_test_user()
    tq.set_token_balance(user.user_id, 10)

    with pytest.raises(InsufficientTokensError):
        require_tokens(
            user_id=user.user_id,
            amount=fixed_cost_for_source(BILLING_WORKFLOW_ONLY),
            source=BILLING_WORKFLOW_ONLY,
        )


def test_require_chat_tokens_blocks_low_balance(require_db: None) -> None:
    user = _create_test_user()
    tq.set_token_balance(user.user_id, 10)

    with pytest.raises(InsufficientTokensError):
        require_chat_tokens(
            user_id=user.user_id,
            portal_role="USER",
            user_text="x" * 100,
        )


def test_require_tokens_http_returns_402(require_db: None) -> None:
    user = _create_test_user()
    tq.set_token_balance(user.user_id, 0)

    with pytest.raises(HTTPException) as exc:
        require_tokens_http(
            user_id=user.user_id,
            amount=fixed_cost_for_source(BILLING_REPORT_ONLY),
            source=BILLING_REPORT_ONLY,
        )
    assert exc.value.status_code == 402


def test_consume_tokens_http_returns_402(require_db: None) -> None:
    user = _create_test_user()
    tq.set_token_balance(user.user_id, 0)

    with pytest.raises(HTTPException) as exc:
        consume_tokens_http(
            user_id=user.user_id,
            amount=fixed_cost_for_source(BILLING_REPORT_ONLY),
            source=BILLING_REPORT_ONLY,
        )
    assert exc.value.status_code == 402


def test_consume_chat_turn_skips_admin(require_db: None) -> None:
    user = _create_test_user(role="ADMIN")
    tq.set_token_balance(user.user_id, 0)
    result = consume_chat_turn(
        user_id=user.user_id,
        portal_role="ADMIN",
        user_text="hello",
        assistant_text="world",
    )
    assert result is None
    assert tq.get_token_balance(user.user_id) == 0


def test_consume_chat_turn_uses_chat_source(require_db: None) -> None:
    user = _create_test_user()
    tq.set_token_balance(user.user_id, 100)
    remaining = consume_chat_turn(
        user_id=user.user_id,
        portal_role="USER",
        user_text="abcd",
        assistant_text="efgh",
    )
    assert remaining == 98
    assert tq.get_token_balance(user.user_id) == 98


def test_auth_me_includes_token_balance(require_db: None, client) -> None:
    user = _create_test_user()
    tq.set_token_balance(user.user_id, 4321)
    token = login_access_token(user)
    res = client.get("/api/v1/public/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["token_balance"] == 4321
