"""Token billing rate limit tests."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.core import rate_limit as rl
from app.core.config import settings
from app.db import token_queries as tq
from app.services.token_service import (
    BILLING_REPORT_ONLY,
    TokenRateLimitExceeded,
    consume_tokens,
    require_tokens,
    require_tokens_http,
)

@pytest.fixture(autouse=True)
def enable_token_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "database_url", None)
    monkeypatch.setattr(settings, "token_rate_limit_enabled", True)
    monkeypatch.setattr(settings, "token_requests_per_minute", 3)
    monkeypatch.setattr(settings, "token_spend_per_minute", 100)
    rl._memory_hits.clear()
    rl._table_ready = False


def test_acquire_token_rate_limits_tracks_requests_and_spend() -> None:
    user_id = "00000000-0000-0000-0000-000000000001"
    assert rl.acquire_token_rate_limits(user_id, 40) is True
    assert rl.acquire_token_rate_limits(user_id, 40) is True
    assert rl.sum_weight(f"token-req:{user_id}") == 2
    assert rl.sum_weight(f"token-spend:{user_id}") == 80


def test_acquire_rejects_when_request_limit_exceeded() -> None:
    user_id = "00000000-0000-0000-0000-000000000002"
    for _ in range(3):
        assert rl.acquire_token_rate_limits(user_id, 1) is True
    assert rl.acquire_token_rate_limits(user_id, 1) is False


def test_acquire_rejects_when_spend_limit_exceeded() -> None:
    user_id = "00000000-0000-0000-0000-000000000003"
    assert rl.acquire_token_rate_limits(user_id, 90) is True
    assert rl.acquire_token_rate_limits(user_id, 20) is False


def test_require_tokens_raises_on_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tq, "get_token_balance", lambda user_id: 10_000)
    user_id = "00000000-0000-0000-0000-000000000004"
    for _ in range(3):
        rl.acquire_token_rate_limits(user_id, 1)

    with pytest.raises(TokenRateLimitExceeded):
        require_tokens(
            user_id=user_id,
            amount=1,
            source=BILLING_REPORT_ONLY,
            portal_role="USER",
        )


def test_require_tokens_http_returns_429(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tq, "get_token_balance", lambda user_id: 10_000)
    user_id = "00000000-0000-0000-0000-000000000005"
    for _ in range(3):
        rl.acquire_token_rate_limits(user_id, 1)

    with pytest.raises(HTTPException) as exc:
        require_tokens_http(
            user_id=user_id,
            amount=1,
            source=BILLING_REPORT_ONLY,
        )
    assert exc.value.status_code == 429
    assert exc.value.detail == "rate limit exceeded"


def test_consume_tokens_records_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tq, "get_token_balance", lambda user_id: 10_000)
    monkeypatch.setattr(
        tq,
        "consume_tokens",
        lambda **kwargs: 9975,
    )
    user_id = "00000000-0000-0000-0000-000000000006"

    consume_tokens(
        user_id=user_id,
        amount=25,
        source=BILLING_REPORT_ONLY,
        metadata={"type": "report", "action": "ingest", "keyword": "黄金"},
    )
    assert rl.sum_weight(f"token-req:{user_id}") == 1
    assert rl.sum_weight(f"token-spend:{user_id}") == 25
