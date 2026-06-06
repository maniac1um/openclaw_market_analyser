"""OpenClaw per-user API key and public read (scheme B) integration tests."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from tests.api.conftest import AuthTestUser, api_key_headers, bearer_headers, report_ingest_ids, minimal_report_payload


@pytest.fixture(autouse=True)
def _stub_publish(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.publish_service.PublishService.trigger_publish",
        lambda self, rendered_path: None,
    )


def test_invalid_api_key_returns_401() -> None:
    client = TestClient(app)
    resp = client.get("/api/v1/public/reports", headers={"X-Api-Key": "oc_invalid_key"})
    assert resp.status_code == 401


def test_user_api_key_post_report(require_db: None, user_a: AuthTestUser) -> None:
    client = TestClient(app)
    request_id = f"req-{uuid.uuid4().hex[:12]}"
    headers = {**api_key_headers(user_a), "X-Request-Id": request_id}
    resp = client.post(
        "/api/v1/openclaw/reports",
        headers=headers,
        json=minimal_report_payload(task_id=request_id),
    )
    assert resp.status_code == 202
    ingest_id = resp.json()["ingest_id"]

    get_resp = client.get(
        f"/api/v1/openclaw/reports/{ingest_id}",
        headers=api_key_headers(user_a),
    )
    assert get_resp.status_code == 200


def test_user_b_cannot_read_user_a_ingest(require_db: None, user_a: AuthTestUser, user_b: AuthTestUser) -> None:
    client = TestClient(app)
    request_id = f"req-{uuid.uuid4().hex[:12]}"
    headers = {**api_key_headers(user_a), "X-Request-Id": request_id}
    post = client.post(
        "/api/v1/openclaw/reports",
        headers=headers,
        json=minimal_report_payload(task_id=request_id),
    )
    assert post.status_code == 202
    ingest_id = post.json()["ingest_id"]

    cross = client.get(
        f"/api/v1/openclaw/reports/{ingest_id}",
        headers=api_key_headers(user_b),
    )
    assert cross.status_code == 404


def test_public_reports_scoped_to_user(require_db: None, user_a: AuthTestUser, user_b: AuthTestUser) -> None:
    client = TestClient(app)
    request_id = f"req-{uuid.uuid4().hex[:12]}"
    post = client.post(
        "/api/v1/openclaw/reports",
        headers={**api_key_headers(user_a), "X-Request-Id": request_id},
        json=minimal_report_payload(task_id=request_id, keyword="iso-a"),
    )
    assert post.status_code == 202
    ingest_id = post.json()["ingest_id"]

    list_a = client.get("/api/v1/public/reports", headers=api_key_headers(user_a))
    assert list_a.status_code == 200
    ids_a = report_ingest_ids(list_a.json())
    assert ingest_id in ids_a

    list_b = client.get("/api/v1/public/reports", headers=api_key_headers(user_b))
    assert list_b.status_code == 200
    ids_b = report_ingest_ids(list_b.json())
    assert ingest_id not in ids_b


def test_public_reports_jwt_scoped(require_db: None, user_a: AuthTestUser) -> None:
    client = TestClient(app)
    request_id = f"req-{uuid.uuid4().hex[:12]}"
    post = client.post(
        "/api/v1/openclaw/reports",
        headers={**api_key_headers(user_a), "X-Request-Id": request_id},
        json=minimal_report_payload(task_id=request_id),
    )
    ingest_id = post.json()["ingest_id"]

    jwt_resp = client.get("/api/v1/public/reports", headers=bearer_headers(user_a))
    assert jwt_resp.status_code == 200
    ids = report_ingest_ids(jwt_resp.json())
    assert ingest_id in ids


def test_public_unauthenticated_returns_401() -> None:
    client = TestClient(app)
    assert client.get("/api/v1/public/reports").status_code == 401


def test_bootstrap_monitor_scoped(require_db: None, user_a: AuthTestUser, user_b: AuthTestUser) -> None:
    if not settings.monitoring_database_url:
        pytest.skip("monitoring database not configured")

    client = TestClient(app)
    boot = client.post(
        "/api/v1/openclaw/monitoring/bootstrap",
        headers=api_key_headers(user_a),
        json={"keyword": f"pytest-{uuid.uuid4().hex[:6]}", "candidate_count": 1},
    )
    assert boot.status_code == 201
    monitor_id = boot.json()["monitor_id"]

    ok = client.get(
        f"/api/v1/public/monitoring/{monitor_id}/timeseries?window_days=7",
        headers=api_key_headers(user_a),
    )
    assert ok.status_code == 200

    cross = client.get(
        f"/api/v1/public/monitoring/{monitor_id}/timeseries?window_days=7",
        headers=api_key_headers(user_b),
    )
    assert cross.status_code == 404


def test_create_api_key_via_portal(admin_user: AuthTestUser) -> None:
    client = TestClient(app)
    login = client.post(
        "/api/v1/public/auth/login",
        json={"email": admin_user.email, "password": admin_user.password},
    )
    token = login.json()["access_token"]
    created = client.post(
        "/api/v1/public/auth/api-keys",
        headers={"Authorization": f"Bearer {token}"},
        json={"label": "portal-test"},
    )
    assert created.status_code == 200
    body = created.json()
    assert body["api_key"].startswith("oc_")
    assert "api_key" in body


def test_revoked_api_key_rejected(require_db: None, user_a: AuthTestUser) -> None:
    from app.db import user_queries as uq

    client = TestClient(app)
    raw_key, record = uq.create_api_key(user_id=user_a.user_id, label="revoke-me")
    assert (
        client.get("/api/v1/public/reports", headers={"X-Api-Key": raw_key}).status_code
        in {200, 503}
    )
    assert uq.revoke_api_key(user_id=user_a.user_id, key_id=record.id)
    assert client.get("/api/v1/public/reports", headers={"X-Api-Key": raw_key}).status_code == 401
