import pytest
from fastapi.testclient import TestClient

from app.core.startup_checks import validate_security_config
from app.main import app


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
    monkeypatch.setattr("app.core.config.settings.openclaw_enable_signature", True)
    monkeypatch.setattr("app.core.config.settings.portal_embed_api_key_in_spa", False)


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
