from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request, status

from app.core.config import settings
from app.core.security import verify_optional_signature, verify_user_api_key
from app.db import public_queries as pq
from app.db.query_context import QueryContext
from app.db.user_models import User
from app.db.repositories import InMemoryIngestRepository, PostgresIngestRepository
from app.schemas.monitoring import (
    MonitoringAddUrlsRequest,
    MonitoringAddUrlsResponse,
    MonitoringBootstrapRequest,
    MonitoringBootstrapResponse,
    MonitoringObservationIngestRequest,
    MonitoringObservationIngestResponse,
    MonitoringRunOnceResponse,
    MonitoringSummaryResponse,
)
from app.schemas.news import NewsLibraryCreated, NewsLibraryIn, NewsLibraryItem
from app.schemas.report import IngestAccepted, IngestStatusResponse, OpenClawReportIn
from app.services.intake_service import IntakeService
from app.services.monitoring_service import MonitoringService
from app.services.publish_service import PublishService
from app.services.report_service import ReportService
from app.workers.job_runner import JobRunner

router = APIRouter(
    prefix="/openclaw",
    tags=["OpenClaw 接入"],
)

repo = PostgresIngestRepository(settings.database_url) if settings.database_url else InMemoryIngestRepository()
job_runner = JobRunner(repo=repo, report_service=ReportService(), publish_service=PublishService())
intake_service = IntakeService(repo=repo, job_runner=job_runner)


def _require_monitor_accessible(monitor_id: str, user: User) -> None:
    ctx = QueryContext(user_id=user.id, role=user.role)
    if not pq.monitor_accessible(monitor_id, ctx):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitor not found")


def _assert_ingest_owner(record, user: User) -> None:
    if record.user_id and record.user_id != user.id and user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingest not found")


def _ensure_news_tables(news_db_url: str) -> None:
    import psycopg

    sql = """
    CREATE TABLE IF NOT EXISTS news_library (
      id BIGSERIAL PRIMARY KEY,
      keyword TEXT NOT NULL,
      summary TEXT NOT NULL,
      source_url TEXT NOT NULL,
      title TEXT,
      source_name TEXT,
      published_at TIMESTAMPTZ,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_news_library_keyword_created_at
      ON news_library (keyword, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_news_library_source_url
      ON news_library (source_url);
    ALTER TABLE news_library ADD COLUMN IF NOT EXISTS user_id UUID;
    """
    with psycopg.connect(news_db_url) as conn, conn.cursor() as cur:
        cur.execute(sql)
        conn.commit()


@router.post(
    "/reports",
    response_model=IngestAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    summary="上报 OpenClaw 报告",
    description="接收 OpenClaw 发送的结构化报告 JSON，校验后入队异步处理。",
)
async def create_report_ingest(
    request: Request,
    report: OpenClawReportIn,
    background_tasks: BackgroundTasks,
    x_request_id: str | None = Header(default=None, description="请求幂等键，请求重试时保持一致。"),
    x_signature: str | None = Header(default=None, description="可选签名；开启签名校验时必填。"),
    user: User = Depends(verify_user_api_key),
) -> IngestAccepted:
    verify_optional_signature(await request.body(), x_signature)
    ingest_id, ingest_status = intake_service.ingest(
        report=report,
        request_id=x_request_id,
        background_tasks=background_tasks,
        user_id=user.id,
    )
    return IngestAccepted(ingest_id=ingest_id, status=ingest_status)


@router.get(
    "/reports/{ingest_id}",
    response_model=IngestStatusResponse,
    summary="查询处理状态",
    description="根据 ingest_id 查询任务状态与产物路径。",
)
def get_ingest_status(
    ingest_id: str,
    user: User = Depends(verify_user_api_key),
) -> IngestStatusResponse:
    record = repo.get_by_ingest_id(ingest_id=ingest_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingest not found")
    _assert_ingest_owner(record, user)
    return IngestStatusResponse(
        ingest_id=record.ingest_id,
        request_id=record.request_id,
        task_id=record.task_id,
        status=record.status,
        raw_path=record.raw_path,
        rendered_path=record.rendered_path,
        error=record.error,
    )


@router.post(
    "/reports/{ingest_id}/retry",
    response_model=IngestAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    summary="重试失败任务（预留）",
    description="仅允许对失败任务发起重试。当前为预留接口。",
)
def retry_ingest(
    ingest_id: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(verify_user_api_key),
) -> IngestAccepted:
    record = repo.get_by_ingest_id(ingest_id=ingest_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingest not found")
    _assert_ingest_owner(record, user)
    if record.status != "failed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only failed ingest can be retried")
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Retry payload hydration not implemented")


@router.post(
    "/monitoring/bootstrap",
    response_model=MonitoringBootstrapResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建关键词监测并自动生成候选 URL",
    description=(
        "默认（OPENCLAW_MONITORING_ALLOW_SERVER_SCRAPE=false）仅创建监测任务并写入一条占位 URL，"
        "由 OpenClaw 采集后 POST observations/ingest 入库；"
        "若将 OPENCLAW_MONITORING_ALLOW_SERVER_SCRAPE=true，则按关键词推断生成候选抓取 URL（大宗商品或电商）。"
    ),
)
def bootstrap_monitoring(
    payload: MonitoringBootstrapRequest,
    user: User = Depends(verify_user_api_key),
) -> MonitoringBootstrapResponse:
    if not settings.monitoring_database_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="未配置 OPENCLAW_MONITORING_DATABASE_URL。",
        )
    service = MonitoringService(
        settings.monitoring_database_url,
        allow_server_scrape=settings.monitoring_allow_server_scrape,
    )
    service.ensure_tables()
    monitor_id, urls = service.bootstrap_monitor(
        keyword=payload.keyword,
        candidate_count=payload.candidate_count,
        platforms=payload.platforms,
        cadence=payload.cadence,
        source_profile=payload.source_profile,
        user_id=user.id,
    )
    return MonitoringBootstrapResponse(
        monitor_id=monitor_id,
        keyword=payload.keyword,
        inserted_urls=len(urls),
        urls=urls,
    )


@router.post(
    "/monitoring/{monitor_id}/run-once",
    response_model=MonitoringRunOnceResponse,
    status_code=status.HTTP_200_OK,
    summary="执行一次监测采样并写入 observations",
    description=(
        "仅在 OPENCLAW_MONITORING_ALLOW_SERVER_SCRAPE=true 时遍历 URL 并服务端抓取；"
        "否则返回 server_scrape_skipped=true，不发起外网请求（请用 observations/ingest）。"
    ),
)
def run_monitoring_once(
    monitor_id: str,
    user: User = Depends(verify_user_api_key),
) -> MonitoringRunOnceResponse:
    if not settings.monitoring_database_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="未配置 OPENCLAW_MONITORING_DATABASE_URL。",
        )
    _require_monitor_accessible(monitor_id, user)
    service = MonitoringService(
        settings.monitoring_database_url,
        allow_server_scrape=settings.monitoring_allow_server_scrape,
    )
    service.ensure_tables()
    try:
        result = service.run_once(monitor_id=monitor_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitor not found")
    return MonitoringRunOnceResponse(**result)


@router.post(
    "/monitoring/{monitor_id}/observations/ingest",
    response_model=MonitoringObservationIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="OpenClaw 上报一条价格观测并入库",
    description="将 OpenClaw 已解析的价格写入 price_observations；无需服务端抓取页面。",
)
def ingest_monitoring_observation(
    monitor_id: str,
    payload: MonitoringObservationIngestRequest,
    user: User = Depends(verify_user_api_key),
) -> MonitoringObservationIngestResponse:
    if not settings.monitoring_database_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="未配置 OPENCLAW_MONITORING_DATABASE_URL。",
        )
    service = MonitoringService(
        settings.monitoring_database_url,
        allow_server_scrape=settings.monitoring_allow_server_scrape,
    )
    service.ensure_tables()
    try:
        result = service.ingest_openclaw_observation(
            monitor_id,
            price=payload.price,
            title=payload.title,
            currency=payload.currency,
            captured_at=payload.captured_at,
            source_url=payload.source_url,
            raw_payload=payload.raw_payload,
            user_id=user.id,
        )
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitor not found")
    return MonitoringObservationIngestResponse(**result)


@router.get(
    "/monitoring/{monitor_id}/summary",
    response_model=MonitoringSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="查询监测窗口期摘要",
    description="返回最近 N 天的观测数量和价格统计。",
)
def get_monitoring_summary(
    monitor_id: str,
    window_days: int = 7,
    user: User = Depends(verify_user_api_key),
) -> MonitoringSummaryResponse:
    window_days = max(1, min(int(window_days), 365))
    if not settings.monitoring_database_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="未配置 OPENCLAW_MONITORING_DATABASE_URL。",
        )
    _require_monitor_accessible(monitor_id, user)
    service = MonitoringService(
        settings.monitoring_database_url,
        allow_server_scrape=settings.monitoring_allow_server_scrape,
    )
    service.ensure_tables()
    try:
        result = service.get_summary(monitor_id=monitor_id, window_days=window_days)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitor not found")
    return MonitoringSummaryResponse(**result)


@router.post(
    "/monitoring/{monitor_id}/urls",
    response_model=MonitoringAddUrlsResponse,
    status_code=status.HTTP_200_OK,
    summary="为监测任务追加 URL",
    description="用于手工补充商品详情页 URL，提升价格抽取命中率。",
)
def add_monitoring_urls(
    monitor_id: str,
    payload: MonitoringAddUrlsRequest,
    user: User = Depends(verify_user_api_key),
) -> MonitoringAddUrlsResponse:
    if not settings.monitoring_database_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="未配置 OPENCLAW_MONITORING_DATABASE_URL。",
        )
    _require_monitor_accessible(monitor_id, user)
    service = MonitoringService(
        settings.monitoring_database_url,
        allow_server_scrape=settings.monitoring_allow_server_scrape,
    )
    service.ensure_tables()
    try:
        inserted = service.add_urls(monitor_id=monitor_id, urls=payload.urls, platform=payload.platform)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitor not found")
    return MonitoringAddUrlsResponse(monitor_id=monitor_id, inserted_urls=inserted)


@router.get(
    "/monitoring/scheduler/status",
    status_code=status.HTTP_200_OK,
    summary="查询内部监测定时任务状态",
    description="返回内部 scheduler 的配置与当前启动状态。",
)
def get_monitoring_scheduler_status(
    request: Request,
    _: None = Depends(verify_user_api_key),
) -> dict:
    started = bool(getattr(request.app.state, "monitoring_scheduler_started", False))
    has_db = bool(settings.monitoring_database_url)
    has_monitor = bool(settings.monitoring_scheduler_monitor_id)
    return {
        "mode": "internal",
        "enabled": settings.monitoring_scheduler_enabled,
        "started": started,
        "configured": settings.monitoring_scheduler_enabled and has_db and has_monitor,
        "monitor_id": settings.monitoring_scheduler_monitor_id,
        "interval_minutes": settings.monitoring_scheduler_interval_minutes,
        "run_on_start": settings.monitoring_scheduler_run_on_start,
        "has_monitoring_database_url": has_db,
        "allow_server_scrape": settings.monitoring_allow_server_scrape,
    }


@router.post(
    "/news/library",
    response_model=NewsLibraryCreated,
    status_code=status.HTTP_201_CREATED,
    summary="写入新闻库",
    description="将新闻条目写入独立 news_library（关键词、概述、原文链接等）。",
)
def create_news_library_item(
    payload: NewsLibraryIn,
    user: User = Depends(verify_user_api_key),
) -> NewsLibraryCreated:
    if not settings.news_database_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="未配置 OPENCLAW_NEWS_DATABASE_URL。",
        )
    _ensure_news_tables(settings.news_database_url)
    import psycopg

    sql = """
    INSERT INTO news_library (keyword, summary, source_url, title, source_name, published_at, user_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s::uuid)
    RETURNING id, created_at
    """
    with psycopg.connect(settings.news_database_url) as conn, conn.cursor() as cur:
        cur.execute(
            sql,
            (
                payload.keyword,
                payload.summary,
                payload.source_url,
                payload.title,
                payload.source_name,
                payload.published_at,
                user.id,
            ),
        )
        row = cur.fetchone()
        conn.commit()
    return NewsLibraryCreated(id=int(row[0]), created_at=row[1])


@router.get(
    "/news/library",
    response_model=list[NewsLibraryItem],
    status_code=status.HTTP_200_OK,
    summary="查询新闻库",
    description="按关键词可选过滤新闻库，默认返回最近 100 条。",
)
def list_news_library_items(
    keyword: str | None = None,
    limit: int = 100,
    user: User = Depends(verify_user_api_key),
) -> list[NewsLibraryItem]:
    pq.require_public_news_db()
    cap = max(1, min(int(limit), 500))
    ctx = QueryContext(user_id=user.id, role=user.role)
    rows = pq.list_news_library_from_db(limit=cap, keyword=keyword, ctx=ctx)
    return [
        NewsLibraryItem(
            id=int(row["id"]),
            keyword=row["keyword"],
            summary=row["summary"],
            source_url=row["source_url"],
            title=row["title"],
            source_name=row["source_name"],
            published_at=row["published_at"],
            created_at=row["created_at"],
        )
        for row in rows
    ]
