"""Token grants ledger tests."""

from __future__ import annotations

import pytest

from app.core.config import settings
from app.db import payment_queries as pay_q
from app.db import token_grant_queries as grant_q
from app.db import token_queries as tq
from tests.api.conftest import _create_test_user


@pytest.fixture
def require_db() -> None:
    if not settings.database_url:
        pytest.skip("OPENCLAW_DATABASE_URL not configured")


def test_balance_is_grants_minus_usage(require_db: None) -> None:
    user = _create_test_user()
    tq.set_token_balance(user.user_id, 200)

    remaining = tq.consume_tokens(
        user_id=user.user_id,
        tokens_used=50,
        endpoint="workflow_only",
        metadata={"type": "workflow", "action": "analysis"},
    )

    assert remaining == 150
    assert tq.get_token_balance(user.user_id) == 150


def test_payment_confirm_writes_payment_grant(require_db: None) -> None:
    user = _create_test_user()
    tq.set_token_balance(user.user_id, 100)

    order = pay_q.create_payment(user.user_id, tokens=500)
    pay_q.confirm_payment(order["id"], user.user_id)

    assert tq.get_token_balance(user.user_id) == 600
    assert grant_q.sum_grants(user.user_id) == 600


def test_new_user_gets_bonus_grant(require_db: None) -> None:
    user = _create_test_user()

    assert grant_q.sum_grants(user.user_id) == settings.default_token_balance
    assert tq.get_token_balance(user.user_id) == settings.default_token_balance
