import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.middleware.security import BodyTooLarge, MaxBodySizeMiddleware
from app.utils.log_safety import sanitize_for_log
from app.utils.public_errors import sanitize_client_error


def test_monitoring_timeseries_invalid_uuid_returns_422(api_headers: dict[str, str]) -> None:
    client = TestClient(app)
    resp = client.get("/api/v1/public/monitoring/not-a-uuid/timeseries", headers=api_headers)
    assert resp.status_code == 422


def test_monitoring_observations_invalid_uuid_returns_422(api_headers: dict[str, str]) -> None:
    client = TestClient(app)
    resp = client.get("/api/v1/public/monitoring/not-a-uuid/observations", headers=api_headers)
    assert resp.status_code == 422


def test_content_length_over_limit_returns_413() -> None:
    from starlette.applications import Starlette
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route
    from starlette.testclient import TestClient as StarletteClient

    async def endpoint(_request):
        return PlainTextResponse("ok")

    starlette_app = Starlette(routes=[Route("/", endpoint, methods=["POST"])])
    starlette_app.add_middleware(MaxBodySizeMiddleware, max_bytes=32)
    client = StarletteClient(starlette_app)
    resp = client.post("/", content=b"x" * 64)
    assert resp.status_code == 413


def test_ws_gateway_error_is_sanitized(monkeypatch: pytest.MonkeyPatch, api_headers: dict[str, str]) -> None:
    async def fail_probe(*_args, **_kwargs):
        return {"ok": False, "detail": "secret-host:18789 connection refused"}

    monkeypatch.setattr("app.api.v1.chat.probe_openclaw_gateway", fail_probe)
    client = TestClient(app)
    with client.websocket_connect(
        "/api/v1/chat/ws",
        headers={"x-api-key": api_headers["X-Api-Key"]},
    ) as ws:
        ws.send_json({"type": "user_message", "sessionKey": "s1", "text": "hello"})
        first = ws.receive_json()
        assert first["type"] == "assistant_delta"
        msg = ws.receive_json()
        assert msg["type"] == "assistant_error"
        assert "secret-host" not in msg.get("error", "")
        assert "18789" not in msg.get("error", "")


def test_sanitize_for_log_redacts_dsn_password() -> None:
    raw = "connect failed: postgresql://openclaw_app:supersecret@127.0.0.1/db"
    assert "supersecret" not in sanitize_for_log(raw)
    assert "***@" in sanitize_for_log(raw)


def test_sanitize_client_error_hides_gateway_internals() -> None:
    msg = sanitize_client_error(RuntimeError("detail=secret-host:18789 refused"))
    assert "secret-host" not in msg
    assert "Gateway" in msg


def test_max_body_middleware_wraps_unknown_length() -> None:
    import asyncio

    from starlette.requests import Request

    async def receive():
        return {"type": "http.request", "body": b"123456789", "more_body": False}

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/",
        "headers": [],
        "query_string": b"",
        "server": ("test", 80),
        "client": ("test", 1234),
        "scheme": "http",
        "http_version": "1.1",
    }

    request = Request(scope, receive)
    wrapped_request = MaxBodySizeMiddleware._wrap_receive_with_limit(request, 8)

    async def read_body() -> None:
        with pytest.raises(BodyTooLarge):
            await wrapped_request.body()

    asyncio.run(read_body())
