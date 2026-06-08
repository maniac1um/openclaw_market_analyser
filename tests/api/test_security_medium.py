import pytest
from fastapi.testclient import TestClient

from app.core.startup_checks import validate_security_config
from app.main import app


from tests.api.conftest import cookie_write_headers


def test_openapi_hidden_by_default() -> None:
    client = TestClient(app)
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_workflow_diagnostics_requires_auth(api_headers: dict[str, str]) -> None:
    client = TestClient(app)
    assert client.get("/api/v1/public/workflow/diagnostics").status_code == 401
    client.post("/api/v1/public/auth/session", headers=api_headers)
    assert client.get("/api/v1/public/workflow/diagnostics").status_code == 200


def test_workflow_gateway_status_requires_auth(api_headers: dict[str, str]) -> None:
    client = TestClient(app)
    assert client.get("/api/v1/public/workflow/gateway-status").status_code == 401
    client.post("/api/v1/public/auth/session", headers=api_headers)
    assert client.get("/api/v1/public/workflow/gateway-status").status_code == 200


def test_workflow_run_readiness_requires_auth(api_headers: dict[str, str]) -> None:
    client = TestClient(app)
    assert client.get("/api/v1/public/workflow/run-readiness").status_code == 401
    client.post("/api/v1/public/auth/session", headers=api_headers)
    assert client.get("/api/v1/public/workflow/run-readiness").status_code == 200


def test_report_detail_invalid_uuid_returns_422(api_headers: dict[str, str]) -> None:
    client = TestClient(app)
    resp = client.get("/api/v1/public/reports/not-a-uuid", headers=api_headers)
    assert resp.status_code == 422


def _production_base(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.config.settings.production_mode", True)
    monkeypatch.setattr("app.core.config.settings.openclaw_api_key", "x" * 40)
    monkeypatch.setattr("app.core.config.settings.openclaw_hmac_secret", "y" * 40)
    monkeypatch.setattr("app.core.config.settings.jwt_secret", "z" * 40)
    monkeypatch.setattr("app.core.config.settings.cookie_secure", True)
    monkeypatch.setattr("app.core.config.settings.database_url", "postgresql://app:strongpass@db.example/app")
    monkeypatch.setattr("app.core.config.settings.monitoring_database_url", "postgresql://mon:strongpass@db.example/mon")
    monkeypatch.setattr("app.core.config.settings.news_database_url", "postgresql://news:strongpass@db.example/news")
    monkeypatch.setattr("app.core.config.settings.openclaw_enable_signature", True)
    monkeypatch.setattr("app.core.config.settings.portal_embed_api_key_in_spa", False)
    monkeypatch.setattr("app.core.config.settings.legacy_api_key_enabled", False)
    monkeypatch.setattr("app.core.config.settings.allow_registration", False)
    monkeypatch.setattr("app.core.config.settings.first_user_is_admin", False)
    monkeypatch.setattr("app.core.config.settings.demo_seed_enabled", False)
    monkeypatch.setattr("app.db.user_queries.bootstrap_admin_uses_default_password", lambda: False)


def test_production_blocks_git_auto_push(monkeypatch: pytest.MonkeyPatch) -> None:
    _production_base(monkeypatch)
    monkeypatch.setattr("app.core.config.settings.git_auto_push", True)
    monkeypatch.setattr("app.core.config.settings.expose_openapi", False)
    with pytest.raises(RuntimeError, match="GIT_AUTO_PUSH"):
        validate_security_config()


def test_production_blocks_expose_openapi(monkeypatch: pytest.MonkeyPatch) -> None:
    _production_base(monkeypatch)
    monkeypatch.setattr("app.core.config.settings.git_auto_push", False)
    monkeypatch.setattr("app.core.config.settings.expose_openapi", True)
    with pytest.raises(RuntimeError, match="EXPOSE_OPENAPI"):
        validate_security_config()


def test_production_blocks_weak_jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    _production_base(monkeypatch)
    monkeypatch.setattr("app.core.config.settings.jwt_secret", "dev-jwt-secret-change-me-in-production")
    monkeypatch.setattr("app.core.config.settings.git_auto_push", False)
    monkeypatch.setattr("app.core.config.settings.expose_openapi", False)
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        validate_security_config()


def test_production_blocks_insecure_cookie(monkeypatch: pytest.MonkeyPatch) -> None:
    _production_base(monkeypatch)
    monkeypatch.setattr("app.core.config.settings.cookie_secure", False)
    monkeypatch.setattr("app.core.config.settings.git_auto_push", False)
    monkeypatch.setattr("app.core.config.settings.expose_openapi", False)
    with pytest.raises(RuntimeError, match="COOKIE_SECURE"):
        validate_security_config()


def test_production_blocks_open_registration(monkeypatch: pytest.MonkeyPatch) -> None:
    _production_base(monkeypatch)
    monkeypatch.setattr("app.core.config.settings.allow_registration", True)
    monkeypatch.setattr("app.core.config.settings.git_auto_push", False)
    monkeypatch.setattr("app.core.config.settings.expose_openapi", False)
    with pytest.raises(RuntimeError, match="ALLOW_REGISTRATION"):
        validate_security_config()


def test_production_blocks_weak_db_dsn(monkeypatch: pytest.MonkeyPatch) -> None:
    _production_base(monkeypatch)
    monkeypatch.setattr("app.core.config.settings.database_url", "postgresql://openclaw_app:openclaw_dev@postgres/app")
    monkeypatch.setattr("app.core.config.settings.git_auto_push", False)
    monkeypatch.setattr("app.core.config.settings.expose_openapi", False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        validate_security_config()


def test_api_key_hash_uses_hmac_prefix() -> None:
    from app.db import user_queries as uq

    digest = uq.hash_api_key("oc_test_key_value")
    assert digest.startswith("hmac:")
    assert digest != uq.legacy_hash_api_key("oc_test_key_value")


def test_gateway_status_sanitizes_exception_detail(monkeypatch: pytest.MonkeyPatch, api_headers: dict[str, str]) -> None:
    async def boom(*_args, **_kwargs):
        raise ConnectionError("secret internal host:18789 refused")

    monkeypatch.setattr("app.db.public_queries.probe_openclaw_gateway", boom)
    client = TestClient(app)
    client.post("/api/v1/public/auth/session", headers=api_headers)
    resp = client.get("/api/v1/public/workflow/gateway-status")
    assert resp.status_code == 200
    body = resp.json()
    assert "secret internal" not in body.get("detail", "")
    assert body.get("ws_url") in {"", "configured"}


def test_ws_user_message_rate_limit(monkeypatch: pytest.MonkeyPatch, api_headers: dict[str, str]) -> None:
    monkeypatch.setattr("app.core.config.settings.ws_messages_per_minute", 2)
    client = TestClient(app)
    with client.websocket_connect(
        "/api/v1/chat/ws",
        headers={"x-api-key": api_headers["X-Api-Key"]},
    ) as ws:
        for _ in range(2):
            ws.send_json({"type": "user_message", "sessionKey": "s1", "text": ""})
            msg = ws.receive_json()
            assert msg["type"] == "assistant_error"
        ws.send_json({"type": "user_message", "sessionKey": "s1", "text": ""})
        msg = ws.receive_json()
        assert msg["type"] == "assistant_error"
        assert "Rate limit" in msg.get("error", "")
