import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.openclaw import router as openclaw_router
from app.api.v1.public import router as public_router
from app.core.config import settings
from app.core.startup_checks import validate_security_config
from app.middleware.security import MaxBodySizeMiddleware, RateLimitMiddleware, SecurityHeadersMiddleware
from app.services.monitoring_scheduler import MonitoringScheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

_monitoring_scheduler: MonitoringScheduler | None = None
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _monitoring_scheduler
    validate_security_config()
    if settings.database_url:
        try:
            from app.db.user_queries import run_multi_user_migrations

            run_multi_user_migrations()
        except Exception as exc:
            logging.getLogger(__name__).warning("multi-user migration skipped: %s", exc)
    if settings.monitoring_scheduler_enabled:
        if not settings.monitoring_database_url:
            logging.getLogger(__name__).warning(
                "monitoring scheduler enabled but OPENCLAW_MONITORING_DATABASE_URL is not set"
            )
            app.state.monitoring_scheduler_started = False
        elif not settings.monitoring_scheduler_monitor_id:
            logging.getLogger(__name__).warning(
                "monitoring scheduler enabled but OPENCLAW_MONITORING_SCHEDULER_MONITOR_ID is not set"
            )
            app.state.monitoring_scheduler_started = False
        elif not settings.monitoring_allow_server_scrape:
            logging.getLogger(__name__).warning(
                "monitoring scheduler skipped: OPENCLAW_MONITORING_ALLOW_SERVER_SCRAPE is false"
            )
            app.state.monitoring_scheduler_started = False
        else:
            _monitoring_scheduler = MonitoringScheduler(
                database_url=settings.monitoring_database_url,
                monitor_id=settings.monitoring_scheduler_monitor_id,
                interval_minutes=settings.monitoring_scheduler_interval_minutes,
                run_on_start=settings.monitoring_scheduler_run_on_start,
                allow_server_scrape=settings.monitoring_allow_server_scrape,
            )
            _monitoring_scheduler.start()
            app.state.monitoring_scheduler_started = True
    else:
        app.state.monitoring_scheduler_started = False

    yield

    if _monitoring_scheduler is not None:
        _monitoring_scheduler.stop()
    app.state.monitoring_scheduler_started = False


def create_app() -> FastAPI:
    docs_url = "/docs" if settings.expose_openapi else None
    redoc_url = "/redoc" if settings.expose_openapi else None
    openapi_url = "/openapi.json" if settings.expose_openapi else None

    app = FastAPI(
        title="OpenClaw 新闻发布服务",
        description="接收 OpenClaw 生成的新闻分析结果，完成入站、处理与发布。",
        version="0.2.0",
        lifespan=lifespan,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )
    app.state.monitoring_scheduler_started = False
    app.state.external_scheduler_jobs = {}

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        MaxBodySizeMiddleware,
        max_bytes=settings.max_request_body_bytes,
    )
    app.add_middleware(RateLimitMiddleware)

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=[
                "Content-Type",
                "X-Api-Key",
                "X-Request-Id",
                "X-Signature",
                "Authorization",
            ],
        )

    app.include_router(openclaw_router, prefix=settings.api_v1_prefix)
    app.include_router(auth_router, prefix=settings.api_v1_prefix)
    app.include_router(chat_router, prefix=settings.api_v1_prefix)
    app.include_router(public_router, prefix=settings.api_v1_prefix)

    @app.get("/healthz", summary="健康检查")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/healthz/db", summary="数据库健康检查")
    def healthz_db() -> dict:
        if not settings.database_url:
            return {"ok": False, "enabled": False, "detail": "database_url is not configured"}
        try:
            import psycopg

            with psycopg.connect(settings.database_url) as conn, conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
            return {"ok": True, "enabled": True}
        except Exception as exc:  # noqa: BLE001
            detail = str(exc) if settings.healthz_expose_db_detail else "database connection failed"
            return {"ok": False, "enabled": True, "detail": detail}

    if settings.serve_spa and FRONTEND_DIST.is_dir():
        assets_dir = FRONTEND_DIST / "assets"
        if assets_dir.is_dir():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        def _spa_index_response():
            index = FRONTEND_DIST / "index.html"
            if not index.is_file():
                return None
            if settings.portal_embed_api_key_in_spa:
                content = index.read_text(encoding="utf-8")
                runtime = json.dumps({"apiKey": settings.openclaw_api_key}, ensure_ascii=False)
                inject = f"<script>window.__OPENCLAW_RUNTIME__={runtime}</script>"
                if "</head>" in content:
                    content = content.replace("</head>", f"  {inject}\n  </head>", 1)
                else:
                    content = inject + content
                return HTMLResponse(content)
            return FileResponse(index)

        @app.get("/{full_path:path}", include_in_schema=False)
        def spa_fallback(full_path: str):
            if full_path.startswith(("api/", "docs", "openapi.json", "redoc")):
                raise HTTPException(status_code=404, detail="Not Found")
            response = _spa_index_response()
            if response is not None:
                return response
            return {"detail": "Frontend not built. Run: cd frontend && npm run build"}

    return app


app = create_app()
