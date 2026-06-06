from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_v1_prefix: str = "/api/v1"
    openclaw_api_key: str = Field(default="dev-openclaw-key")
    openclaw_enable_signature: bool = Field(default=False)
    openclaw_hmac_secret: str = Field(default="dev-secret")
    content_raw_dir: str = Field(default="content/reports/raw")
    content_rendered_dir: str = Field(default="content/reports/rendered")
    git_auto_push: bool = Field(default=False)
    git_remote: str = Field(default="origin")
    git_branch: str = Field(default="main")
    # Optional PostgreSQL DSN, for example:
    # postgresql://openclaw_app:password@127.0.0.1:5432/openclaw_app
    database_url: str | None = Field(default=None)
    # Optional PostgreSQL DSN dedicated to keyword monitoring.
    # Example: postgresql://openclaw_monitor:password@127.0.0.1:5432/openclaw_monitor
    monitoring_database_url: str | None = Field(default=None)
    # Optional PostgreSQL DSN dedicated to news library storage.
    # Example: postgresql://openclaw_news:password@127.0.0.1:5432/openclaw_news
    news_database_url: str | None = Field(default=None)
    # When false (default), the app does not HTTP-fetch monitor URLs; OpenClaw should POST observations.
    # Set OPENCLAW_MONITORING_ALLOW_SERVER_SCRAPE=true to restore legacy server-side scraping (run-once / scheduler).
    monitoring_allow_server_scrape: bool = Field(default=False)
    # Internal scheduler for periodic monitoring run-once jobs.
    monitoring_scheduler_enabled: bool = Field(default=False)
    monitoring_scheduler_monitor_id: str | None = Field(default=None)
    monitoring_scheduler_interval_minutes: int = Field(default=1440)
    monitoring_scheduler_run_on_start: bool = Field(default=False)
    # OpenClaw Gateway WebSocket endpoint.
    # It is used by the chat proxy in `app/api/v1/chat.py`.
    openclaw_ws_url: str = Field(default="ws://localhost:18789/ws")
    # Probe timeout for checking OpenClaw Gateway availability (seconds).
    openclaw_gateway_probe_timeout_seconds: float = Field(default=2.0)
    # Max idle time waiting for the next Gateway event during one chat turn (seconds).
    openclaw_chat_recv_timeout_seconds: float = Field(default=120.0)
    # Max wall-clock time for one chat turn from connect through final event (seconds).
    openclaw_chat_total_timeout_seconds: float = Field(default=600.0)
    bind_host: str = Field(default="0.0.0.0")
    bind_port: int = Field(default=8000)
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        description="Comma-separated CORS origins for SPA dev server",
    )
    serve_spa: bool = Field(default=True, description="Serve built frontend from frontend/dist")
    # Deprecated: do not embed API keys in SPA HTML (security risk). Use portal session cookie instead.
    portal_embed_api_key_in_spa: bool = Field(default=False)
    # When true, refuse startup if default/weak secrets or signature disabled (production hardening).
    production_mode: bool = Field(default=False)
    expose_openapi: bool = Field(default=False)
    max_request_body_bytes: int = Field(default=1_048_576, description="Max HTTP request body size (1 MiB)")
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_read_per_minute: int = Field(default=180)
    rate_limit_write_per_minute: int = Field(default=40)
    healthz_expose_db_detail: bool = Field(default=False)
    trust_x_forwarded_for: bool = Field(
        default=False,
        description="Only enable behind a trusted reverse proxy for rate-limit client IP",
    )
    ws_messages_per_minute: int = Field(default=12, description="Per WebSocket connection user_message rate limit")
    expose_gateway_ws_url: bool = Field(
        default=False,
        description="Include raw OPENCLAW_WS_URL in public gateway status responses",
    )
    # Multi-user auth (JWT + per-user API keys)
    jwt_secret: str = Field(default="dev-jwt-secret-change-me-in-production")
    jwt_access_ttl_seconds: int = Field(default=900)
    jwt_refresh_ttl_seconds: int = Field(default=604800)
    allow_registration: bool = Field(default=True)
    first_user_is_admin: bool = Field(default=True)
    legacy_api_key_enabled: bool = Field(
        default=False,
        description="When true, OPENCLAW_OPENCLAW_API_KEY maps to ADMIN scope (deprecated transition)",
    )
    login_max_attempts: int = Field(default=5)
    login_lockout_seconds: int = Field(default=900)

    model_config = SettingsConfigDict(env_prefix="OPENCLAW_", env_file=".env", extra="ignore")


settings = Settings()
