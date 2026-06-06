from app.core.config import settings

_WEAK_API_KEYS = frozenset({"dev-openclaw-key", "changeme", "replace_me"})
_WEAK_HMAC_SECRETS = frozenset({"dev-secret", "changeme", "replace_me"})


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

    if not settings.openclaw_enable_signature:
        raise RuntimeError(
            "OPENCLAW_PRODUCTION=true requires OPENCLAW_OPENCLAW_ENABLE_SIGNATURE=true for report ingest."
        )

    if settings.git_auto_push:
        raise RuntimeError(
            "OPENCLAW_PRODUCTION=true requires OPENCLAW_GIT_AUTO_PUSH=false; use a controlled deploy pipeline."
        )

    if settings.portal_embed_api_key_in_spa:
        raise RuntimeError(
            "OPENCLAW_PRODUCTION=true requires OPENCLAW_PORTAL_EMBED_API_KEY_IN_SPA=false."
        )

    if settings.expose_openapi:
        raise RuntimeError(
            "OPENCLAW_PRODUCTION=true requires OPENCLAW_EXPOSE_OPENAPI=false."
        )
