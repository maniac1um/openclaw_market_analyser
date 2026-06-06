"""Gateway proxy security: role isolation, permission checks, audit."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db import audit_queries as audit_q
from app.db.user_models import User
from app.main import app
from app.services.gateway_permission_checker import (
    assert_chat_allowed,
    build_gateway_message,
)
from app.services.openclaw_chat_bridge import (
    build_gateway_session_key,
    resolve_gateway_connect_context,
)
def _now() -> datetime:
    return datetime.now(timezone.utc)


def _user(*, user_id: str | None = None, role: str = "USER") -> User:
    uid = user_id or str(uuid.uuid4())
    return User(
        id=uid,
        email=f"{uid[:8]}@example.com",
        username=f"user_{uid[:8]}",
        role=role,
        status="active",
        created_at=_now(),
        updated_at=_now(),
    )


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _session_key() -> str:
    return str(uuid.uuid4())


def test_build_gateway_session_key_namespaces_by_agent_and_user() -> None:
    key = build_gateway_session_key(
        agent_id="portal-readonly",
        portal_user_id="11111111-1111-1111-1111-111111111111",
        client_session_key="22222222-2222-2222-2222-222222222222",
    )
    assert key.startswith("portal-readonly:11111111-1111-1111-1111-111111111111:")


def test_user_permission_blocks_shell_commands() -> None:
    user = _user(role="USER")
    decision = assert_chat_allowed(
        user,
        "cat /etc/passwd",
        chat_enabled_for_user=True,
        portal_agent_id="portal-readonly",
        admin_agent_id="main",
    )
    assert not decision.allowed
    assert decision.decision == "blocked"


def test_user_permission_allows_normal_question() -> None:
    user = _user(role="USER")
    decision = assert_chat_allowed(
        user,
        "我是否是管理员？",
        chat_enabled_for_user=True,
        portal_agent_id="portal-readonly",
        admin_agent_id="main",
    )
    assert decision.allowed
    assert decision.agent_id == "portal-readonly"


def test_build_gateway_message_injects_user_role_context() -> None:
    msg = build_gateway_message(
        portal_user_id="u1",
        portal_role="USER",
        agent_id="portal-readonly",
        user_text="你好",
    )
    assert "role=USER" in msg
    assert "portal-readonly" in msg
    assert "不是 Gateway 管理员" in msg
    assert "用户消息：你好" in msg


def test_resolve_gateway_connect_context_uses_portal_agent_for_user() -> None:
    ctx = resolve_gateway_connect_context(
        portal_user_id="11111111-1111-1111-1111-111111111111",
        portal_role="USER",
    )
    assert ctx.agent_id == settings.gateway_portal_agent_id


def test_resolve_gateway_connect_context_uses_admin_agent_for_admin() -> None:
    ctx = resolve_gateway_connect_context(
        portal_user_id="11111111-1111-1111-1111-111111111111",
        portal_role="ADMIN",
    )
    assert ctx.agent_id == settings.gateway_admin_agent_id


@patch("app.api.v1.chat.resolve_websocket_user")
def test_chat_ws_rejects_invalid_session_key(mock_ws_user, client: TestClient) -> None:
    mock_ws_user.return_value = _user()
    with client.websocket_connect("/api/v1/chat/ws") as ws:
        ws.send_json({"type": "user_message", "sessionKey": "not-a-uuid", "text": "hello"})
        msg = ws.receive_json()
        assert msg["type"] == "assistant_error"
        assert "Invalid" in msg.get("error", "")


@patch("app.api.v1.chat.resolve_websocket_user")
def test_chat_ws_blocks_user_dangerous_command(mock_ws_user, client: TestClient) -> None:
    portal_user = _user()
    mock_ws_user.return_value = portal_user
    sk = _session_key()
    with client.websocket_connect("/api/v1/chat/ws") as ws:
        ws.send_json({"type": "user_message", "sessionKey": sk, "text": "cat /etc/passwd"})
        msg = ws.receive_json()
        assert msg["type"] == "assistant_error"
        assert "只读" in msg.get("error", "") or "文件" in msg.get("error", "")


@patch("app.api.v1.chat.stream_openclaw_reply", new_callable=AsyncMock)
@patch("app.api.v1.chat.probe_openclaw_gateway", new_callable=AsyncMock)
@patch("app.api.v1.chat.resolve_websocket_user")
def test_user_chat_uses_portal_agent_and_context(
    mock_ws_user: AsyncMock,
    mock_probe: AsyncMock,
    mock_stream: AsyncMock,
    client: TestClient,
) -> None:
    portal_user = _user()
    mock_ws_user.return_value = portal_user
    mock_probe.return_value = {"ok": True}
    mock_stream.return_value = {
        "agent_id": "portal-readonly",
        "gateway_device_role": "operator",
        "latency_ms": 10,
    }

    sk = _session_key()
    with client.websocket_connect("/api/v1/chat/ws") as ws:
        ws.send_json({"type": "user_message", "sessionKey": sk, "text": "羽毛球价格趋势"})
        ws.receive_json()
        import time

        for _ in range(50):
            time.sleep(0.05)
            if mock_stream.called:
                break

    assert mock_stream.called
    call_kwargs = mock_stream.call_args.kwargs
    assert call_kwargs["connect_ctx"].agent_id == settings.gateway_portal_agent_id
    assert "portal-readonly" in call_kwargs["session_key"]
    assert portal_user.id in call_kwargs["session_key"]
    assert "role=USER" in call_kwargs["user_text"]


def test_production_requires_portal_state_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "production_mode", True)
    monkeypatch.setattr(settings, "openclaw_api_key", "a" * 20)
    monkeypatch.setattr(settings, "openclaw_hmac_secret", "b" * 20)
    monkeypatch.setattr(settings, "openclaw_enable_signature", True)
    monkeypatch.setattr(settings, "git_auto_push", False)
    monkeypatch.setattr(settings, "portal_embed_api_key_in_spa", False)
    monkeypatch.setattr(settings, "expose_openapi", False)
    monkeypatch.setattr(settings, "chat_enabled_for_user", True)
    monkeypatch.setattr(settings, "gateway_portal_state_dir", None)

    from app.core.startup_checks import validate_security_config

    with pytest.raises(RuntimeError, match="OPENCLAW_GATEWAY_PORTAL_STATE_DIR"):
        validate_security_config()


@patch("app.api.v1.chat.resolve_websocket_user")
def test_chat_disabled_for_user_when_flag_off(
    mock_ws_user,
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_ws_user.return_value = _user(role="USER")
    monkeypatch.setattr(settings, "chat_enabled_for_user", False)
    sk = _session_key()
    with client.websocket_connect("/api/v1/chat/ws") as ws:
        ws.send_json({"type": "user_message", "sessionKey": sk, "text": "hello"})
        msg = ws.receive_json()
        assert msg["type"] == "assistant_error"
        assert "管理员" in msg.get("error", "")


def test_gateway_audit_api_admin_only(client: TestClient) -> None:
    from app.core.security import get_current_user

    user = _user(role="USER")
    admin = _user(role="ADMIN")

    app.dependency_overrides[get_current_user] = lambda: user
    try:
        resp_user = client.get("/api/v1/public/audit/gateway-events")
        assert resp_user.status_code == 403
    finally:
        app.dependency_overrides.clear()

    app.dependency_overrides[get_current_user] = lambda: admin
    try:
        with patch("app.api.v1.public.audit_q.list_gateway_audit_events", return_value=[]):
            resp_admin = client.get("/api/v1/public/audit/gateway-events")
        assert resp_admin.status_code == 200
        assert "events" in resp_admin.json()
    finally:
        app.dependency_overrides.clear()


@patch("app.db.audit_queries.insert_gateway_audit_event")
def test_gateway_audit_service_logs_blocked(mock_insert) -> None:
    from app.services.gateway_audit_service import log_gateway_event

    log_gateway_event(
        user_id=str(uuid.uuid4()),
        user_role="USER",
        session_key=str(uuid.uuid4()),
        action="chat.blocked",
        message="cat /etc/passwd",
        decision="blocked",
        agent_id="portal-readonly",
        gateway_device_role="portal",
        error_redacted="文件读取命令",
    )
    mock_insert.assert_called_once()
    assert mock_insert.call_args.kwargs["decision"] == "blocked"
