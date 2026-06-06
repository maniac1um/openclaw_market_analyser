import uuid

from fastapi.testclient import TestClient

from app.main import app
from tests.api.conftest import AuthTestUser, api_key_headers, login_client


def test_public_reports_unauthenticated_returns_401() -> None:
    client = TestClient(app)
    assert client.get("/api/v1/public/reports").status_code == 401


def test_public_reports_with_per_user_api_key(admin_user: AuthTestUser) -> None:
    client = TestClient(app)
    resp = client.get("/api/v1/public/reports", headers=api_key_headers(admin_user))
    assert resp.status_code in {200, 503}


def test_legacy_global_api_key_rejected_when_disabled() -> None:
    client = TestClient(app)
    resp = client.get(
        "/api/v1/public/reports",
        headers={"X-Api-Key": "dev-openclaw-key"},
    )
    assert resp.status_code == 401


def test_legacy_global_api_key_works_when_enabled(monkeypatch) -> None:
    monkeypatch.setattr("app.core.config.settings.legacy_api_key_enabled", True)
    client = TestClient(app)
    resp = client.get(
        "/api/v1/public/reports",
        headers={"X-Api-Key": "dev-openclaw-key"},
    )
    assert resp.status_code in {200, 503}


def test_auth_register_validation() -> None:
    client = TestClient(app)
    resp = client.post(
        "/api/v1/public/auth/register",
        json={"email": "bad", "username": "x", "password": "short"},
    )
    assert resp.status_code in {422, 503}


def test_auth_login_invalid_credentials(require_db: None) -> None:
    client = TestClient(app)
    resp = client.post(
        "/api/v1/public/auth/login",
        json={"email": "nobody@example.com", "password": "wrongpass1"},
    )
    assert resp.status_code == 401


def test_auth_login_accepts_localhost_bootstrap_email(require_db: None, admin_user: AuthTestUser) -> None:
    client = TestClient(app)
    resp = client.post(
        "/api/v1/public/auth/login",
        json={"email": admin_user.email, "password": admin_user.password},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["user"]["role"] == "ADMIN"


def test_auth_register_new_user(require_db: None) -> None:
    suffix = uuid.uuid4().hex[:8]
    client = TestClient(app)
    resp = client.post(
        "/api/v1/public/auth/register",
        json={
            "email": f"register-{suffix}@example.com",
            "username": f"reg_{suffix}",
            "password": "Register1",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["user"]["role"] == "USER"
    assert resp.json()["access_token"]


def test_auth_me_requires_credentials() -> None:
    client = TestClient(app)
    assert client.get("/api/v1/public/auth/me").status_code == 401


def test_auth_logout_clears_session(admin_user: AuthTestUser) -> None:
    client = login_client(admin_user)
    assert client.delete("/api/v1/public/auth/logout").status_code == 200
    assert client.get("/api/v1/public/auth/me").status_code == 401


def test_auth_refresh_rotates_access(admin_user: AuthTestUser) -> None:
    client = login_client(admin_user)
    refresh = client.post("/api/v1/public/auth/refresh")
    assert refresh.status_code == 200
    assert refresh.json()["access_token"]


def test_auth_register_duplicate_email(user_a: AuthTestUser) -> None:
    client = TestClient(app)
    resp = client.post(
        "/api/v1/public/auth/register",
        json={"email": user_a.email, "username": "other_user", "password": "OtherPass1"},
    )
    assert resp.status_code == 409
