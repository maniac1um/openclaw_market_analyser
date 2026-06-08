import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status

from app.core.auth_service import REFRESH_COOKIE
from app.core.config import settings
from app.core.rate_limit import allow as rate_limit_allow
from app.core.security import (
    PORTAL_SESSION_COOKIE,
    CurrentUser,
    resolve_websocket_user,
)
from app.db.query_context import ADMIN_ROLE
from app.services.chat_run_store import ChatRunStatus, chat_run_store
from app.services.gateway_audit_service import log_gateway_event
from app.services.gateway_permission_checker import (
    assert_chat_allowed,
    build_gateway_message,
)
from app.services.openclaw_chat_bridge import (
    ChatCancelledError,
    GatewayConnectContext,
    OpenClawChatTimeoutError,
    build_gateway_session_key,
    probe_openclaw_gateway,
    resolve_gateway_connect_context,
    stream_openclaw_reply,
)
from app.utils.path_safety import parse_uuid
from app.utils.public_errors import sanitize_client_error, sanitize_gateway_probe_detail

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["OpenClaw 对话"],
)

_CANCEL_SUFFIX = "\n\n---\n\n（已停止生成）"
_TIMEOUT_SUFFIX = "\n\n---\n\n（响应超时，可点击「停止」后重试或缩短问题）"

_user_rate_lock = asyncio.Lock()


def _run_to_payload(record) -> dict[str, Any]:
    return {
        "sessionKey": record.session_key,
        "text": record.text,
        "done": record.done,
        "status": record.status,
        "error": record.error,
        "updatedAt": record.updated_at,
    }


def _append_status_suffix(text: str, suffix: str) -> str:
    body = (text or "").rstrip()
    if not body:
        return suffix.strip()
    return body + suffix


def _validate_client_session_key(session_key: str) -> bool:
    """Client session keys must be UUIDs to prevent agent namespace injection."""
    return parse_uuid(session_key) is not None


async def _check_user_rate_limit(user_id: str) -> bool:
    limit = max(1, int(settings.chat_user_messages_per_minute))
    bucket = f"chat-user:{user_id}"
    async with _user_rate_lock:
        return rate_limit_allow(bucket, limit=limit)


async def _safe_send_json(
    websocket: WebSocket,
    payload: dict[str, Any],
    *,
    send_lock: asyncio.Lock,
) -> bool:
    async with send_lock:
        try:
            await websocket.send_json(payload)
            return True
        except Exception:  # noqa: BLE001
            return False


async def _execute_chat_turn(
    *,
    owner_user_id: str,
    portal_role: str,
    client_session_key: str,
    user_text: str,
    connect_ctx: GatewayConnectContext,
    cancel_event: asyncio.Event,
    turn_generation: int,
    publish: Callable[[dict[str, Any]], Awaitable[None]],
    audit_decision: str,
) -> None:
    gateway_session_key = build_gateway_session_key(
        agent_id=connect_ctx.agent_id,
        portal_user_id=owner_user_id,
        client_session_key=client_session_key,
    )
    gateway_message = build_gateway_message(
        portal_user_id=owner_user_id,
        portal_role=portal_role,
        agent_id=connect_ctx.agent_id,
        user_text=user_text,
    )

    await chat_run_store.update_run(
        owner_user_id=owner_user_id,
        session_key=client_session_key,
        text="",
        done=False,
        status="processing",
    )
    await publish(
        {
            "type": "assistant_delta",
            "sessionKey": client_session_key,
            "text": "",
            "done": False,
            "status": "processing",
        }
    )

    async def on_assistant_update(delta_text: str, done: bool) -> None:
        current = await chat_run_store.get_run(
            owner_user_id=owner_user_id,
            session_key=client_session_key,
        )
        if current is None or current.generation != turn_generation:
            return
        run_status: ChatRunStatus = "done" if done else "streaming"
        updated = await chat_run_store.update_run(
            owner_user_id=owner_user_id,
            session_key=client_session_key,
            text=delta_text,
            done=done,
            status=run_status,
        )
        if updated is None:
            return
        await publish(
            {
                "type": "assistant_delta",
                "sessionKey": client_session_key,
                "text": delta_text,
                "done": done,
                "status": run_status,
            }
        )

    turn_started = time.monotonic()
    try:
        probe = await probe_openclaw_gateway(
            openclaw_ws_url=settings.openclaw_ws_url,
            timeout_seconds=settings.openclaw_gateway_probe_timeout_seconds,
        )
        if not probe.get("ok"):
            detail = sanitize_gateway_probe_detail(str(probe.get("detail") or ""))
            raise RuntimeError(f"OpenClaw Gateway 当前不可用，请稍后重试。 detail={detail}")

        meta = await stream_openclaw_reply(
            openclaw_ws_url=settings.openclaw_ws_url,
            user_text=gateway_message,
            session_key=gateway_session_key,
            connect_ctx=connect_ctx,
            on_assistant_update=on_assistant_update,
            recv_timeout_seconds=settings.openclaw_chat_recv_timeout_seconds,
            total_timeout_seconds=settings.openclaw_chat_total_timeout_seconds,
            cancel_event=cancel_event,
        )
        current = await chat_run_store.get_run(
            owner_user_id=owner_user_id,
            session_key=client_session_key,
        )
        if current is None or current.generation != turn_generation:
            return
        latency_ms = int((time.monotonic() - turn_started) * 1000)
        log_gateway_event(
            user_id=owner_user_id,
            user_role=portal_role,
            session_key=client_session_key,
            action="chat.send",
            message=user_text,
            decision=audit_decision,
            agent_id=meta.get("agent_id"),
            gateway_device_role=meta.get("gateway_device_role"),
            latency_ms=latency_ms,
        )
    except ChatCancelledError as exc:
        current = await chat_run_store.get_run(
            owner_user_id=owner_user_id,
            session_key=client_session_key,
        )
        if current is None or current.generation != turn_generation:
            return
        final_text = _append_status_suffix(exc.partial_text, _CANCEL_SUFFIX)
        await chat_run_store.update_run(
            owner_user_id=owner_user_id,
            session_key=client_session_key,
            text=final_text,
            done=True,
            status="cancelled",
        )
        await publish(
            {
                "type": "assistant_delta",
                "sessionKey": client_session_key,
                "text": final_text,
                "done": True,
                "status": "cancelled",
            }
        )
        log_gateway_event(
            user_id=owner_user_id,
            user_role=portal_role,
            session_key=client_session_key,
            action="chat.cancelled",
            message=user_text,
            decision=audit_decision,
            agent_id=connect_ctx.agent_id,
            gateway_device_role=connect_ctx.portal_role,
            latency_ms=int((time.monotonic() - turn_started) * 1000),
        )
    except OpenClawChatTimeoutError as exc:
        current = await chat_run_store.get_run(
            owner_user_id=owner_user_id,
            session_key=client_session_key,
        )
        if current is None or current.generation != turn_generation:
            return
        final_text = _append_status_suffix(exc.partial_text, _TIMEOUT_SUFFIX)
        await chat_run_store.update_run(
            owner_user_id=owner_user_id,
            session_key=client_session_key,
            text=final_text,
            done=True,
            status="timeout",
        )
        await publish(
            {
                "type": "assistant_delta",
                "sessionKey": client_session_key,
                "text": final_text,
                "done": True,
                "status": "timeout",
            }
        )
        log_gateway_event(
            user_id=owner_user_id,
            user_role=portal_role,
            session_key=client_session_key,
            action="chat.timeout",
            message=user_text,
            decision=audit_decision,
            agent_id=connect_ctx.agent_id,
            error_redacted="timeout",
            latency_ms=int((time.monotonic() - turn_started) * 1000),
        )
    except Exception as exc:
        current = await chat_run_store.get_run(
            owner_user_id=owner_user_id,
            session_key=client_session_key,
        )
        if current is None or current.generation != turn_generation:
            return
        error = sanitize_client_error(exc)
        await chat_run_store.update_run(
            owner_user_id=owner_user_id,
            session_key=client_session_key,
            text="",
            done=True,
            status="error",
            error=error,
        )
        await publish(
            {
                "type": "assistant_error",
                "sessionKey": client_session_key,
                "error": error,
            }
        )
        log_gateway_event(
            user_id=owner_user_id,
            user_role=portal_role,
            session_key=client_session_key,
            action="chat.error",
            message=user_text,
            decision=audit_decision,
            agent_id=connect_ctx.agent_id,
            error_redacted=error[:200],
            latency_ms=int((time.monotonic() - turn_started) * 1000),
        )


@router.get("/runs/active")
async def list_active_chat_runs(user: CurrentUser) -> dict[str, Any]:
    records = await chat_run_store.list_active_for_user(str(user.id))
    return {"runs": [_run_to_payload(record) for record in records]}


@router.get("/runs/{session_key}")
async def get_chat_run(session_key: str, user: CurrentUser) -> dict[str, Any]:
    record = await chat_run_store.get_run(owner_user_id=str(user.id), session_key=session_key)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat run not found")
    return _run_to_payload(record)


@router.websocket("/ws")
async def chat_ws(websocket: WebSocket) -> None:
    if settings.production_mode and websocket.query_params.get("token"):
        await websocket.close(code=1008, reason="Unauthorized")
        return
    bearer = None if settings.production_mode else websocket.query_params.get("token")
    ws_user = resolve_websocket_user(
        header_api_key=websocket.headers.get("x-api-key"),
        portal_cookie=websocket.cookies.get(PORTAL_SESSION_COOKIE),
        bearer_token=bearer,
        refresh_cookie=websocket.cookies.get(REFRESH_COOKIE),
    )
    if ws_user is None:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    await websocket.accept()
    owner_user_id = str(ws_user.id)
    portal_role = ws_user.role
    send_lock = asyncio.Lock()
    connection_bucket = f"ws-conn:{owner_user_id}:{id(websocket)}"
    msg_limit = max(1, int(settings.ws_messages_per_minute))

    async def publish(payload: dict[str, Any]) -> None:
        await _safe_send_json(websocket, payload, send_lock=send_lock)

    log_gateway_event(
        user_id=owner_user_id,
        user_role=portal_role,
        session_key=None,
        action="ws.connect",
        decision="allowed" if portal_role == ADMIN_ROLE or settings.chat_enabled_for_user else "restricted",
        agent_id=settings.resolve_gateway_agent_id(portal_role=portal_role),
    )

    try:
        while True:
            incoming = await websocket.receive_json()
            if not isinstance(incoming, dict):
                continue

            msg_type = incoming.get("type")

            if msg_type == "cancel_message":
                cancel_key = incoming.get("sessionKey")
                if isinstance(cancel_key, str) and cancel_key:
                    await chat_run_store.request_cancel(
                        owner_user_id=owner_user_id,
                        session_key=cancel_key,
                    )
                continue

            if msg_type != "user_message":
                continue

            if not rate_limit_allow(connection_bucket, limit=msg_limit):
                await publish(
                    {
                        "type": "assistant_error",
                        "sessionKey": incoming.get("sessionKey"),
                        "error": "Rate limit exceeded for chat messages.",
                    },
                )
                continue

            user_text = incoming.get("text") or ""
            session_key = incoming.get("sessionKey")
            if not isinstance(session_key, str) or not session_key or not user_text.strip():
                await publish(
                    {
                        "type": "assistant_error",
                        "sessionKey": session_key,
                        "error": "Invalid user_message payload.",
                    },
                )
                continue

            if not _validate_client_session_key(session_key):
                await publish(
                    {
                        "type": "assistant_error",
                        "sessionKey": session_key,
                        "error": "Invalid sessionKey format.",
                    },
                )
                continue

            perm = assert_chat_allowed(
                ws_user,
                user_text.strip(),
                chat_enabled_for_user=settings.chat_enabled_for_user,
                portal_agent_id=settings.gateway_portal_agent_id,
                admin_agent_id=settings.gateway_admin_agent_id,
            )
            if not perm.allowed:
                log_gateway_event(
                    user_id=owner_user_id,
                    user_role=portal_role,
                    session_key=session_key,
                    action="chat.blocked",
                    message=user_text.strip(),
                    decision=perm.decision,
                    agent_id=perm.agent_id,
                    gateway_device_role=perm.gateway_device_role,
                    error_redacted=perm.reason,
                )
                await publish(
                    {
                        "type": "assistant_error",
                        "sessionKey": session_key,
                        "error": perm.reason or "消息未通过安全校验。",
                    },
                )
                continue

            if not await _check_user_rate_limit(owner_user_id):
                await publish(
                    {
                        "type": "assistant_error",
                        "sessionKey": session_key,
                        "error": "User rate limit exceeded for chat messages.",
                    },
                )
                continue

            if await chat_run_store.is_user_busy(owner_user_id):
                await publish(
                    {
                        "type": "assistant_error",
                        "sessionKey": session_key,
                        "error": "Server busy: wait for the current reply to finish.",
                    },
                )
                continue

            try:
                record = await chat_run_store.begin_run(
                    owner_user_id=owner_user_id,
                    session_key=session_key,
                )
            except RuntimeError:
                await publish(
                    {
                        "type": "assistant_error",
                        "sessionKey": session_key,
                        "error": "Server busy: wait for the current reply to finish.",
                    },
                )
                continue

            connect_ctx = resolve_gateway_connect_context(
                portal_user_id=owner_user_id,
                portal_role=portal_role,
            )

            asyncio.create_task(
                _execute_chat_turn(
                    owner_user_id=owner_user_id,
                    portal_role=portal_role,
                    client_session_key=session_key,
                    user_text=user_text.strip(),
                    connect_ctx=connect_ctx,
                    cancel_event=record.cancel_event,
                    turn_generation=record.generation,
                    publish=publish,
                    audit_decision=perm.decision,
                ),
                name=f"chat-turn:{session_key}",
            )

    except WebSocketDisconnect:
        logger.info("chat websocket disconnected user_id=%s (background runs continue)", owner_user_id)
        return
