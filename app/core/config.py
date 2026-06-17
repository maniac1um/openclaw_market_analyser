from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os


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
    cookie_secure: bool = Field(
        default=False,
        description="Set Secure flag on refresh token cookie (required in production)",
    )
    cookie_domain: str | None = Field(
        default=None,
        description="Optional Domain attribute for refresh token cookie",
    )
    allow_registration: bool = Field(default=True)
    first_user_is_admin: bool = Field(default=True)
    legacy_api_key_enabled: bool = Field(
        default=False,
        description="When true, OPENCLAW_OPENCLAW_API_KEY maps to ADMIN scope (deprecated transition)",
    )
    login_max_attempts: int = Field(default=5)
    login_lockout_seconds: int = Field(default=900)
    # Gateway proxy isolation: separate state dirs for portal (limited) vs admin device identity.
    gateway_state_dir: str | None = Field(
        default=None,
        description="Admin/full Gateway device state (openclaw.json, identity/, devices/). "
        "Falls back to OPENCLAW_STATE_DIR env or ~/.openclaw",
    )
    gateway_portal_state_dir: str | None = Field(
        default=None,
        description="Portal USER Gateway device state with restricted scopes. Required in production "
        "when chat is enabled for USER role.",
    )
    gateway_portal_agent_id: str = Field(
        default="portal-readonly",
        description="OpenClaw agent id for portal USER chat (must be configured on Gateway)",
    )
    gateway_admin_agent_id: str = Field(
        default="main",
        description="OpenClaw agent id for ADMIN portal chat",
    )
    chat_enabled_for_user: bool = Field(
        default=True,
        description="When false, only ADMIN role may use portal chat WebSocket",
    )
    chat_user_messages_per_minute: int = Field(
        default=30,
        description="Per-user chat message rate limit across all WS connections",
    )
    demo_user_email: str = Field(default="demo@openclaw.local")
    demo_user_password: str = Field(default="Demo_OpenClaw2026")
    demo_seed_enabled: bool = Field(
        default=True,
        description="Seed demo trial account on startup; disable in production",
    )
    demo_reset_marker_path: Path = Field(
        default=Path("content/demo/.last_reset"),
        description="UTC date marker for daily demo data reset",
    )
    default_token_balance: int = Field(
        default=10_000,
        description="Initial token balance for new and backfilled users",
    )
    token_response_reserve: int = Field(
        default=512,
        description="Reserved tokens estimated for each chat response when pre-checking balance",
    )
    token_workflow_cost: int = Field(
        default=500,
        description="Fixed token cost per portal workflow analysis run",
    )
    token_agent_cost: int = Field(
        default=500,
        description="Fixed token cost per OpenClaw agent news-trigger analysis",
    )
    token_report_cost: int = Field(
        default=300,
        description="Fixed token cost per report ingest/generation",
    )
    simulated_recharge_amount: int = Field(
        default=1000,
        description="Tokens credited per simulated recharge (no real payment)",
    )
    subscription_monthly_tokens_free: int = Field(
        default=5000,
        description="Monthly subscription token grant for free plan",
    )
    subscription_monthly_tokens_pro: int = Field(
        default=100_000,
        description="Monthly subscription token grant for pro plan",
    )
    subscription_grant_period_days: int = Field(
        default=30,
        description="Days added to current_period_end after each monthly grant",
    )
    subscription_grant_scheduler_enabled: bool = Field(
        default=True,
        description="Enable cron scheduler for monthly subscription token grants",
    )
    subscription_grant_scheduler_interval_minutes: int = Field(
        default=60,
        description="How often the grant scheduler checks the cron window",
    )
    subscription_grant_scheduler_cron_hour_utc: int = Field(
        default=0,
        description="UTC hour (0-23) when daily grant batch may run",
    )
    subscription_grant_scheduler_run_on_start: bool = Field(
        default=False,
        description="Run grant batch immediately on app startup (if cron window matches)",
    )
    token_balance_cache_seconds: int = Field(
        default=30,
        description="Optional TTL for computed token balance cache (0 disables)",
    )
    token_rate_limit_enabled: bool = Field(
        default=True,
        description="Per-user token billing rate limits (requests and spend per minute)",
    )
    token_requests_per_minute: int = Field(
        default=10,
        description="Max token-billed operations per user per minute",
    )
    token_spend_per_minute: int = Field(
        default=5000,
        description="Max tokens consumed per user per minute across billed operations",
    )

    model_config = SettingsConfigDict(env_prefix="OPENCLAW_", env_file=".env", extra="ignore")

    def resolve_gateway_state_dir(self, *, portal_role: str) -> Path:
        """Return Gateway state directory for the given portal role."""
        if portal_role == "ADMIN":
            if self.gateway_state_dir:
                return Path(self.gateway_state_dir)
        else:
            if self.gateway_portal_state_dir:
                return Path(self.gateway_portal_state_dir)
            if self.gateway_state_dir:
                return Path(self.gateway_state_dir)
        env_dir = os.environ.get("OPENCLAW_STATE_DIR")
        if env_dir:
            return Path(env_dir)
        return Path.home() / ".openclaw"

    def resolve_gateway_agent_id(self, *, portal_role: str) -> str:
        if portal_role == "ADMIN":
            return self.gateway_admin_agent_id
        return self.gateway_portal_agent_id


settings = Settings()
