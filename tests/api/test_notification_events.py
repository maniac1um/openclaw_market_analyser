"""Event-driven notification tests."""

from __future__ import annotations

import pytest

from app.core.config import settings
from app.db import notification_queries as nq
from app.services.notification_service import (
    NOTIFICATION_TYPE_REPORT_READY,
    NOTIFICATION_TYPE_TOKEN_LOW,
    NOTIFICATION_TYPE_WORKFLOW_DONE,
    create_notification,
    emit_report_ready,
    emit_token_low,
    emit_workflow_done,
)
from tests.api.conftest import _create_test_user


@pytest.fixture
def require_db() -> None:
    if not settings.database_url:
        pytest.skip("OPENCLAW_DATABASE_URL not configured")


def test_create_notification_event(require_db: None) -> None:
    user = _create_test_user()
    create_notification(user.user_id, NOTIFICATION_TYPE_REPORT_READY, "《黄金》报告已就绪")

    payload = nq.list_notifications_for_user(user.user_id)
    assert payload["unread_count"] >= 1
    item = payload["notifications"][0]
    assert item["notification_type"] == NOTIFICATION_TYPE_REPORT_READY
    assert "黄金" in item["content"]


def test_emit_token_low_dedupes(require_db: None) -> None:
    user = _create_test_user()
    emit_token_low(user.user_id, balance=5, required=100)
    emit_token_low(user.user_id, balance=5, required=100)

    payload = nq.list_notifications_for_user(user.user_id)
    token_items = [
        n for n in payload["notifications"] if n.get("notification_type") == NOTIFICATION_TYPE_TOKEN_LOW
    ]
    assert len(token_items) == 1


def test_emit_report_ready(require_db: None) -> None:
    user = _create_test_user()
    emit_report_ready(user.user_id, keyword="黄金", ingest_id="abcd1234-0000-4000-8000-000000000001")

    payload = nq.list_notifications_for_user(user.user_id)
    assert any(n.get("notification_type") == NOTIFICATION_TYPE_REPORT_READY for n in payload["notifications"])


def test_emit_workflow_done(require_db: None) -> None:
    user = _create_test_user()
    emit_workflow_done(user.user_id, keyword="原油", publish=False)

    payload = nq.list_notifications_for_user(user.user_id)
    item = next(n for n in payload["notifications"] if n.get("notification_type") == NOTIFICATION_TYPE_WORKFLOW_DONE)
    assert "原油" in item["content"]
