from app.core.config import settings

_WEAK_API_KEYS = frozenset({"dev-openclaw-key", "changeme", "replace_me"})
_WEAK_HMAC_SECRETS = frozenset({"dev-secret", "changeme", "replace_me"})
_WEAK_JWT_SECRETS = frozenset({"dev-jwt-secret-change-me-in-production", "changeme", "replace_me"})


def validate_security_config() -> None:
    """Fail fast when production_mode is enabled with insecure defaults."""
    if not settings.production_mode:
        return

    api_key = (settings.openclaw_api_key or "").strip()
    if not api_key or api_key.lower() in _WEAK_API_KEYS or len(api_key) < 16:
        raise RuntimeError(
            "OPENCLAW_PRODUCTION=true requires a strong OPENCLAW_OPENCLAW_API_KEY (>=16 chars, not a dev default)."
        )

    hmac_secret = (settings.openclaw_hmac_secret or "").strip()
    if not hmac_secret or hmac_secret.lower() in _WEAK_HMAC_SECRETS or len(hmac_secret) < 16:
        raise RuntimeError(
            "OPENCLAW_PRODUCTION=true requires a strong OPENCLAW_OPENCLAW_HMAC_SECRET (>=16 chars, not a dev default)."
        )

    jwt_secret = (settings.jwt_secret or "").strip()
    if not jwt_secret or jwt_secret.lower() in _WEAK_JWT_SECRETS or len(jwt_secret) < 32:
        raise RuntimeError(
            "OPENCLAW_PRODUCTION=true requires a strong OPENCLAW_JWT_SECRET (>=32 chars, not a dev default)."
        )

    if not settings.cookie_secure:
        raise RuntimeError(
            "OPENCLAW_PRODUCTION=true requires OPENCLAW_COOKIE_SECURE=true for refresh token cookies."
        )

    if not settings.database_url:
        raise RuntimeError(
            "OPENCLAW_PRODUCTION=true requires OPENCLAW_DATABASE_URL for shared rate limiting and multi-user auth."
        )

    from app.db import user_queries as uq

    if uq.bootstrap_admin_uses_default_password():
        raise RuntimeError(
            "OPENCLAW_PRODUCTION=true requires changing the bootstrap admin password from the dev default."
        )

    if not settings.openclaw_enable_signature:
        raise RuntimeError(
            "OPENCLAW_PRODUCTION=true requires OPENCLAW_OPENCLAW_ENABLE_SIGNATURE=true for report ingest."
        )

    if settings.git_auto_push:
        raise RuntimeError(
            "OPENCLAW_PRODUCTION=true requires OPENCLAW_GIT_AUTO_PUSH=false; use a controlled deploy pipeline."
        )

    if settings.chat_enabled_for_user and not settings.gateway_portal_state_dir:
        raise RuntimeError(
            "OPENCLAW_PRODUCTION=true with OPENCLAW_CHAT_ENABLED_FOR_USER=true requires "
            "OPENCLAW_GATEWAY_PORTAL_STATE_DIR (restricted portal Gateway device credentials)."
        )

    if settings.portal_embed_api_key_in_spa:
        raise RuntimeError(
            "OPENCLAW_PRODUCTION=true requires OPENCLAW_PORTAL_EMBED_API_KEY_IN_SPA=false."
        )

    if settings.expose_openapi:
        raise RuntimeError(
            "OPENCLAW_PRODUCTION=true requires OPENCLAW_EXPOSE_OPENAPI=false."
        )

    if settings.legacy_api_key_enabled:
        raise RuntimeError(
            "OPENCLAW_PRODUCTION=true requires OPENCLAW_LEGACY_API_KEY_ENABLED=false."
        )

    if settings.allow_registration:
        raise RuntimeError(
            "OPENCLAW_PRODUCTION=true requires OPENCLAW_ALLOW_REGISTRATION=false."
        )

    if settings.first_user_is_admin:
        raise RuntimeError(
            "OPENCLAW_PRODUCTION=true requires OPENCLAW_FIRST_USER_IS_ADMIN=false."
        )

    if settings.demo_seed_enabled:
        raise RuntimeError(
            "OPENCLAW_PRODUCTION=true requires OPENCLAW_DEMO_SEED_ENABLED=false."
        )

    weak_db_markers = ("openclaw_dev", "replace_me")
    for label, dsn in (
        ("OPENCLAW_DATABASE_URL", settings.database_url),
        ("OPENCLAW_MONITORING_DATABASE_URL", settings.monitoring_database_url),
        ("OPENCLAW_NEWS_DATABASE_URL", settings.news_database_url),
    ):
        if dsn and any(marker in dsn.lower() for marker in weak_db_markers):
            raise RuntimeError(
                f"OPENCLAW_PRODUCTION=true requires strong credentials in {label} (dev defaults detected)."
            )
