import time
from collections import deque
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.auth_service import REFRESH_COOKIE
from app.core.config import settings
from app.core.security import PORTAL_SESSION_COOKIE, is_websocket_authorized
from app.services.openclaw_chat_bridge import probe_openclaw_gateway, stream_openclaw_reply
from app.utils.prompt_safety import check_user_message
from app.utils.public_errors import sanitize_client_error, sanitize_gateway_probe_detail

router = APIRouter(
    prefix="/chat",
    tags=["OpenClaw 对话"],
)


async def _send_json(websocket: WebSocket, payload: dict[str, Any]) -> None:
    # FastAPI/WebSocket will serialize JSON for us if we call send_json.
    await websocket.send_json(payload)


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

    # Current implementation is sequential per WS connection:
    # the client should not send a new user_message while one is running.
    active_session_key: str | None = None
    message_times: deque[float] = deque()
    msg_limit = max(1, int(settings.ws_messages_per_minute))
    try:
        while True:
            incoming = await websocket.receive_json()
            if not isinstance(incoming, dict):
                continue

            msg_type = incoming.get("type")
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
            message_times.append(now)

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
            # Optional: send an early processing update for better UX.
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

    except WebSocketDisconnect:
        return

