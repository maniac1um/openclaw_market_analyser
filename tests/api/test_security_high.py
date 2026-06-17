import pytest
from fastapi.testclient import TestClient

from app.core.startup_checks import validate_security_config
from app.main import app
from app.schemas.report import OpenClawReportIn
from tests.api.conftest import AuthTestUser, cookie_write_headers, login_client


def _auth_headers(api_key: str) -> dict[str, str]:
    return {"X-Api-Key": api_key, "X-Request-Id": "req-h1"}


def _base_payload() -> dict:
    return {
        "task_id": "task-h1",
        "keyword": "羽毛球",
        "time_range": {
            "start": "2026-03-01T00:00:00+00:00",
            "end": "2026-04-01T00:00:00+00:00",
        },
        "sources": ["source-a"],
        "items": [
            {
                "title": "x",
                "source": "source-a",
                "url": "https://example.com/1",
                "published_at": "2026-03-20T10:00:00+00:00",
            }
        ],
        "analysis": "ok",
        "generated_title": "t",
        "generated_at": "2026-04-01T11:00:00+00:00",
    }


def test_production_fail_fast_weak_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.config.settings.production_mode", True)
    monkeypatch.setattr("app.core.config.settings.openclaw_api_key", "dev-openclaw-key")
    with pytest.raises(RuntimeError, match="OPENCLAW_OPENCLAW_API_KEY"):
        validate_security_config()


def test_oversized_analysis_rejected_by_schema() -> None:
    data = _base_payload()
    data["analysis"] = "A" * 60_000
    with pytest.raises(Exception):
        OpenClawReportIn.model_validate(data)


def test_javascript_url_rejected_by_schema() -> None:
    data = _base_payload()
    data["items"][0]["url"] = "javascript:alert(1)"
    with pytest.raises(Exception):
        OpenClawReportIn.model_validate(data)


def test_bulk_delete_invalid_uuid_returns_422(api_headers: dict[str, str]) -> None:
    client = TestClient(app)
    client.post("/api/v1/public/auth/session", headers=api_headers)
    resp = client.post(
        "/api/v1/public/reports/bulk-delete",
        json={"ingest_ids": ["../../../etc/passwd"]},
    )
    assert resp.status_code == 422


def test_healthz_db_hides_exception_detail_by_default() -> None:
    client = TestClient(app)
    resp = client.get("/healthz/db")
    assert resp.status_code == 200
    body = resp.json()
    if not body.get("ok"):
        assert body.get("detail") == "database connection failed"


def test_rate_limit_returns_429(monkeypatch: pytest.MonkeyPatch, api_headers: dict[str, str]) -> None:
    monkeypatch.setattr("app.core.config.settings.rate_limit_enabled", True)
    monkeypatch.setattr("app.core.config.settings.rate_limit_read_per_minute", 3)
    client = TestClient(app)
    for _ in range(3):
        assert client.get("/api/v1/public/reports", headers=api_headers).status_code in {200, 503}
    assert client.get("/api/v1/public/reports", headers=api_headers).status_code == 429


def test_ssrf_guard_blocks_localhost() -> None:
    from app.utils.ssrf_guard import validate_outbound_http_url

    with pytest.raises(ValueError):
        validate_outbound_http_url("http://127.0.0.1/admin")


def test_ssrf_guard_blocks_unresolvable_host() -> None:
    from app.utils.ssrf_guard import validate_outbound_http_url

    with pytest.raises(ValueError):
        validate_outbound_http_url("http://this-host-does-not-exist-7f3a9b.example.invalid/")


def test_payment_tokens_capped_at_simulated_recharge_amount() -> None:
    from app.schemas.billing import PaymentCreateRequest

    cap = 1000
    assert PaymentCreateRequest(tokens=cap).tokens == cap
    with pytest.raises(Exception):
        PaymentCreateRequest(tokens=cap + 1)


def test_require_uuid_rejects_sqli_payload() -> None:
    from app.utils.path_safety import require_uuid

    with pytest.raises(ValueError, match="invalid payment_id UUID"):
        require_uuid("1' OR '1'='1", "payment_id")


def test_production_fail_fast_simulated_payment_confirm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.config.settings.production_mode", True)
    monkeypatch.setattr("app.core.config.settings.openclaw_api_key", "x" * 16)
    monkeypatch.setattr("app.core.config.settings.openclaw_hmac_secret", "y" * 16)
    monkeypatch.setattr("app.core.config.settings.jwt_secret", "z" * 32)
    monkeypatch.setattr("app.core.config.settings.cookie_secure", True)
    monkeypatch.setattr("app.core.config.settings.database_url", "postgresql://u:p@localhost/db")
    monkeypatch.setattr("app.core.config.settings.openclaw_enable_signature", True)
    monkeypatch.setattr("app.core.config.settings.git_auto_push", False)
    monkeypatch.setattr("app.core.config.settings.portal_embed_api_key_in_spa", False)
    monkeypatch.setattr("app.core.config.settings.expose_openapi", False)
    monkeypatch.setattr("app.core.config.settings.legacy_api_key_enabled", False)
    monkeypatch.setattr("app.core.config.settings.allow_registration", False)
    monkeypatch.setattr("app.core.config.settings.first_user_is_admin", False)
    monkeypatch.setattr("app.core.config.settings.demo_seed_enabled", False)
    monkeypatch.setattr("app.core.config.settings.payments_simulated_confirm_enabled", True)
    monkeypatch.setattr("app.core.config.settings.subscriptions_simulated_upgrade_enabled", False)
    monkeypatch.setattr("app.core.config.settings.admin_cross_tenant_access", False)
    monkeypatch.setattr("app.core.config.settings.monitoring_allow_server_scrape", False)
    monkeypatch.setattr(
        "app.db.user_queries.bootstrap_admin_uses_default_password",
        lambda: False,
    )
    with pytest.raises(RuntimeError, match="PAYMENTS_SIMULATED_CONFIRM"):
        validate_security_config()


def test_production_fail_fast_admin_cross_tenant(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.config.settings.production_mode", True)
    monkeypatch.setattr("app.core.config.settings.openclaw_api_key", "x" * 16)
    monkeypatch.setattr("app.core.config.settings.openclaw_hmac_secret", "y" * 16)
    monkeypatch.setattr("app.core.config.settings.jwt_secret", "z" * 32)
    monkeypatch.setattr("app.core.config.settings.cookie_secure", True)
    monkeypatch.setattr("app.core.config.settings.database_url", "postgresql://u:p@localhost/db")
    monkeypatch.setattr("app.core.config.settings.openclaw_enable_signature", True)
    monkeypatch.setattr("app.core.config.settings.git_auto_push", False)
    monkeypatch.setattr("app.core.config.settings.portal_embed_api_key_in_spa", False)
    monkeypatch.setattr("app.core.config.settings.expose_openapi", False)
    monkeypatch.setattr("app.core.config.settings.legacy_api_key_enabled", False)
    monkeypatch.setattr("app.core.config.settings.allow_registration", False)
    monkeypatch.setattr("app.core.config.settings.first_user_is_admin", False)
    monkeypatch.setattr("app.core.config.settings.demo_seed_enabled", False)
    monkeypatch.setattr("app.core.config.settings.payments_simulated_confirm_enabled", False)
    monkeypatch.setattr("app.core.config.settings.subscriptions_simulated_upgrade_enabled", False)
    monkeypatch.setattr("app.core.config.settings.admin_cross_tenant_access", True)
    monkeypatch.setattr("app.core.config.settings.monitoring_allow_server_scrape", False)
    monkeypatch.setattr(
        "app.db.user_queries.bootstrap_admin_uses_default_password",
        lambda: False,
    )
    with pytest.raises(RuntimeError, match="ADMIN_CROSS_TENANT"):
        validate_security_config()


def test_persistent_dev_deployment_rejects_weak_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.config.settings.production_mode", False)
    monkeypatch.setattr("app.core.config.settings.database_url", "postgresql://u:p@localhost/db")
    monkeypatch.setattr("app.core.config.settings.allow_insecure_dev_deployment", False)
    monkeypatch.setattr("app.core.config.settings.openclaw_api_key", "dev-openclaw-key")
    with pytest.raises(RuntimeError, match="ALLOW_INSECURE_DEV_DEPLOYMENT"):
        validate_security_config()


def test_production_fail_fast_simulated_subscription_upgrade(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.config.settings.production_mode", True)
    monkeypatch.setattr("app.core.config.settings.openclaw_api_key", "x" * 16)
    monkeypatch.setattr("app.core.config.settings.openclaw_hmac_secret", "y" * 16)
    monkeypatch.setattr("app.core.config.settings.jwt_secret", "z" * 32)
    monkeypatch.setattr("app.core.config.settings.cookie_secure", True)
    monkeypatch.setattr("app.core.config.settings.database_url", "postgresql://u:p@localhost/db")
    monkeypatch.setattr("app.core.config.settings.openclaw_enable_signature", True)
    monkeypatch.setattr("app.core.config.settings.git_auto_push", False)
    monkeypatch.setattr("app.core.config.settings.portal_embed_api_key_in_spa", False)
    monkeypatch.setattr("app.core.config.settings.expose_openapi", False)
    monkeypatch.setattr("app.core.config.settings.legacy_api_key_enabled", False)
    monkeypatch.setattr("app.core.config.settings.allow_registration", False)
    monkeypatch.setattr("app.core.config.settings.first_user_is_admin", False)
    monkeypatch.setattr("app.core.config.settings.demo_seed_enabled", False)
    monkeypatch.setattr("app.core.config.settings.payments_simulated_confirm_enabled", False)
    monkeypatch.setattr("app.core.config.settings.subscriptions_simulated_upgrade_enabled", True)
    monkeypatch.setattr("app.core.config.settings.admin_cross_tenant_access", False)
    monkeypatch.setattr("app.core.config.settings.monitoring_allow_server_scrape", False)
    monkeypatch.setattr(
        "app.db.user_queries.bootstrap_admin_uses_default_password",
        lambda: False,
    )
    with pytest.raises(RuntimeError, match="SUBSCRIPTIONS_SIMULATED_UPGRADE"):
        validate_security_config()


def test_refresh_requires_csrf_token(admin_user: AuthTestUser) -> None:
    client = login_client(admin_user)
    denied = client.post("/api/v1/public/auth/refresh")
    assert denied.status_code == 403
    allowed = client.post(
        "/api/v1/public/auth/refresh",
        headers=cookie_write_headers(client),
    )
    assert allowed.status_code == 200
