"""Order-driven payment / recharge tests."""

from __future__ import annotations

import pytest

from app.core.config import settings
from app.db import payment_queries as pay_q
from app.db import token_queries as tq
from tests.api.conftest import _create_test_user, login_access_token


@pytest.fixture
def require_db() -> None:
    if not settings.database_url:
        pytest.skip("OPENCLAW_DATABASE_URL not configured")


def test_create_payment_pending_no_credit(require_db: None) -> None:
    user = _create_test_user()
    tq.set_token_balance(user.user_id, 100)

    payment = pay_q.create_payment(user.user_id, tokens=1000)

    assert payment["tokens"] == 1000
    assert payment["status"] == "pending"
    assert tq.get_token_balance(user.user_id) == 100


def test_confirm_payment_credits_balance(require_db: None) -> None:
    user = _create_test_user()
    tq.set_token_balance(user.user_id, 100)

    order = pay_q.create_payment(user.user_id, tokens=1000)
    result = pay_q.confirm_payment(order["id"], user.user_id)

    assert result["status"] == "success"
    assert result["token_balance"] == 1100
    assert tq.get_token_balance(user.user_id) == 1100


def test_confirm_payment_idempotent(require_db: None) -> None:
    user = _create_test_user()
    tq.set_token_balance(user.user_id, 50)

    order = pay_q.create_payment(user.user_id, tokens=500)
    first = pay_q.confirm_payment(order["id"], user.user_id)
    second = pay_q.confirm_payment(order["id"], user.user_id)

    assert first["token_balance"] == 550
    assert second["token_balance"] == 550
    assert tq.get_token_balance(user.user_id) == 550


def test_payment_order_api_flow(require_db: None, client) -> None:
    user = _create_test_user()
    tq.set_token_balance(user.user_id, 50)
    token = login_access_token(user)

    create_res = client.post(
        "/api/v1/public/payments",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    assert create_res.status_code == 200
    order = create_res.json()
    assert order["status"] == "pending"
    assert order["tokens"] == settings.simulated_recharge_amount

    confirm_res = client.post(
        f"/api/v1/public/payments/{order['id']}/confirm",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert confirm_res.status_code == 200
    confirmed = confirm_res.json()
    assert confirmed["status"] == "success"
    assert confirmed["token_balance"] == 50 + settings.simulated_recharge_amount

    poll_res = client.get(
        f"/api/v1/public/payments/{order['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert poll_res.status_code == 200
    assert poll_res.json()["status"] == "success"


def test_billing_recharge_removed(require_db: None, client) -> None:
    user = _create_test_user()
    token = login_access_token(user)

    res = client.post(
        "/api/v1/public/billing/recharge",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404
