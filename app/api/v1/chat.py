import asyncio
import logging
import time
from collections import deque
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status

from app.core.auth_service import REFRESH_COOKIE
from app.core.config import settings
from app.core.security import (
    PORTAL_SESSION_COOKIE,
    CurrentUser,
    resolve_websocket_user,
)
from app.services.chat_run_store import ChatRunStatus, chat_run_store
from app.services.openclaw_chat_bridge import (
    ChatCancelledError,
    OpenClawChatTimeoutError,
    probe_openclaw_gateway,
    stream_openclaw_reply,
)
from app.utils.prompt_safety import check_user_message
from app.utils.public_errors import sanitize_client_error, sanitize_gateway_probe_detail

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["OpenClaw 对话"],
)

_CANCEL_SUFFIX = "\n\n---\n\n（已停止生成）"
_TIMEOUT_SUFFIX = "\n\n---\n\n（响应超时，可点击「停止」后重试或缩短问题）"


def _append_status_suffix(text: str, suffix: str) -> str:
    body = (text or "").rstrip()
    if not body:
        return suffix.strip()
    return body + suffix


def _run_to_payload(record) -> dict[str, Any]:
    return {
        "sessionKey": record.session_key,
        "text": record.text,
        "done": record.done,
        "status": record.status,
        "error": record.error,
        "updatedAt": record.updated_at,
    }


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
    session_key: str,
    user_text: str,
    cancel_event: asyncio.Event,
    publish: Callable[[dict[str, Any]], Awaitable[None]],
) -> None:
    await chat_run_store.update_run(
        owner_user_id=owner_user_id,
        session_key=session_key,
        text="",
        done=False,
        status="processing",
    )
    await publish(
        {
            "type": "assistant_delta",
            "sessionKey": session_key,
            "text": "",
            "done": False,
            "status": "processing",
        }
    )

    async def on_assistant_update(delta_text: str, done: bool) -> None:
        run_status: ChatRunStatus = "done" if done else "streaming"
        await chat_run_store.update_run(
            owner_user_id=owner_user_id,
            session_key=session_key,
            text=delta_text,
            done=done,
            status=run_status,
        )
        await publish(
            {
                "type": "assistant_delta",
                "sessionKey": session_key,
                "text": delta_text,
                "done": done,
                "status": run_status,
            }
        )

    try:
        probe = await probe_openclaw_gateway(
            openclaw_ws_url=settings.openclaw_ws_url,
            timeout_seconds=settings.openclaw_gateway_probe_timeout_seconds,
        )
        if not probe.get("ok"):
            detail = sanitize_gateway_probe_detail(str(probe.get("detail") or ""))
            raise RuntimeError(f"OpenClaw Gateway 当前不可用，请稍后重试。 detail={detail}")
        await stream_openclaw_reply(
            openclaw_ws_url=settings.openclaw_ws_url,
            user_text=user_text,
            session_key=session_key,
            on_assistant_update=on_assistant_update,
            recv_timeout_seconds=settings.openclaw_chat_recv_timeout_seconds,
            total_timeout_seconds=settings.openclaw_chat_total_timeout_seconds,
            cancel_event=cancel_event,
        )
    except ChatCancelledError as exc:
        final_text = _append_status_suffix(exc.partial_text, _CANCEL_SUFFIX)
        await chat_run_store.update_run(
            owner_user_id=owner_user_id,
            session_key=session_key,
            text=final_text,
            done=True,
            status="cancelled",
        )
        await publish(
            {
                "type": "assistant_delta",
                "sessionKey": session_key,
                "text": final_text,
                "done": True,
                "status": "cancelled",
            }
        )
    except OpenClawChatTimeoutError as exc:
        final_text = _append_status_suffix(exc.partial_text, _TIMEOUT_SUFFIX)
        await chat_run_store.update_run(
            owner_user_id=owner_user_id,
            session_key=session_key,
            text=final_text,
            done=True,
            status="timeout",
        )
        await publish(
            {
                "type": "assistant_delta",
                "sessionKey": session_key,
                "text": final_text,
                "done": True,
                "status": "timeout",
            }
        )
    except Exception as exc:
        error = sanitize_client_error(exc)
        await chat_run_store.update_run(
            owner_user_id=owner_user_id,
            session_key=session_key,
            text="",
            done=True,
            status="error",
            error=error,
        )
        await publish(
            {
                "type": "assistant_error",
                "sessionKey": session_key,
                "error": error,
            }
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
    bearer = websocket.query_params.get("token")
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
    send_lock = asyncio.Lock()
    message_times: deque[float] = deque()
    msg_limit = max(1, int(settings.ws_messages_per_minute))

    async def publish(payload: dict[str, Any]) -> None:
        await _safe_send_json(websocket, payload, send_lock=send_lock)

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

            now = time.monotonic()
            while message_times and message_times[0] < now - 60.0:
                message_times.popleft()
            if len(message_times) >= msg_limit:
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

            if await chat_run_store.is_user_busy(owner_user_id, except_session_key=session_key):
                await publish(
                    {
                        "type": "assistant_error",
                        "sessionKey": session_key,
                        "error": "Server busy: wait for the current reply to finish.",
                    },
                )
                continue

            blocked = check_user_message(user_text)
            if blocked:
                await publish(
                    {
                        "type": "assistant_error",
                        "sessionKey": session_key,
                        "error": f"消息未发送：检测到可能有害或违规内容（{blocked}）。请修改后重试。",
                    },
                )
                continue

            message_times.append(now)
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

            asyncio.create_task(
                _execute_chat_turn(
                    owner_user_id=owner_user_id,
                    session_key=session_key,
                    user_text=user_text.strip(),
                    cancel_event=record.cancel_event,
                    publish=publish,
                ),
                name=f"chat-turn:{session_key}",
            )

    except WebSocketDisconnect:
        logger.info("chat websocket disconnected user_id=%s (background runs continue)", owner_user_id)
        return
