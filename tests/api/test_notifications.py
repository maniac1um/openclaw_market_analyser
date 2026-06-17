"""Notification system tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db import notification_queries as nq
from tests.api.conftest import _create_test_user, admin_user, login_access_token


@pytest.fixture
def require_db() -> None:
    if not settings.database_url:
        pytest.skip("OPENCLAW_DATABASE_URL not configured")


def test_create_and_list_notifications(require_db: None) -> None:
    user = _create_test_user()
    other = _create_test_user()

    nq.create_notification(title="全员公告", content="系统维护通知", target="all")
    nq.create_notification(title="私信", content="仅你可见", target=user.user_id)

    payload = nq.list_notifications_for_user(user.user_id)
    titles = [item["title"] for item in payload["notifications"]]
    assert "全员公告" in titles
    assert "私信" in titles
    assert payload["unread_count"] == 2

    other_payload = nq.list_notifications_for_user(other.user_id)
    other_titles = [item["title"] for item in other_payload["notifications"]]
    assert "全员公告" in other_titles
    assert "私信" not in other_titles


def test_mark_notification_read(require_db: None) -> None:
    user = _create_test_user()
    created = nq.create_notification(title="测试", content="内容", target="all")
    notification_id = str(created["id"])

    assert nq.mark_notification_read(user.user_id, notification_id) is True
    payload = nq.list_notifications_for_user(user.user_id)
    assert payload["unread_count"] == 0
    assert payload["notifications"][0]["read"] is True


def test_notifications_api(require_db: None, client: TestClient, admin_user) -> None:
    user = _create_test_user()
    admin_token = login_access_token(admin_user)
    user_token = login_access_token(user)

    create_res = client.post(
        "/api/v1/public/notifications",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"title": "API 通知", "content": "来自管理员", "target": "all"},
    )
    assert create_res.status_code == 200

    list_res = client.get(
        "/api/v1/public/notifications",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert list_res.status_code == 200
    body = list_res.json()
    assert body["unread_count"] >= 1
    notification_id = body["notifications"][0]["id"]

    read_res = client.post(
        f"/api/v1/public/notifications/{notification_id}/read",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert read_res.status_code == 200
    assert read_res.json()["unread_count"] == 0
