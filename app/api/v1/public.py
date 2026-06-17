from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query, Request

from app.core.config import settings
from app.core.security import AdminUser, CurrentUser, QueryCtx, verify_portal_write_auth, verify_user_api_key
from app.db import audit_queries as audit_q
from app.db import notification_queries as notif_q
from app.db import payment_queries as pay_q
from app.db import public_queries as pq
from app.db import token_queries as tq
from app.db.user_models import User
from app.schemas.monitoring import MonitoringBootstrapRequest
from app.schemas.portal import (
    BulkDeleteRequest,
    ExternalSchedulerConfigRequest,
    ExternalSchedulerHeartbeatRequest,
    ExternalSchedulerToggleRequest,
    NewsBulkDeleteRequest,
    NewsTriggerAnalysisRequest,
    WorkflowBootstrapRequest,
    WorkflowTriggerRequest,
)
from app.schemas.billing import PaymentCreateRequest, PaymentResponse
from app.schemas.notification import (
    MarkReadResponse,
    NotificationCreateRequest,
    NotificationCreatedResponse,
    NotificationListResponse,
)
from app.schemas.usage import UsageEntriesResponse, UsageStatsResponse
from app.db.query_context import QueryContext
from app.services.monitoring_service import MonitoringService
from app.services.news_analysis_service import run_news_trigger_analysis
from app.services.token_service import ROUTE_AGENT, ROUTE_WORKFLOW, enrich_usage_entries
from app.services.notification_service import emit_monitor_error
from app.utils.path_safety import parse_uuid, require_uuid

router = APIRouter(tags=["public"])


def _reject_simulated_billing_in_production() -> None:
    if settings.production_mode:
        raise HTTPException(
            status_code=403,
            detail="Simulated billing operations are disabled in production",
        )


@router.get("/public/usage/stats", response_model=UsageStatsResponse, summary="Token 使用统计")
def usage_stats(
    user: CurrentUser,
    range: str = Query(default="7d", description="Time range: 1h, 6h, 24h, 7d, 30d, all"),
) -> UsageStatsResponse:
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="User database is not configured")
    return UsageStatsResponse(**tq.get_usage_stats(str(user.id), range_key=range))


@router.get("/public/usage/entries", response_model=UsageEntriesResponse, summary="Token 使用明细")
def usage_entries(
    user: CurrentUser,
    range: str = Query(default="7d", description="Time range: 1h, 6h, 24h, 7d, 30d, all"),
    limit: int = Query(default=100, ge=1, le=500),
) -> UsageEntriesResponse:
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="User database is not configured")
    rows = enrich_usage_entries(tq.list_usage_entries(str(user.id), range_key=range, limit=limit))
    return UsageEntriesResponse(range=range, entries=rows)


@router.post("/public/payments", response_model=PaymentResponse, summary="创建充值订单")
def create_payment_order(
    user: CurrentUser,
    body: PaymentCreateRequest = Body(default_factory=PaymentCreateRequest),
) -> PaymentResponse:
    from app.db.demo_guard import reject_demo_write

    if not settings.database_url:
        raise HTTPException(status_code=503, detail="User database is not configured")
    reject_demo_write(user)
    try:
        payment = pay_q.create_payment(
            str(user.id),
            tokens=body.tokens,
            amount=body.amount,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return PaymentResponse(**payment)


@router.get("/public/payments/{payment_id}", response_model=PaymentResponse, summary="查询订单状态")
def get_payment_order(user: CurrentUser, payment_id: str) -> PaymentResponse:
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="User database is not configured")
    try:
        payment_uuid = require_uuid(payment_id, "payment_id")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    payment = pay_q.get_payment(payment_uuid, str(user.id))
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return PaymentResponse(**payment)


@router.post(
    "/public/payments/{payment_id}/confirm",
    response_model=PaymentResponse,
    summary="模拟支付确认",
)
def confirm_payment_order(user: CurrentUser, payment_id: str) -> PaymentResponse:
    from app.db.demo_guard import reject_demo_write

    if not settings.database_url:
        raise HTTPException(status_code=503, detail="User database is not configured")
    _reject_simulated_billing_in_production()
    if not settings.payments_simulated_confirm_enabled:
        raise HTTPException(status_code=403, detail="Simulated payment confirmation is disabled")
    reject_demo_write(user)
    try:
        payment_uuid = require_uuid(payment_id, "payment_id")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    try:
        payment = pay_q.confirm_payment(payment_uuid, str(user.id))
    except KeyError:
        raise HTTPException(status_code=404, detail="Payment not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return PaymentResponse(**payment)


@router.get("/public/notifications", response_model=NotificationListResponse, summary="通知列表")
def list_notifications(user: CurrentUser) -> NotificationListResponse:
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="User database is not configured")
    return NotificationListResponse(**notif_q.list_notifications_for_user(str(user.id)))


@router.post(
    "/public/notifications/{notification_id}/read",
    response_model=MarkReadResponse,
    summary="标记通知已读",
)
def mark_notification_read(notification_id: str, user: CurrentUser) -> MarkReadResponse:
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="User database is not configured")
    if not parse_uuid(notification_id):
        raise HTTPException(status_code=422, detail="invalid notification_id")
    ok = notif_q.mark_notification_read(str(user.id), notification_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Notification not found")
    payload = notif_q.list_notifications_for_user(str(user.id))
    return MarkReadResponse(ok=True, unread_count=int(payload["unread_count"]))


@router.post("/public/notifications/read-all", response_model=MarkReadResponse, summary="全部标记已读")
def mark_all_notifications_read(user: CurrentUser) -> MarkReadResponse:
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="User database is not configured")
    notif_q.mark_all_notifications_read(str(user.id))
    payload = notif_q.list_notifications_for_user(str(user.id))
    return MarkReadResponse(ok=True, unread_count=int(payload["unread_count"]))


@router.post(
    "/public/notifications",
    response_model=NotificationCreatedResponse,
    summary="发送通知（ADMIN）",
)
def create_notification(payload: NotificationCreateRequest, _: AdminUser) -> NotificationCreatedResponse:
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="User database is not configured")
    try:
        created = notif_q.create_notification(
            title=payload.title,
            content=payload.content,
            target=payload.target,
            notification_type=payload.notification_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return NotificationCreatedResponse(**created)


@router.get("/public/reports", summary="用户侧报告列表")
def list_reports(ctx: QueryCtx) -> list[dict]:
    pq.require_public_reports_db()
    return pq.list_reports_from_db(ctx)


@router.get("/public/reports/{ingest_id}", summary="用户侧报告详情")
def get_report_detail(ingest_id: str, ctx: QueryCtx) -> dict:
    if not parse_uuid(ingest_id):
        raise HTTPException(status_code=422, detail="invalid ingest_id UUID")
    pq.require_public_reports_db()
    payload = pq.get_report_detail_from_db(ingest_id, ctx)
    if payload is None:
        raise HTTPException(status_code=404, detail="Report not found")
    if not payload.get("insights"):
        payload["insights"] = pq.derive_insights_from_report(payload)
    return payload


@router.post("/public/reports/bulk-delete", summary="批量删除报告")
def bulk_delete_reports(
    request: BulkDeleteRequest,
    user: CurrentUser,
    ctx: QueryCtx,
) -> dict:
    from app.db.demo_guard import reject_demo_write

    reject_demo_write(user)
    pq.require_public_reports_db()
    return pq.delete_reports_from_db(request.ingest_ids, ctx)


@router.get("/public/news/library", summary="用户侧新闻库列表")
def public_news_library(ctx: QueryCtx, limit: int = 100, keyword: str | None = None) -> list[dict]:
    pq.require_public_news_db()
    cap = max(1, min(int(limit), 500))
    return pq.list_news_library_from_db(limit=cap, keyword=keyword, ctx=ctx)


@router.get("/public/news/library/{item_id}", summary="用户侧新闻库详情")
def public_news_library_item(item_id: int, ctx: QueryCtx) -> dict:
    pq.require_public_news_db()
    item = pq.get_news_library_item_from_db(item_id, ctx=ctx)
    if not item:
        raise HTTPException(status_code=404, detail="新闻不存在或无权访问")
    return item


@router.post("/public/news/library/bulk-delete", summary="用户侧批量删除新闻库条目")
def public_news_library_bulk_delete(
    request: NewsBulkDeleteRequest,
    user: CurrentUser,
    ctx: QueryCtx,
) -> dict:
    from app.db.demo_guard import reject_demo_write

    reject_demo_write(user)
    pq.require_public_news_db()
    return pq.delete_news_library_from_db(request.ids, ctx)


@router.get("/public/news/items", summary="用户侧新闻通道条目")
def public_news_items(ctx: QueryCtx, limit: int = 120) -> list[dict]:
    pq.require_public_reports_db()
    cap = max(1, min(int(limit), 300))
    return pq.list_news_items_from_db(limit=cap, ctx=ctx)


@router.get("/public/topic/cards", summary="用户侧专题分析卡片")
def public_topic_cards(ctx: QueryCtx, limit: int = 60) -> list[dict]:
    pq.require_public_reports_db()
    cap = max(1, min(int(limit), 200))
    cards = pq.topic_analysis_cards_from_db(limit=cap, ctx=ctx)
    for card in cards:
        if not card.get("insights"):
            card["insights"] = pq.derive_insights_from_report(card)
    return cards


@router.get("/public/monitoring/scheduler-status", summary="用户侧定时任务状态")
def public_monitoring_scheduler_status(request: Request, ctx: QueryCtx) -> dict:
    return pq.monitoring_scheduler_status_public(request.app)


@router.get("/public/monitoring/external-jobs", summary="用户侧外部定时任务心跳")
def public_monitoring_external_jobs(request: Request, ctx: QueryCtx) -> dict:
    return pq.external_scheduler_jobs_public(request.app, ctx=ctx)


@router.get("/public/portal/openclaw-work-overview", summary="门户首页 OpenClaw 工作情况聚合")
def public_openclaw_work_overview(request: Request, ctx: QueryCtx) -> dict:
    return pq.openclaw_work_overview_public(request.app, ctx=ctx)


@router.get("/public/monitoring/monitors", summary="用户侧关键词监测总览")
def public_monitoring_monitors(ctx: QueryCtx) -> list[dict]:
    return pq.list_monitors_public(ctx)


@router.get("/public/monitoring/{monitor_id}/timeseries", summary="用户侧价格时序数据")
def public_monitoring_timeseries(monitor_id: str, ctx: QueryCtx, window_days: int = 30) -> dict:
    if not parse_uuid(monitor_id):
        raise HTTPException(status_code=422, detail="invalid monitor_id UUID")
    if not pq.monitor_accessible(monitor_id, ctx):
        raise HTTPException(status_code=404, detail="Monitor not found")
    cap_days = max(1, min(int(window_days), 365))
    return pq.monitor_timeseries_public(monitor_id=monitor_id, window_days=cap_days, ctx=ctx)


@router.get("/public/monitoring/{monitor_id}/observations", summary="用户侧价格采集明细")
def public_monitoring_observations(monitor_id: str, ctx: QueryCtx, limit: int = 200) -> dict:
    if not parse_uuid(monitor_id):
        raise HTTPException(status_code=422, detail="invalid monitor_id UUID")
    if not pq.monitor_accessible(monitor_id, ctx):
        raise HTTPException(status_code=404, detail="Monitor not found")
    cap_limit = max(1, min(int(limit), 1000))
    return pq.monitor_observations_public(monitor_id=monitor_id, limit=cap_limit, ctx=ctx)


@router.get("/public/audit/gateway-events", summary="Gateway 对话审计事件（ADMIN）")
def public_gateway_audit_events(
    _: AdminUser,
    limit: int = 100,
    user_id: str | None = None,
) -> dict:
    if user_id and not parse_uuid(user_id):
        raise HTTPException(status_code=422, detail="invalid user_id UUID")
    events = audit_q.list_gateway_audit_events(limit=limit, user_id=user_id)
    return {"events": events, "count": len(events)}


@router.get("/public/workflow/state", summary="网页工作流总览状态")
def public_workflow_state(request: Request, ctx: QueryCtx) -> dict:
    overview = pq.openclaw_work_overview_public(request.app, ctx=ctx)
    scheduler = pq.monitoring_scheduler_status_public(request.app)
    configs = pq.external_scheduler_configs_public(ctx=ctx)
    runs = pq.external_scheduler_run_history_public(limit=60, ctx=ctx)
    return {
        "overview": overview,
        "gateway": overview.get("gateway") or pq.openclaw_gateway_status_public(),
        "internal_scheduler": scheduler,
        "external_scheduler_configs": configs.get("configs", []),
        "external_scheduler_runs": runs.get("runs", []),
    }


@router.get("/public/workflow/gateway-status", summary="OpenClaw Gateway 连通性")
def public_workflow_gateway_status(
    _: User = Depends(verify_portal_write_auth),
) -> dict:
    return pq.openclaw_gateway_status_public()


@router.get("/public/workflow/diagnostics", summary="工作流一键诊断")
def public_workflow_diagnostics(
    request: Request,
    ctx: QueryCtx,
    _: User = Depends(verify_portal_write_auth),
) -> dict:
    return pq.workflow_diagnostics_public(request.app, ctx=ctx)


@router.get("/public/workflow/run-readiness", summary="工作流可运行性验证")
def public_workflow_run_readiness(
    request: Request,
    ctx: QueryCtx,
    monitor_id: str | None = None,
    _: User = Depends(verify_portal_write_auth),
) -> dict:
    if monitor_id and not parse_uuid(monitor_id):
        raise HTTPException(status_code=422, detail="invalid monitor_id UUID")
    return pq.workflow_run_readiness_public(request.app, monitor_id=monitor_id, ctx=ctx)


@router.get("/public/workflow/external-runs", summary="外部调度运行历史")
def public_workflow_external_runs(ctx: QueryCtx, limit: int = 120) -> dict:
    cap_limit = max(1, min(int(limit), 500))
    return pq.external_scheduler_run_history_public(limit=cap_limit, ctx=ctx)


@router.get("/public/workflow/external-configs", summary="外部调度配置列表")
def public_workflow_external_configs(ctx: QueryCtx) -> dict:
    return pq.external_scheduler_configs_public(ctx=ctx)


@router.post("/public/workflow/external-configs", summary="保存外部调度配置")
def public_workflow_external_config_upsert(
    payload: ExternalSchedulerConfigRequest,
    user: CurrentUser,
    ctx: QueryCtx,
) -> dict:
    from app.db.demo_guard import reject_demo_write

    reject_demo_write(user)
    return pq.upsert_external_scheduler_config(payload, ctx)


@router.post("/public/workflow/external-configs/{job_name}/toggle", summary="启停外部调度配置")
def public_workflow_external_config_toggle(
    job_name: str,
    payload: ExternalSchedulerToggleRequest,
    user: CurrentUser,
    ctx: QueryCtx,
) -> dict:
    from app.db.demo_guard import reject_demo_write

    reject_demo_write(user)
    return pq.toggle_external_scheduler_config(job_name=job_name, enabled=payload.enabled, ctx=ctx)


@router.post("/public/workflow/monitor/bootstrap", summary="网页创建监测任务")
def public_workflow_monitor_bootstrap(
    payload: WorkflowBootstrapRequest,
    user: CurrentUser,
) -> dict:
    from app.db.demo_guard import reject_demo_write

    reject_demo_write(user)
    if not settings.monitoring_database_url:
        raise HTTPException(status_code=503, detail="未配置 OPENCLAW_MONITORING_DATABASE_URL。")
    req = MonitoringBootstrapRequest(
        keyword=payload.keyword,
        candidate_count=max(1, min(int(payload.candidate_count), 60)),
        platforms=list(payload.platforms or ["news"]),
        source_profile=payload.source_profile or "auto",
        cadence=payload.cadence or "daily",
    )
    svc = MonitoringService(
        settings.monitoring_database_url,
        allow_server_scrape=settings.monitoring_allow_server_scrape,
    )
    svc.ensure_tables()
    try:
        monitor_id, urls = svc.bootstrap_monitor(
            keyword=req.keyword,
            candidate_count=req.candidate_count,
            platforms=req.platforms,
            cadence=req.cadence,
            source_profile=req.source_profile,
            user_id=user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    return {
        "monitor_id": monitor_id,
        "keyword": req.keyword,
        "inserted_urls": len(urls),
        "urls": urls,
    }


@router.post("/public/workflow/analysis/run", summary="网页触发联合分析并可选发布")
def public_workflow_analysis_run(
    payload: WorkflowTriggerRequest,
    background_tasks: BackgroundTasks,
    user: CurrentUser,
    ctx: QueryCtx,
) -> dict:
    from app.db.demo_guard import reject_demo_write

    reject_demo_write(user)
    window_days = max(1, min(int(payload.window_days), 365))
    news_hours = max(1, min(int(payload.news_hours), 24 * 30))
    return run_news_trigger_analysis(
        monitor_id=payload.monitor_id,
        keyword=payload.keyword,
        keywords=payload.keywords,
        window_days=window_days,
        news_hours=news_hours,
        horizon=payload.horizon,
        publish=payload.publish,
        background_tasks=background_tasks,
        user_id=user.id,
        ctx=ctx,
        billing_route=ROUTE_WORKFLOW,
    )


@router.post("/openclaw/monitoring/external-heartbeat", summary="上报外部定时任务心跳")
def report_external_scheduler_heartbeat(
    payload: ExternalSchedulerHeartbeatRequest,
    request: Request,
    user: User = Depends(verify_user_api_key),
) -> dict:
    if payload.monitor_id:
        if not parse_uuid(payload.monitor_id):
            raise HTTPException(status_code=422, detail="invalid monitor_id UUID")
        heartbeat_ctx = QueryContext(user_id=user.id, role=user.role)
        if not pq.monitor_accessible(payload.monitor_id, heartbeat_ctx):
            raise HTTPException(status_code=404, detail="Monitor not found")
    now = pq.save_external_scheduler_run(
        job_name=payload.job_name,
        status=payload.status,
        monitor_id=payload.monitor_id,
        message=payload.message,
        source="heartbeat",
        user_id=user.id,
    )
    request.app.state.external_scheduler_jobs[f"{user.id}:{payload.job_name}"] = {
        "status": payload.status,
        "monitor_id": payload.monitor_id,
        "message": payload.message,
        "last_seen_at": now,
        "user_id": user.id,
    }
    status_norm = (payload.status or "").strip().lower()
    if status_norm and status_norm not in {"ok", "success"}:
        emit_monitor_error(
            user.id,
            monitor_id=payload.monitor_id or payload.job_name,
            message=payload.message or f"外部任务 {payload.job_name} 状态异常：{payload.status}",
        )
    return {"ok": True, "job_name": payload.job_name, "last_seen_at": now}


@router.post("/openclaw/analysis/news-trigger", summary="新闻触发价格联合分析")
def trigger_news_price_analysis(
    payload: NewsTriggerAnalysisRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(verify_user_api_key),
) -> dict:
    window_days = max(1, min(int(payload.window_days), 365))
    news_hours = max(1, min(int(payload.news_hours), 24 * 30))
    return run_news_trigger_analysis(
        monitor_id=payload.monitor_id,
        keyword=payload.keyword,
        keywords=None,
        window_days=window_days,
        news_hours=news_hours,
        horizon=payload.horizon,
        publish=payload.publish,
        background_tasks=background_tasks,
        user_id=user.id,
        ctx=QueryContext(user_id=user.id, role=user.role),
        billing_route=ROUTE_AGENT,
    )
