"""IDOR tests (SQL unit checks + PostgreSQL integration)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.query_context import QueryContext
from app.main import app
from tests.api.conftest import AuthTestUser, api_key_headers, minimal_report_payload


def test_delete_reports_sql_includes_user_filter() -> None:
    ctx = QueryContext(user_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", role="USER")
    clause, params = ctx.owner_clause()
    sql = f"DELETE FROM reports WHERE ingest_id = %s::uuid{clause}"
    assert "user_id" in sql
    assert params[0] == ctx.user_id


def test_admin_delete_reports_sql_scoped_by_default() -> None:
    ctx = QueryContext(user_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", role="ADMIN")
    clause, params = ctx.owner_clause()
    sql = f"DELETE FROM reports WHERE ingest_id = %s::uuid{clause}"
    assert "user_id" in sql
    assert params[0] == ctx.user_id


def test_admin_delete_reports_sql_no_user_filter_when_cross_tenant(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.config.settings.admin_cross_tenant_access", True)
    ctx = QueryContext(user_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", role="ADMIN")
    clause, params = ctx.owner_clause()
    sql = f"DELETE FROM reports WHERE ingest_id = %s::uuid{clause}"
    assert "user_id" not in sql
    assert params == ()


def test_news_library_list_filters_user() -> None:
    ctx = QueryContext(user_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", role="USER")
    clause, params = ctx.owner_clause()
    sql = f"SELECT id FROM news_library WHERE 1=1{clause}"
    assert params == (ctx.user_id,)


def test_external_scheduler_toggle_sql_scoped() -> None:
    ctx = QueryContext(user_id="cccccccc-cccc-cccc-cccc-cccccccccccc", role="USER")
    clause, params = ctx.owner_clause()
    sql = f"UPDATE external_scheduler_configs SET enabled = %s WHERE job_name = %s{clause}"
    assert "user_id" in sql
    assert params == (ctx.user_id,)


@pytest.fixture(autouse=True)
def _stub_publish(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.publish_service.PublishService.trigger_publish",
        lambda self, rendered_path: None,
    )


def test_user_cannot_read_other_ingest_detail(require_db: None, user_a: AuthTestUser, user_b: AuthTestUser) -> None:
    client = TestClient(app)
    req = f"req-{uuid.uuid4().hex[:12]}"
    post = client.post(
        "/api/v1/openclaw/reports",
        headers={**api_key_headers(user_a), "X-Request-Id": req},
        json=minimal_report_payload(task_id=req),
    )
    ingest_id = post.json()["ingest_id"]

    detail = client.get(
        f"/api/v1/public/reports/{ingest_id}",
        headers=api_key_headers(user_b),
    )
    assert detail.status_code == 404


def test_random_uuid_returns_404(require_db: None, user_a: AuthTestUser) -> None:
    client = TestClient(app)
    random_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    resp = client.get(
        f"/api/v1/public/reports/{random_id}",
        headers=api_key_headers(user_a),
    )
    assert resp.status_code == 404


def test_user_cannot_ingest_to_other_monitor(require_db: None, user_a: AuthTestUser, user_b: AuthTestUser) -> None:
    if not settings.monitoring_database_url:
        pytest.skip("monitoring database not configured")

    client = TestClient(app)
    boot = client.post(
        "/api/v1/openclaw/monitoring/bootstrap",
        headers=api_key_headers(user_b),
        json={"keyword": f"idor-{uuid.uuid4().hex[:6]}", "candidate_count": 1},
    )
    monitor_id = boot.json()["monitor_id"]

    ingest = client.post(
        f"/api/v1/openclaw/monitoring/{monitor_id}/observations/ingest",
        headers=api_key_headers(user_a),
        json={"price": 100.0, "currency": "CNY"},
    )
    assert ingest.status_code == 404


def _bootstrap_monitor_for_user(client: TestClient, user: AuthTestUser) -> str:
    boot = client.post(
        "/api/v1/openclaw/monitoring/bootstrap",
        headers=api_key_headers(user),
        json={"keyword": f"idor-{uuid.uuid4().hex[:6]}", "candidate_count": 1},
    )
    assert boot.status_code == 201, boot.text
    return boot.json()["monitor_id"]


def test_user_cannot_read_other_monitor_summary(require_db: None, user_a: AuthTestUser, user_b: AuthTestUser) -> None:
    if not settings.monitoring_database_url:
        pytest.skip("monitoring database not configured")

    client = TestClient(app)
    monitor_id = _bootstrap_monitor_for_user(client, user_b)

    resp = client.get(
        f"/api/v1/openclaw/monitoring/{monitor_id}/summary?window_days=7",
        headers=api_key_headers(user_a),
    )
    assert resp.status_code == 404


def test_user_cannot_run_once_on_other_monitor(require_db: None, user_a: AuthTestUser, user_b: AuthTestUser) -> None:
    if not settings.monitoring_database_url:
        pytest.skip("monitoring database not configured")

    client = TestClient(app)
    monitor_id = _bootstrap_monitor_for_user(client, user_b)

    resp = client.post(
        f"/api/v1/openclaw/monitoring/{monitor_id}/run-once",
        headers=api_key_headers(user_a),
    )
    assert resp.status_code == 404


def test_user_cannot_add_urls_to_other_monitor(require_db: None, user_a: AuthTestUser, user_b: AuthTestUser) -> None:
    if not settings.monitoring_database_url:
        pytest.skip("monitoring database not configured")

    client = TestClient(app)
    monitor_id = _bootstrap_monitor_for_user(client, user_b)

    resp = client.post(
        f"/api/v1/openclaw/monitoring/{monitor_id}/urls",
        headers=api_key_headers(user_a),
        json={"urls": ["https://example.com/product/1"], "platform": "jd"},
    )
    assert resp.status_code == 404


def test_user_cannot_analyze_other_monitor(require_db: None, user_a: AuthTestUser, user_b: AuthTestUser) -> None:
    if not settings.monitoring_database_url:
        pytest.skip("monitoring database not configured")

    client = TestClient(app)
    monitor_id = _bootstrap_monitor_for_user(client, user_b)

    resp = client.post(
        "/api/v1/openclaw/analysis/news-trigger",
        headers=api_key_headers(user_a),
        json={"monitor_id": monitor_id, "publish": False, "window_days": 7, "news_hours": 72, "horizon": "24h"},
    )
    assert resp.status_code == 404


def test_external_scheduler_jobs_sql_scoped() -> None:
    from app.db.query_context import QueryContext

    ctx = QueryContext(user_id="dddddddd-dddd-dddd-dddd-dddddddddddd", role="USER")
    clause, params = ctx.monitor_owner_clause("r")
    sql = f"SELECT job_name FROM external_scheduler_runs r WHERE 1=1{clause}"
    assert "r.user_id" in sql
    assert params == (ctx.user_id,)


def test_user_cannot_run_readiness_on_other_monitor(require_db: None, user_a: AuthTestUser, user_b: AuthTestUser) -> None:
    if not settings.monitoring_database_url:
        pytest.skip("monitoring database not configured")

    client = TestClient(app)
    monitor_id = _bootstrap_monitor_for_user(client, user_b)

    resp = client.get(
        f"/api/v1/public/workflow/run-readiness?monitor_id={monitor_id}",
        headers=api_key_headers(user_a),
    )
    assert resp.status_code == 404


def test_user_cannot_heartbeat_other_monitor(require_db: None, user_a: AuthTestUser, user_b: AuthTestUser) -> None:
    if not settings.monitoring_database_url:
        pytest.skip("monitoring database not configured")

    client = TestClient(app)
    monitor_id = _bootstrap_monitor_for_user(client, user_b)

    resp = client.post(
        "/api/v1/openclaw/monitoring/external-heartbeat",
        headers=api_key_headers(user_a),
        json={
            "job_name": f"pytest-{uuid.uuid4().hex[:8]}",
            "status": "ok",
            "monitor_id": monitor_id,
            "message": "test",
        },
    )
    assert resp.status_code == 404
