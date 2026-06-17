"""Subscription plan tests."""

from __future__ import annotations

import pytest

from app.core.config import settings
from app.db import subscription_queries as sub_q
from app.db import user_queries as uq
from tests.api.conftest import _create_test_user, login_access_token


@pytest.fixture
def require_db() -> None:
    if not settings.database_url:
        pytest.skip("OPENCLAW_DATABASE_URL not configured")


def test_new_user_default_free_plan(require_db: None) -> None:
    user = _create_test_user()
    sub = sub_q.get_or_create_subscription(user.user_id)

    assert sub.plan == sub_q.PLAN_FREE
    assert sub.status == sub_q.STATUS_ACTIVE
    assert sub.current_period_end is not None


def test_upgrade_to_pro(require_db: None) -> None:
    user = _create_test_user()
    sub_q.get_or_create_subscription(user.user_id)

    upgraded = sub_q.upgrade_subscription(user.user_id)

    assert upgraded.plan == sub_q.PLAN_PRO
    assert upgraded.status == sub_q.STATUS_ACTIVE
    assert upgraded.current_period_end is not None


def test_cancel_subscription(require_db: None) -> None:
    user = _create_test_user()
    sub_q.upgrade_subscription(user.user_id)

    cancelled = sub_q.cancel_subscription(user.user_id)

    assert cancelled.plan == sub_q.PLAN_PRO
    assert cancelled.status == sub_q.STATUS_CANCELLED


def test_subscription_api_flow(require_db: None, client) -> None:
    user = _create_test_user()
    token = login_access_token(user)

    me_res = client.get(
        "/api/v1/public/subscriptions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    body = me_res.json()
    assert body["plan"] == "free"
    assert body["status"] == "active"

    upgrade_res = client.post(
        "/api/v1/public/subscriptions/upgrade",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upgrade_res.status_code == 200
    assert upgrade_res.json()["plan"] == "pro"
    assert upgrade_res.json()["status"] == "active"

    cancel_res = client.post(
        "/api/v1/public/subscriptions/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"
