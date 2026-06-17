import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

_WEAK_API_KEYS = frozenset({"dev-openclaw-key", "changeme", "replace_me"})
_WEAK_HMAC_SECRETS = frozenset({"dev-secret", "changeme", "replace_me"})
_WEAK_JWT_SECRETS = frozenset({"dev-jwt-secret-change-me-in-production", "changeme", "replace_me"})


def uses_weak_secrets() -> bool:
    api_key = (settings.openclaw_api_key or "").strip()
    if not api_key or api_key.lower() in _WEAK_API_KEYS or len(api_key) < 16:
        return True
    hmac_secret = (settings.openclaw_hmac_secret or "").strip()
    if not hmac_secret or hmac_secret.lower() in _WEAK_HMAC_SECRETS or len(hmac_secret) < 16:
        return True
    jwt_secret = (settings.jwt_secret or "").strip()
    if not jwt_secret or jwt_secret.lower() in _WEAK_JWT_SECRETS or len(jwt_secret) < 32:
        return True
    return False


def _bind_accepts_public_clients() -> bool:
    host = (settings.bind_host or "").strip().lower()
    return host in {"", "0.0.0.0", "::"}


def validate_security_config() -> None:
    """Fail fast when production_mode is enabled with insecure defaults."""
    if settings.production_mode:
        _validate_production_config()
        return
    _validate_persistent_dev_deployment()


def _validate_production_config() -> None:
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

    if settings.payments_simulated_confirm_enabled:
        raise RuntimeError(
            "OPENCLAW_PRODUCTION=true requires OPENCLAW_PAYMENTS_SIMULATED_CONFIRM_ENABLED=false."
        )

    if settings.subscriptions_simulated_upgrade_enabled:
        raise RuntimeError(
            "OPENCLAW_PRODUCTION=true requires OPENCLAW_SUBSCRIPTIONS_SIMULATED_UPGRADE_ENABLED=false."
        )

    if settings.admin_cross_tenant_access:
        raise RuntimeError(
            "OPENCLAW_PRODUCTION=true requires OPENCLAW_ADMIN_CROSS_TENANT_ACCESS=false."
        )

    if settings.monitoring_allow_server_scrape:
        raise RuntimeError(
            "OPENCLAW_PRODUCTION=true requires OPENCLAW_MONITORING_ALLOW_SERVER_SCRAPE=false."
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


def _validate_persistent_dev_deployment() -> None:
    """Block accidental public deployments that keep dev defaults."""
    if not settings.database_url:
        return

    insecure = uses_weak_secrets() or not settings.openclaw_enable_signature
    if insecure and not settings.allow_insecure_dev_deployment:
        raise RuntimeError(
            "Persistent deployment (OPENCLAW_DATABASE_URL set) still uses dev-default secrets or "
            "unsigned report ingest. Set OPENCLAW_PRODUCTION=true with strong secrets, or "
            "OPENCLAW_ALLOW_INSECURE_DEV_DEPLOYMENT=true for isolated local labs only."
        )

    if settings.demo_seed_enabled and _bind_accepts_public_clients() and not settings.demo_allow_public_bind:
        raise RuntimeError(
            "Demo seed is enabled while bind_host accepts public clients. "
            "Set OPENCLAW_DEMO_SEED_ENABLED=false, bind to loopback, or "
            "OPENCLAW_DEMO_ALLOW_PUBLIC_BIND=true for isolated demos only."
        )

    if settings.portal_embed_api_key_in_spa:
        logger.error(
            "OPENCLAW_PORTAL_EMBED_API_KEY_IN_SPA=true is deprecated and ignored; "
            "use per-user API keys or JWT instead."
        )

    if uses_weak_secrets():
        logger.warning(
            "Dev-default API/JWT/HMAC secrets are in use. Do not expose this instance to untrusted networks."
        )

    if settings.trust_x_forwarded_for:
        logger.warning(
            "OPENCLAW_TRUST_X_FORWARDED_FOR=true: ensure the app is only reachable via a trusted reverse proxy."
        )

    if settings.rate_limit_enabled and not settings.database_url:
        logger.warning(
            "Rate limiting uses in-process counters without OPENCLAW_DATABASE_URL; limits do not span workers."
        )
