"""Event-driven in-app notifications."""

from __future__ import annotations

import logging

from app.core.config import settings
from app.db import notification_queries as nq

logger = logging.getLogger(__name__)

NOTIFICATION_TYPE_REPORT_READY = nq.NOTIFICATION_TYPE_REPORT_READY
NOTIFICATION_TYPE_TOKEN_LOW = nq.NOTIFICATION_TYPE_TOKEN_LOW
NOTIFICATION_TYPE_WORKFLOW_DONE = nq.NOTIFICATION_TYPE_WORKFLOW_DONE
NOTIFICATION_TYPE_MONITOR_ERROR = nq.NOTIFICATION_TYPE_MONITOR_ERROR

_TYPE_TITLES: dict[str, str] = {
    NOTIFICATION_TYPE_REPORT_READY: "报告已生成",
    NOTIFICATION_TYPE_TOKEN_LOW: "Token 余额不足",
    NOTIFICATION_TYPE_WORKFLOW_DONE: "工作流已完成",
    NOTIFICATION_TYPE_MONITOR_ERROR: "监测异常",
}


def create_notification(user_id: str, notification_type: str, content: str) -> None:
    """Create a user-targeted notification for a system event (never raises)."""
    if not settings.database_url:
        return
    if not user_id or notification_type not in nq.VALID_NOTIFICATION_TYPES:
        return
    text = (content or "").strip()
    if not text:
        return
    title = _TYPE_TITLES.get(notification_type, "系统通知")
    try:
        nq.create_notification(
            title=title,
            content=text[:4000],
            target=user_id,
            notification_type=notification_type,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "failed to create notification user_id=%s type=%s error=%s",
            user_id,
            notification_type,
            exc,
        )


def emit_report_ready(
    user_id: str,
    *,
    keyword: str,
    ingest_id: str,
    title: str | None = None,
) -> None:
    kw = (keyword or "").strip() or "未命名"
    report_title = (title or "").strip()
    detail = f"《{kw}》专题报告已生成，可在「专题分析」中查看。"
    if report_title:
        detail = f"「{report_title}」已生成，关键词：{kw}。"
    create_notification(
        user_id,
        NOTIFICATION_TYPE_REPORT_READY,
        f"{detail}（ID: {ingest_id[:8]}…）",
    )


def emit_token_low(
    user_id: str,
    *,
    balance: int,
    required: int | None = None,
) -> None:
    if nq.has_recent_notification(user_id, NOTIFICATION_TYPE_TOKEN_LOW, within_minutes=10):
        return
    if required is not None:
        content = f"当前余额 {balance} tokens，本次操作需要 {required} tokens。请前往充值或稍后再试。"
    else:
        content = f"当前余额 {balance} tokens，不足以完成本次 AI 操作。请前往「账单」充值。"
    create_notification(user_id, NOTIFICATION_TYPE_TOKEN_LOW, content)


def emit_workflow_done(
    user_id: str,
    *,
    keyword: str,
    publish: bool,
    ingest_id: str | None = None,
) -> None:
    kw = (keyword or "").strip() or "未命名"
    if publish and ingest_id:
        content = f"「{kw}」联合分析已完成，报告已发布。"
    elif publish:
        content = f"「{kw}」联合分析已完成并已提交报告。"
    else:
        content = f"「{kw}」联合分析已完成，可在工作流页面查看结果。"
    create_notification(user_id, NOTIFICATION_TYPE_WORKFLOW_DONE, content)


def emit_monitor_error(
    user_id: str,
    *,
    monitor_id: str,
    keyword: str | None = None,
    message: str,
) -> None:
    if nq.has_recent_notification(user_id, NOTIFICATION_TYPE_MONITOR_ERROR, within_minutes=5):
        return
    kw = (keyword or "").strip()
    prefix = f"关键词「{kw}」" if kw else "监测任务"
    detail = (message or "").strip() or "监测执行失败"
    create_notification(
        user_id,
        NOTIFICATION_TYPE_MONITOR_ERROR,
        f"{prefix}出现异常：{detail}（monitor: {monitor_id[:8]}…）",
    )
