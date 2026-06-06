"""Data isolation tests (unit + PostgreSQL integration)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.query_context import QueryContext
from app.main import app
from tests.api.conftest import AuthTestUser, api_key_headers, minimal_report_payload, report_ingest_ids


def test_query_context_user_filters() -> None:
    ctx = QueryContext(user_id="11111111-1111-1111-1111-111111111111", role="USER")
    clause, params = ctx.owner_clause()
    assert "user_id" in clause
    assert params == (ctx.user_id,)


def test_query_context_admin_no_filter() -> None:
    ctx = QueryContext(user_id="11111111-1111-1111-1111-111111111111", role="ADMIN")
    clause, params = ctx.owner_clause()
    assert clause == ""
    assert params == ()


def test_monitor_owner_clause_user() -> None:
    ctx = QueryContext(user_id="22222222-2222-2222-2222-222222222222", role="USER")
    clause, params = ctx.monitor_owner_clause("m")
    assert "m.user_id" in clause
    assert params[0] == ctx.user_id


def test_monitor_accessible_false_without_db(monkeypatch) -> None:
    from app.db import public_queries as pq

    monkeypatch.setattr(pq.settings, "monitoring_database_url", None)
    ctx = QueryContext(user_id="11111111-1111-1111-1111-111111111111", role="USER")
    assert pq.monitor_accessible("00000000-0000-0000-0000-000000000001", ctx) is False


@pytest.fixture(autouse=True)
def _stub_publish(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.publish_service.PublishService.trigger_publish",
        lambda self, rendered_path: None,
    )


def test_user_report_lists_are_isolated(require_db: None, user_a: AuthTestUser, user_b: AuthTestUser) -> None:
    client = TestClient(app)
    req_a = f"req-{uuid.uuid4().hex[:12]}"
    req_b = f"req-{uuid.uuid4().hex[:12]}"

    post_a = client.post(
        "/api/v1/openclaw/reports",
        headers={**api_key_headers(user_a), "X-Request-Id": req_a},
        json=minimal_report_payload(task_id=req_a, keyword="iso-user-a"),
    )
    post_b = client.post(
        "/api/v1/openclaw/reports",
        headers={**api_key_headers(user_b), "X-Request-Id": req_b},
        json=minimal_report_payload(task_id=req_b, keyword="iso-user-b"),
    )
    assert post_a.status_code == 202
    assert post_b.status_code == 202

    list_a = client.get("/api/v1/public/reports", headers=api_key_headers(user_a)).json()
    list_b = client.get("/api/v1/public/reports", headers=api_key_headers(user_b)).json()
    ids_a = report_ingest_ids(list_a)
    ids_b = report_ingest_ids(list_b)
    assert post_a.json()["ingest_id"] in ids_a
    assert post_a.json()["ingest_id"] not in ids_b
    assert post_b.json()["ingest_id"] in ids_b
    assert post_b.json()["ingest_id"] not in ids_a


def test_admin_sees_all_reports(require_db: None, admin_user: AuthTestUser, user_a: AuthTestUser) -> None:
    client = TestClient(app)
    req = f"req-{uuid.uuid4().hex[:12]}"
    post = client.post(
        "/api/v1/openclaw/reports",
        headers={**api_key_headers(user_a), "X-Request-Id": req},
        json=minimal_report_payload(task_id=req),
    )
    ingest_id = post.json()["ingest_id"]

    admin_list = client.get("/api/v1/public/reports", headers=api_key_headers(admin_user))
    assert admin_list.status_code == 200
    ids = report_ingest_ids(admin_list.json())
    assert ingest_id in ids


def test_news_library_scoped(require_db: None, user_a: AuthTestUser, user_b: AuthTestUser) -> None:
    if not settings.news_database_url:
        pytest.skip("news database not configured")

    client = TestClient(app)
    keyword = f"pytest-{uuid.uuid4().hex[:6]}"
    created = client.post(
        "/api/v1/openclaw/news/library",
        headers=api_key_headers(user_a),
        json={
            "keyword": keyword,
            "summary": "user a news",
            "source_url": "https://example.com/a",
            "title": "A",
        },
    )
    assert created.status_code == 201

    list_a = client.get(
        f"/api/v1/public/news/library?keyword={keyword}&limit=20",
        headers=api_key_headers(user_a),
    )
    assert list_a.status_code == 200
    assert len(list_a.json()) >= 1

    list_b = client.get(
        f"/api/v1/public/news/library?keyword={keyword}&limit=20",
        headers=api_key_headers(user_b),
    )
    assert list_b.status_code == 200
    assert list_b.json() == []
