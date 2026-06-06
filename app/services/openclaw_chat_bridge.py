import asyncio
import base64
import json
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable, Optional

import websockets

from app.core.config import settings


class ChatCancelledError(Exception):
    """Raised when the browser client cancels an in-flight chat turn."""

    def __init__(self, *, partial_text: str = "") -> None:
        self.partial_text = partial_text
        super().__init__("Chat turn cancelled")


class OpenClawChatTimeoutError(Exception):
    """Raised when Gateway stops sending events before the chat turn completes."""

    def __init__(self, message: str, *, partial_text: str = "") -> None:
        self.partial_text = partial_text
        super().__init__(message)


@dataclass(frozen=True)
class GatewayConnectContext:
    """Portal-side identity injected into each Gateway chat.send turn."""

    portal_user_id: str
    portal_role: str
    agent_id: str
    state_dir: Path


def build_gateway_session_key(*, agent_id: str, portal_user_id: str, client_session_key: str) -> str:
    """Build Gateway sessionKey: agent:<agentId>:<client_uuid> (required by OpenClaw Gateway)."""
    safe_client = (client_session_key or "").strip()
    # portal_user_id retained for API stability; isolation is enforced via agent_id + device creds.
    _ = portal_user_id
    return f"agent:{agent_id}:{safe_client}"


def resolve_gateway_connect_context(*, portal_user_id: str, portal_role: str) -> GatewayConnectContext:
    agent_id = settings.resolve_gateway_agent_id(portal_role=portal_role)
    state_dir = settings.resolve_gateway_state_dir(portal_role=portal_role)
    return GatewayConnectContext(
        portal_user_id=portal_user_id,
        portal_role=portal_role,
        agent_id=agent_id,
        state_dir=state_dir,
    )


async def probe_openclaw_gateway(
    *,
    openclaw_ws_url: str,
    timeout_seconds: float = 2.0,
) -> dict:
    """Lightweight connectivity probe for OpenClaw Gateway."""
    started_at = time.monotonic()
    timeout = max(float(timeout_seconds), 0.2)
    try:
        async with websockets.connect(
            openclaw_ws_url,
            open_timeout=timeout,
            close_timeout=timeout,
            ping_interval=None,
        ) as oc_ws:
            first_raw = await asyncio.wait_for(oc_ws.recv(), timeout=timeout)
        elapsed_ms = int((time.monotonic() - started_at) * 1000)
        try:
            first = json.loads(first_raw)
        except Exception:  # noqa: BLE001
            first = {}
        if first.get("type") == "event" and first.get("event") == "connect.challenge":
            return {
                "ok": True,
                "ready": True,
                "latency_ms": elapsed_ms,
                "detail": "connect.challenge received",
            }
        return {
            "ok": False,
            "ready": False,
            "latency_ms": elapsed_ms,
            "detail": f"unexpected first event: {str(first)[:180]}",
        }
    except Exception as exc:  # noqa: BLE001
        elapsed_ms = int((time.monotonic() - started_at) * 1000)
        return {
            "ok": False,
            "ready": False,
            "latency_ms": elapsed_ms,
            "detail": f"{exc.__class__.__name__}: {exc}",
        }


def _b64url_encode(raw: bytes) -> str:
    s = base64.b64encode(raw).decode("ascii")
    s = s.replace("+", "-").replace("/", "_")
    return s.rstrip("=")


def _extract_chat_text(message: object) -> str:
    """
    Gateway `chat` events have a `payload.message` like:
      { role: "assistant", content: [ {type:"text", text:"..."}, ... ], timestamp: ... }
    """
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for part in content:
        if isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text"), str):
            parts.append(part["text"])
    return "".join(parts)


def _sign_ed25519_openssl(private_key_pem: str, payload: str) -> str:
    """
    Node side uses:
      crypto.sign(null, Buffer.from(payload,'utf8'), privateKey)
    for Ed25519 (algorithm=null => Ed25519 signs the raw message).
    """
    with tempfile.TemporaryDirectory() as td:
        priv_path = Path(td) / "priv.pem"
        msg_path = Path(td) / "payload.txt"
        priv_path.write_text(private_key_pem, encoding="utf-8")
        msg_path.write_text(payload, encoding="utf-8")
        proc = subprocess.run(
            ["openssl", "pkeyutl", "-sign", "-inkey", str(priv_path), "-rawin", "-in", str(msg_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return _b64url_encode(proc.stdout)


def _load_gateway_credentials(state_dir: Path) -> dict:
    openclaw_json_path = state_dir / "openclaw.json"
    device_auth_path = state_dir / "identity" / "device.json"
    paired_devices_path = state_dir / "devices" / "paired.json"

    openclaw_cfg = json.loads(openclaw_json_path.read_text("utf-8"))
    gateway_token = openclaw_cfg["gateway"]["auth"]["token"]

    device_auth = json.loads(device_auth_path.read_text("utf-8"))
    device_id: str = device_auth["deviceId"]
    private_key_pem: str = device_auth["privateKeyPem"]

    paired_devices = json.loads(paired_devices_path.read_text("utf-8"))
    paired_entry: Optional[dict] = paired_devices.get(device_id)
    if not paired_entry:
        raise RuntimeError(f"Missing paired device identity for deviceId={device_id}")

    return {
        "gateway_token": gateway_token,
        "device_id": device_id,
        "private_key_pem": private_key_pem,
        "client_id": paired_entry["clientId"],
        "client_mode": paired_entry["clientMode"],
        "role": paired_entry["role"],
        "scopes": paired_entry["scopes"],
        "public_key_b64url": paired_entry["publicKey"],
        "platform": paired_entry.get("platform") or "linux",
    }


async def stream_openclaw_reply(
    *,
    openclaw_ws_url: str,
    user_text: str,
    session_key: str,
    connect_ctx: GatewayConnectContext,
    on_assistant_update: Callable[[str, bool], Awaitable[None]],
    flush_interval_seconds: float = 0.2,
    recv_timeout_seconds: float = 120.0,
    total_timeout_seconds: float = 600.0,
    cancel_event: asyncio.Event | None = None,
) -> dict:
    """
    Proxy one OpenClaw Gateway chat.send run for a single portal user session.

    Uses role-specific Gateway device credentials from *connect_ctx.state_dir*
    and routes to *connect_ctx.agent_id*.

    Returns metadata dict with gateway_device_role and agent_id for audit.
    """
    creds = _load_gateway_credentials(connect_ctx.state_dir)
    gateway_token = creds["gateway_token"]
    device_id = creds["device_id"]
    private_key_pem = creds["private_key_pem"]
    client_id = creds["client_id"]
    client_mode = creds["client_mode"]
    role = creds["role"]
    scopes = creds["scopes"]
    public_key_b64url = creds["public_key_b64url"]
    platform = creds["platform"]
    device_family = ""
    agent_id = connect_ctx.agent_id

    signed_at_ms = int(time.time() * 1000)

    buffer = ""
    last_flushed_at = 0.0
    last_sent_text = None
    started_at = time.monotonic()
    recv_timeout = max(float(recv_timeout_seconds), 5.0)
    total_timeout = max(float(total_timeout_seconds), recv_timeout)
    last_event_at = started_at
    poll_seconds = 1.0

    async def _flush_if_needed(*, force: bool = False) -> None:
        nonlocal last_flushed_at, last_sent_text
        now = time.monotonic()
        if buffer and buffer != last_sent_text and (
            force or (now - last_flushed_at) >= flush_interval_seconds
        ):
            await on_assistant_update(buffer, False)
            last_flushed_at = now
            last_sent_text = buffer

    def _check_cancel_and_total_timeout() -> None:
        if cancel_event and cancel_event.is_set():
            raise ChatCancelledError(partial_text=buffer)
        if (time.monotonic() - started_at) >= total_timeout:
            raise OpenClawChatTimeoutError(
                f"OpenClaw 响应总时长超过 {int(total_timeout)} 秒。",
                partial_text=buffer,
            )

    # Gateway echoes the same sessionKey we sent (agent:<agentId>:<client_uuid>).
    def _session_key_matches(emitted: str) -> bool:
        return emitted == session_key or emitted.endswith(":" + session_key.split(":")[-1])

    display_name = (
        "openclaw-news-publisher-portal"
        if connect_ctx.portal_role != "ADMIN"
        else "openclaw-news-publisher-admin"
    )

    async with websockets.connect(openclaw_ws_url) as oc_ws:
        first_raw = await oc_ws.recv()
        first = json.loads(first_raw)
        if first.get("type") != "event" or first.get("event") != "connect.challenge":
            raise RuntimeError(f"Expected connect.challenge, got: {first}")
        connect_nonce = first["payload"]["nonce"]

        scopes_csv = ",".join(scopes)
        payload_v3 = "|".join(
            [
                "v3",
                device_id,
                client_id,
                client_mode,
                role,
                scopes_csv,
                str(signed_at_ms),
                gateway_token,
                connect_nonce,
                platform,
                device_family,
            ]
        )
        signature_b64url = _sign_ed25519_openssl(private_key_pem, payload_v3)

        connect_req = {
            "type": "req",
            "id": "c1",
            "method": "connect",
            "params": {
                "minProtocol": 4,
                "maxProtocol": 4,
                "client": {
                    "id": client_id,
                    "displayName": display_name,
                    "version": "0.1.0",
                    "platform": platform,
                    "mode": client_mode,
                },
                "role": role,
                "scopes": scopes,
                "caps": [],
                "commands": [],
                "permissions": {},
                "auth": {"token": gateway_token},
                "locale": "zh-CN",
                "userAgent": "openclaw-news-publisher/0.1",
                "device": {
                    "id": device_id,
                    "publicKey": public_key_b64url,
                    "signature": signature_b64url,
                    "signedAt": signed_at_ms,
                    "nonce": connect_nonce,
                },
            },
        }
        await oc_ws.send(json.dumps(connect_req, ensure_ascii=False))

        while True:
            res_raw = await oc_ws.recv()
            res = json.loads(res_raw)
            if res.get("type") == "res" and res.get("id") == "c1":
                if not res.get("ok"):
                    raise RuntimeError(f"OpenClaw connect failed: {res}")
                break

        chat_req_id = "chat.send:" + session_key
        idem = "idem:" + session_key + ":" + str(uuid.uuid4())
        chat_req = {
            "type": "req",
            "id": chat_req_id,
            "method": "chat.send",
            "params": {
                "sessionKey": session_key,
                "agentId": agent_id,
                "message": user_text,
                "idempotencyKey": idem,
            },
        }
        await oc_ws.send(json.dumps(chat_req, ensure_ascii=False))

        while True:
            _check_cancel_and_total_timeout()
            try:
                raw = await asyncio.wait_for(oc_ws.recv(), timeout=poll_seconds)
            except asyncio.TimeoutError:
                if (time.monotonic() - last_event_at) >= recv_timeout:
                    raise OpenClawChatTimeoutError(
                        f"OpenClaw 超过 {int(recv_timeout)} 秒无新响应。",
                        partial_text=buffer,
                    )
                continue

            last_event_at = time.monotonic()
            msg = json.loads(raw)
            if msg.get("type") != "event" or msg.get("event") != "chat":
                continue
            payload = msg.get("payload")
            if not isinstance(payload, dict):
                continue
            emitted_session_key = payload.get("sessionKey")
            if not isinstance(emitted_session_key, str):
                continue
            if not _session_key_matches(emitted_session_key):
                continue

            state = payload.get("state")
            message = payload.get("message")
            text_part = _extract_chat_text(message)
            if text_part:
                buffer = text_part

            await _flush_if_needed()

            if state in ("final", "error", "aborted"):
                await on_assistant_update(buffer, True)
                break

    elapsed_ms = int((time.monotonic() - started_at) * 1000)
    return {
        "agent_id": agent_id,
        "gateway_device_role": role,
        "latency_ms": elapsed_ms,
    }
