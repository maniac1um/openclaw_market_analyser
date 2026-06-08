"""API test fixtures for multi-user PostgreSQL integration."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from app.core.auth_service import hash_password
from app.core.config import settings
from app.db import user_queries as uq
from app.db.user_queries import BOOTSTRAP_ADMIN_DEFAULT_PASSWORD
from app.main import app

ADMIN_TEST_PASSWORD = BOOTSTRAP_ADMIN_DEFAULT_PASSWORD


@dataclass
class AuthTestUser:
    user_id: str
    email: str
    username: str
    password: str
    role: str
    api_key: str


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def require_db() -> None:
    if not settings.database_url:
        pytest.skip("OPENCLAW_DATABASE_URL not configured")


def _unique_suffix() -> str:
    return uuid.uuid4().hex[:8]


def _create_test_user(*, role: str = "USER") -> AuthTestUser:
    uq.ensure_user_tables()
    suffix = _unique_suffix()
    email = f"pytest-{suffix}@example.com"
    username = f"pytest_{suffix}"
    password = "Pytest1234"
    user = uq.create_user(
        email=email,
        username=username,
        password_hash=hash_password(password),
        role=role,
    )
    raw_key, _ = uq.create_api_key(user_id=user.id, label="pytest")
    return AuthTestUser(
        user_id=user.id,
        email=email,
        username=username,
        password=password,
        role=user.role,
        api_key=raw_key,
    )


def _ensure_admin_password() -> None:
    import psycopg

    admin = uq.get_user_by_email("admin@localhost")
    if not admin:
        uq.ensure_bootstrap_admin()
        admin = uq.get_user_by_email("admin@localhost")
    assert admin is not None
    password_hash = hash_password(ADMIN_TEST_PASSWORD)
    with psycopg.connect(settings.database_url) as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE users SET password_hash = %s, updated_at = NOW() WHERE id = %s::uuid",
            (password_hash, admin.id),
        )
        conn.commit()


@pytest.fixture
def admin_user(require_db: None) -> AuthTestUser:
    uq.ensure_bootstrap_admin()
    _ensure_admin_password()
    admin = uq.get_user_by_email("admin@localhost")
    assert admin is not None
    raw_key, _ = uq.create_api_key(user_id=admin.id, label="pytest-admin")
    return AuthTestUser(
        user_id=admin.id,
        email=admin.email,
        username=admin.username,
        password=ADMIN_TEST_PASSWORD,
        role=admin.role,
        api_key=raw_key,
    )


@pytest.fixture
def user_a(require_db: None) -> AuthTestUser:
    return _create_test_user(role="USER")


@pytest.fixture
def user_b(require_db: None) -> AuthTestUser:
    return _create_test_user(role="USER")


@pytest.fixture
def api_key(admin_user: AuthTestUser) -> str:
    return admin_user.api_key


@pytest.fixture
def api_headers(admin_user: AuthTestUser) -> dict[str, str]:
    return {"X-Api-Key": admin_user.api_key}


def bearer_headers(user: AuthTestUser) -> dict[str, str]:
    return {"Authorization": f"Bearer {login_access_token(user)}"}


def api_key_headers(user: AuthTestUser) -> dict[str, str]:
    return {"X-Api-Key": user.api_key}


def cookie_write_headers(client: TestClient) -> dict[str, str]:
    """Headers for cookie-authenticated writes (includes CSRF double-submit token)."""
    csrf = client.cookies.get("openclaw_csrf")
    if csrf:
        return {"X-CSRF-Token": csrf}
    return {}


def login_access_token(user: AuthTestUser, *, client: TestClient | None = None) -> str:
    c = client or TestClient(app)
    resp = c.post(
        "/api/v1/public/auth/login",
        json={"email": user.email, "password": user.password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def login_client(user: AuthTestUser) -> TestClient:
    c = TestClient(app)
    resp = c.post(
        "/api/v1/public/auth/login",
        json={"email": user.email, "password": user.password},
    )
    assert resp.status_code == 200, resp.text
    return c


def report_ingest_ids(payload: list | dict) -> set[str]:
    if isinstance(payload, list):
        return {str(item["ingest_id"]) for item in payload}
    return {str(item["ingest_id"]) for item in payload.get("items", [])}


def minimal_report_payload(*, task_id: str, keyword: str = "pytest") -> dict:
    return {
        "task_id": task_id,
        "keyword": keyword,
        "time_range": {
            "start": "2026-03-01T00:00:00+00:00",
            "end": "2026-04-01T00:00:00+00:00",
        },
        "sources": ["source-a"],
        "items": [
            {
                "title": "pytest item",
                "source": "source-a",
                "url": "https://example.com/pytest-item",
                "published_at": "2026-03-20T10:00:00+00:00",
                "price": 88.0,
                "currency": "CNY",
                "summary": "summary",
            }
        ],
        "analysis": "analysis",
        "generated_title": "pytest report",
        "generated_at": "2026-04-01T11:00:00+00:00",
    }
