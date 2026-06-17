"""Unified billing at API entry points."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db import token_queries as tq
from app.main import app
from app.services.token_service import (
    BILLING_AGENT_ONLY,
    BILLING_REPORT_ONLY,
    BILLING_WORKFLOW_ONLY,
    BILLING_WORKFLOW_WITH_PUBLISH,
    fixed_cost_for_source,
)
from tests.api.conftest import AuthTestUser, api_key_headers, login_access_token, minimal_report_payload


@pytest.fixture
def require_db() -> None:
    if not settings.database_url:
        pytest.skip("OPENCLAW_DATABASE_URL not configured")


def test_report_ingest_charges_tokens(
    user_a: AuthTestUser,
    require_db: None,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.services.publish_service.PublishService.trigger_publish",
        lambda self, rendered_path: None,
    )
    cost = fixed_cost_for_source(BILLING_REPORT_ONLY)
    tq.set_token_balance(user_a.user_id, cost - 1)

    client = TestClient(app)
    request_id = f"req-{uuid.uuid4().hex[:12]}"
    headers = {**api_key_headers(user_a), "X-Request-Id": request_id}
    resp = client.post(
        "/api/v1/openclaw/reports",
        headers=headers,
        json=minimal_report_payload(task_id=request_id),
    )
    assert resp.status_code == 402
    assert tq.get_token_balance(user_a.user_id) == cost - 1


def test_report_ingest_idempotent_does_not_double_charge(
    user_a: AuthTestUser,
    require_db: None,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.services.publish_service.PublishService.trigger_publish",
        lambda self, rendered_path: None,
    )
    cost = fixed_cost_for_source(BILLING_REPORT_ONLY)
    tq.set_token_balance(user_a.user_id, cost + 50)

    client = TestClient(app)
    request_id = f"req-{uuid.uuid4().hex[:12]}"
    headers = {**api_key_headers(user_a), "X-Request-Id": request_id}
    payload = minimal_report_payload(task_id=request_id)

    first = client.post("/api/v1/openclaw/reports", headers=headers, json=payload)
    second = client.post("/api/v1/openclaw/reports", headers=headers, json=payload)
    assert first.status_code == 202
    assert second.status_code == 202
    assert tq.get_token_balance(user_a.user_id) == 50


def test_workflow_analysis_rejects_insufficient_tokens(
    user_a: AuthTestUser,
    require_db: None,
    monkeypatch,
) -> None:
    if not settings.monitoring_database_url:
        pytest.skip("monitoring DB not configured")

    from app.services.monitoring_service import MonitoringService

    svc = MonitoringService(settings.monitoring_database_url)
    svc.ensure_tables()
    monitor_id, _ = svc.bootstrap_monitor(keyword="billing-test", user_id=user_a.user_id)

    cost = fixed_cost_for_source(BILLING_WORKFLOW_ONLY)
    tq.set_token_balance(user_a.user_id, cost - 1)

    client = TestClient(app)
    token = login_access_token(user_a)
    resp = client.post(
        "/api/v1/public/workflow/analysis/run",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "monitor_id": monitor_id,
            "window_days": 7,
            "news_hours": 24,
            "horizon": "7d",
            "publish": False,
        },
    )
    assert resp.status_code == 402
    assert tq.get_token_balance(user_a.user_id) == cost - 1


def test_workflow_publish_charges_once_not_twice(
    user_a: AuthTestUser,
    require_db: None,
    monkeypatch,
) -> None:
    if not settings.monitoring_database_url:
        pytest.skip("monitoring DB not configured")

    monkeypatch.setattr(
        "app.services.publish_service.PublishService.trigger_publish",
        lambda self, rendered_path: None,
    )

    from app.services.monitoring_service import MonitoringService

    svc = MonitoringService(settings.monitoring_database_url)
    svc.ensure_tables()
    monitor_id, _ = svc.bootstrap_monitor(keyword="billing-publish-test", user_id=user_a.user_id)

    cost = fixed_cost_for_source(BILLING_WORKFLOW_WITH_PUBLISH)
    report_cost = fixed_cost_for_source(BILLING_REPORT_ONLY)
    # Enough for one combined charge, not workflow + report separately.
    tq.set_token_balance(user_a.user_id, cost + 10)

    client = TestClient(app)
    token = login_access_token(user_a)
    resp = client.post(
        "/api/v1/public/workflow/analysis/run",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "monitor_id": monitor_id,
            "window_days": 7,
            "news_hours": 24,
            "horizon": "7d",
            "publish": True,
        },
    )
    assert resp.status_code == 200, resp.text
    assert tq.get_token_balance(user_a.user_id) == 10
    assert tq.get_token_balance(user_a.user_id) < cost + 10 - report_cost


def test_news_trigger_rejects_insufficient_tokens(
    user_a: AuthTestUser,
    require_db: None,
    monkeypatch,
) -> None:
    if not settings.monitoring_database_url:
        pytest.skip("monitoring DB not configured")

    from app.services.monitoring_service import MonitoringService

    svc = MonitoringService(settings.monitoring_database_url)
    svc.ensure_tables()
    monitor_id, _ = svc.bootstrap_monitor(keyword="billing-agent-test", user_id=user_a.user_id)

    cost = fixed_cost_for_source(BILLING_AGENT_ONLY)
    tq.set_token_balance(user_a.user_id, cost - 1)

    client = TestClient(app)
    resp = client.post(
        "/api/v1/openclaw/analysis/news-trigger",
        headers=api_key_headers(user_a),
        json={
            "monitor_id": monitor_id,
            "window_days": 7,
            "news_hours": 24,
            "horizon": "7d",
            "publish": False,
        },
    )
    assert resp.status_code == 402
    assert tq.get_token_balance(user_a.user_id) == cost - 1
