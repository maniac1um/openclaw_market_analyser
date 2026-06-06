import asyncio
import time
from collections import deque
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.auth_service import REFRESH_COOKIE
from app.core.config import settings
from app.core.security import PORTAL_SESSION_COOKIE, is_websocket_authorized
from app.services.openclaw_chat_bridge import (
    ChatCancelledError,
    OpenClawChatTimeoutError,
    probe_openclaw_gateway,
    stream_openclaw_reply,
)
from app.utils.prompt_safety import check_user_message
from app.utils.public_errors import sanitize_client_error, sanitize_gateway_probe_detail

router = APIRouter(
    prefix="/chat",
    tags=["OpenClaw 对话"],
)

_CANCEL_SUFFIX = "\n\n---\n\n（已停止生成）"
_TIMEOUT_SUFFIX = "\n\n---\n\n（响应超时，可点击「停止」后重试或缩短问题）"


async def _send_json(websocket: WebSocket, payload: dict[str, Any]) -> None:
    await websocket.send_json(payload)


def _append_status_suffix(text: str, suffix: str) -> str:
    body = (text or "").rstrip()
    if not body:
        return suffix.strip()
    return body + suffix


@router.websocket("/ws")
async def chat_ws(websocket: WebSocket) -> None:
    bearer = websocket.query_params.get("token")
    if not is_websocket_authorized(
        header_api_key=websocket.headers.get("x-api-key"),
        portal_cookie=websocket.cookies.get(PORTAL_SESSION_COOKIE),
        bearer_token=bearer,
        refresh_cookie=websocket.cookies.get(REFRESH_COOKIE),
    ):
        await websocket.close(code=1008, reason="Unauthorized")
        return

    await websocket.accept()

    active_session_key: str | None = None
    active_cancel_event: asyncio.Event | None = None
    message_times: deque[float] = deque()
    msg_limit = max(1, int(settings.ws_messages_per_minute))
    try:
        while True:
            incoming = await websocket.receive_json()
            if not isinstance(incoming, dict):
                continue

            msg_type = incoming.get("type")

            if msg_type == "cancel_message":
                cancel_key = incoming.get("sessionKey")
                if (
                    active_session_key
                    and cancel_key == active_session_key
                    and active_cancel_event is not None
                ):
                    active_cancel_event.set()
                continue

            if msg_type != "user_message":
                continue

            now = time.monotonic()
            while message_times and message_times[0] < now - 60.0:
                message_times.popleft()
            if len(message_times) >= msg_limit:
                await _send_json(
                    websocket,
                    {
                        "type": "assistant_error",
                        "sessionKey": incoming.get("sessionKey"),
                        "error": "Rate limit exceeded for chat messages.",
                    },
                )
                continue

            if active_session_key is not None:
                await _send_json(
                    websocket,
                    {
                        "type": "assistant_error",
                        "sessionKey": incoming.get("sessionKey"),
                        "error": "Server busy: wait for the current reply to finish.",
                    },
                )
                continue

            user_text = incoming.get("text") or ""
            session_key = incoming.get("sessionKey")
            if not session_key or not user_text.strip():
                await _send_json(
                    websocket,
                    {
                        "type": "assistant_error",
                        "sessionKey": session_key,
                        "error": "Invalid user_message payload.",
                    },
                )
                continue

            blocked = check_user_message(user_text)
            if blocked:
                await _send_json(
                    websocket,
                    {
                        "type": "assistant_error",
                        "sessionKey": session_key,
                        "error": f"消息未发送：检测到可能有害或违规内容（{blocked}）。请修改后重试。",
                    },
                )
                continue

            active_session_key = session_key
            cancel_event = asyncio.Event()
            active_cancel_event = cancel_event

            await _send_json(
                websocket,
                {
                    "type": "assistant_delta",
                    "sessionKey": session_key,
                    "text": "",
                    "done": False,
                    "status": "processing",
                },
            )

            async def on_assistant_update(delta_text: str, done: bool) -> None:
                await _send_json(
                    websocket,
                    {
                        "type": "assistant_delta",
                        "sessionKey": session_key,
                        "text": delta_text,
                        "done": done,
                        "status": "done" if done else "streaming",
                    },
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
                await _send_json(
                    websocket,
                    {
                        "type": "assistant_delta",
                        "sessionKey": session_key,
                        "text": _append_status_suffix(exc.partial_text, _CANCEL_SUFFIX),
                        "done": True,
                        "status": "cancelled",
                    },
                )
            except OpenClawChatTimeoutError as exc:
                await _send_json(
                    websocket,
                    {
                        "type": "assistant_delta",
                        "sessionKey": session_key,
                        "text": _append_status_suffix(exc.partial_text, _TIMEOUT_SUFFIX),
                        "done": True,
                        "status": "timeout",
                    },
                )
            except Exception as exc:
                await _send_json(
                    websocket,
                    {
                        "type": "assistant_error",
                        "sessionKey": session_key,
                        "error": sanitize_client_error(exc),
                    },
                )
            finally:
                active_session_key = None
                active_cancel_event = None

    except WebSocketDisconnect:
        return
