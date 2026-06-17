"""User balance API tests."""

from __future__ import annotations

import pytest

from app.core.config import settings
from app.db import token_queries as tq
from tests.api.conftest import _create_test_user, login_access_token


@pytest.fixture
def require_db() -> None:
    if not settings.database_url:
        pytest.skip("OPENCLAW_DATABASE_URL not configured")


def test_user_balance_api(require_db: None, client) -> None:
    user = _create_test_user()
    tq.set_token_balance(user.user_id, 4321)
    token = login_access_token(user)

    res = client.get(
        "/api/v1/public/users/balance",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["balance"] == 4321
    assert body["total_grants"] == 4321
    assert body["total_usage"] == 0


def test_balance_equals_grants_minus_usage(require_db: None) -> None:
    user = _create_test_user()
    tq.set_token_balance(user.user_id, 500)
    tq.consume_tokens(
        user_id=user.user_id,
        tokens_used=120,
        endpoint="workflow_only",
    )

    detail = tq.get_user_balance_detail(user.user_id, use_cache=False)
    assert detail["total_grants"] == 500
    assert detail["total_usage"] == 120
    assert detail["balance"] == 380
