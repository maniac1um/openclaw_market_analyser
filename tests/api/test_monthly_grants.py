"""Monthly subscription token grant tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.core.config import settings
from app.db import subscription_queries as sub_q
from app.db import token_grant_queries as grant_q
from app.db import token_queries as tq
from app.db.user_queries import _connect
from tests.api.conftest import _create_test_user


@pytest.fixture
def require_db() -> None:
    if not settings.database_url:
        pytest.skip("OPENCLAW_DATABASE_URL not configured")


def _force_period_due(user_id: str) -> None:
    past = datetime.now(timezone.utc) - timedelta(days=1)
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE subscriptions SET current_period_end = %s WHERE user_id = %s::uuid",
            (past, user_id),
        )
        conn.commit()


def test_upgrade_does_not_grant_tokens(require_db: None) -> None:
    user = _create_test_user()
    tq.set_token_balance(user.user_id, 0)
    before = grant_q.sum_grants(user.user_id)

    sub_q.upgrade_subscription(user.user_id)

    assert grant_q.sum_grants(user.user_id) == before


def test_monthly_grant_free_plan(require_db: None) -> None:
    user = _create_test_user()
    tq.set_token_balance(user.user_id, 0)
    _force_period_due(user.user_id)

    result = sub_q.process_due_subscription_grants()

    assert result["granted_count"] == 1
    assert grant_q.sum_grants(user.user_id) == settings.subscription_monthly_tokens_free
    sub = sub_q.get_subscription(user.user_id)
    assert sub is not None
    assert sub.current_period_end is not None
    assert sub.current_period_end > datetime.now(timezone.utc)


def test_monthly_grant_pro_plan(require_db: None) -> None:
    user = _create_test_user()
    tq.set_token_balance(user.user_id, 0)
    sub_q.upgrade_subscription(user.user_id)
    _force_period_due(user.user_id)

    sub_q.process_due_subscription_grants()

    assert grant_q.sum_grants(user.user_id) == settings.subscription_monthly_tokens_pro


def test_cancelled_subscription_skipped(require_db: None) -> None:
    user = _create_test_user()
    tq.set_token_balance(user.user_id, 0)
    sub_q.upgrade_subscription(user.user_id)
    sub_q.cancel_subscription(user.user_id)
    _force_period_due(user.user_id)
    before = grant_q.sum_grants(user.user_id)

    result = sub_q.process_due_subscription_grants()

    assert result["granted_count"] == 0
    assert grant_q.sum_grants(user.user_id) == before
