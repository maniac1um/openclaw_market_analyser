"""Role-based permission checks before forwarding portal chat to OpenClaw Gateway."""

from __future__ import annotations

from dataclasses import dataclass

from app.db.query_context import ADMIN_ROLE
from app.db.user_models import User
from app.utils.prompt_safety import check_gateway_user_message, check_user_message


@dataclass(frozen=True)
class GatewayChatDecision:
    allowed: bool
    decision: str  # allowed | blocked | elevated | requires_admin
    reason: str | None = None
    elevated: bool = False
    agent_id: str | None = None
    gateway_device_role: str | None = None


def assert_chat_allowed(
    user: User,
    message: str,
    *,
    chat_enabled_for_user: bool,
    portal_agent_id: str,
    admin_agent_id: str,
) -> GatewayChatDecision:
    """
    Evaluate whether a portal user may send *message* to Gateway.

    USER role: read-only assistant path only; blocks shell/file/admin intent.
    ADMIN role: elevated path with full agent; still subject to baseline safety filters.
    """
    if user.role != ADMIN_ROLE and not chat_enabled_for_user:
        return GatewayChatDecision(
            allowed=False,
            decision="blocked",
            reason="门户对话当前仅对管理员开放。",
        )

    blocked = check_user_message(message)
    if blocked:
        return GatewayChatDecision(
            allowed=False,
            decision="blocked",
            reason=f"检测到可能有害或违规内容（{blocked}）。",
        )

    if user.role != ADMIN_ROLE:
        gateway_blocked = check_gateway_user_message(message)
        if gateway_blocked:
            return GatewayChatDecision(
                allowed=False,
                decision="blocked",
                reason=f"该请求超出门户只读助手权限（{gateway_blocked}）。",
            )
        return GatewayChatDecision(
            allowed=True,
            decision="allowed",
            elevated=False,
            agent_id=portal_agent_id,
            gateway_device_role="portal",
        )

    return GatewayChatDecision(
        allowed=True,
        decision="elevated",
        elevated=True,
        agent_id=admin_agent_id,
        gateway_device_role="admin",
    )


def build_gateway_message(
    *,
    portal_user_id: str,
    portal_role: str,
    agent_id: str,
    user_text: str,
) -> str:
    """Inject immutable portal context prefix before forwarding to Gateway."""
    if portal_role == ADMIN_ROLE:
        role_hint = (
            "你是门户管理员助手。用户为门户 ADMIN，可协助工作流与市场分析，"
            "但 destructive shell/任意文件删除仍须用户明确确认。"
        )
    else:
        role_hint = (
            "你是门户只读助手（portal-readonly）。用户在门户中的角色是 USER，不是 Gateway 管理员。"
            "禁止执行 shell、读写服务器文件、修改 Gateway/OpenClaw 配置、删除数据或发起未授权 HTTP。"
            "仅可：解答市场分析问题、引导用户打开门户页面（报告/监测/工作流/账户）。"
            "若用户询问权限，明确回答：门户 USER，无 Gateway 管理员权限。"
        )
    return (
        f"[PORTAL_CONTEXT user_id={portal_user_id} role={portal_role} agent={agent_id}]\n"
        f"{role_hint}\n"
        f"用户消息：{user_text.strip()}"
    )
