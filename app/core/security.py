import hashlib
import hmac
import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status

from app.core.auth_service import (
    REFRESH_COOKIE,
    decode_access_token,
    legacy_admin_context,
    resolve_user_from_api_key,
    user_from_access_payload,
    user_to_context,
)
from app.core.config import settings
from app.db.query_context import QueryContext
from app.db.user_models import User

PORTAL_SESSION_COOKIE = "openclaw_portal_session"
PORTAL_SESSION_MAX_AGE_SECONDS = 86400
CSRF_COOKIE = "openclaw_csrf"
CSRF_HEADER = "X-CSRF-Token"


def is_valid_api_key(api_key: str | None) -> bool:
    if not api_key:
        return False
    if settings.database_url:
        user = resolve_user_from_api_key(api_key)
        if user:
            return True
    expected = settings.openclaw_api_key.encode("utf-8")
    provided = api_key.encode("utf-8")
    return secrets.compare_digest(provided, expected)


def verify_api_key(x_api_key: str | None = Header(default=None)) -> User:
    user = resolve_user_from_api_key(x_api_key)
    if user:
        return user
    if (
        settings.legacy_api_key_enabled
        and not settings.production_mode
        and x_api_key
        and secrets.compare_digest(x_api_key.encode("utf-8"), settings.openclaw_api_key.encode("utf-8"))
    ):
        ctx = legacy_admin_context()
        return User(
            id=ctx.user_id,
            email="admin@localhost",
            username="admin",
            role=ctx.role,
            status="active",
            created_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            updated_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        )
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


def portal_session_token() -> str:
    return hmac.new(
        key=settings.openclaw_hmac_secret.encode("utf-8"),
        msg=b"openclaw-portal-session-v1",
        digestmod=hashlib.sha256,
    ).hexdigest()


def is_valid_portal_session(cookie_value: str | None) -> bool:
    if settings.production_mode:
        return False
    if not cookie_value:
        return False
    return secrets.compare_digest(cookie_value, portal_session_token())


def issue_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def set_csrf_cookie(response, token: str) -> None:
    from starlette.responses import Response

    assert isinstance(response, Response)
    kwargs: dict = {
        "key": CSRF_COOKIE,
        "value": token,
        "httponly": False,
        "samesite": "strict",
        "max_age": settings.jwt_refresh_ttl_seconds,
        "path": "/",
        "secure": settings.cookie_secure,
    }
    if settings.cookie_domain:
        kwargs["domain"] = settings.cookie_domain
    response.set_cookie(**kwargs)


def clear_csrf_cookie(response) -> None:
    from starlette.responses import Response

    assert isinstance(response, Response)
    kwargs: dict = {"key": CSRF_COOKIE, "path": "/"}
    if settings.cookie_domain:
        kwargs["domain"] = settings.cookie_domain
    response.delete_cookie(**kwargs)


def _uses_cookie_session_auth(request: Request) -> bool:
    if _bearer_token(request) or request.headers.get("x-api-key"):
        return False
    return bool(request.cookies.get(REFRESH_COOKIE))


def verify_csrf_for_cookie_writes(request: Request) -> None:
    if not _uses_cookie_session_auth(request):
        return
    header = request.headers.get(CSRF_HEADER) or request.headers.get("x-csrf-token")
    cookie = request.cookies.get(CSRF_COOKIE)
    if not header or not cookie or not secrets.compare_digest(header, cookie):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token required")


def _bearer_token(request: Request) -> str | None:
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


def _user_from_request(request: Request) -> User | None:
    token = _bearer_token(request)
    if token:
        payload = decode_access_token(token)
        if payload and payload.get("type") == "access":
            user = user_from_access_payload(payload)
            if user and user.status == "active":
                return user
    api_key = request.headers.get("x-api-key")
    if api_key:
        return resolve_user_from_api_key(api_key)
    refresh = request.cookies.get(REFRESH_COOKIE)
    if refresh:
        from app.db import user_queries as uq

        return uq.get_session_user(refresh)
    if is_valid_portal_session(request.cookies.get(PORTAL_SESSION_COOKIE)):
        ctx = legacy_admin_context()
        from app.db import user_queries as uq

        user = uq.get_user_by_id(ctx.user_id)
        if user:
            return user
        return User(
            id=ctx.user_id,
            email="admin@localhost",
            username="admin",
            role=ctx.role,
            status="active",
            created_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            updated_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        )
    return None


def get_current_user(request: Request) -> User:
    user = _user_from_request(request)
    if not user or user.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user


def resolve_query_context(request: Request) -> QueryContext:
    user = _user_from_request(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user_to_context(user)


def require_role(*roles: str):
    def dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return dep


CurrentUser = Annotated[User, Depends(get_current_user)]
QueryCtx = Annotated[QueryContext, Depends(resolve_query_context)]
AdminUser = Annotated[User, Depends(require_role("ADMIN"))]


def verify_portal_write_auth(
    request: Request,
    x_api_key: str | None = Header(default=None),
) -> User:
    user = _user_from_request(request)
    if user and user.status == "active":
        return user
    if x_api_key:
        try:
            return verify_api_key(x_api_key)
        except HTTPException:
            pass
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing portal credentials")


def verify_user_api_key(x_api_key: str | None = Header(default=None)) -> User:
    return verify_api_key(x_api_key)


def is_websocket_authorized(
    *,
    header_api_key: str | None,
    portal_cookie: str | None,
    bearer_token: str | None = None,
    refresh_cookie: str | None = None,
) -> bool:
    return resolve_websocket_user(
        header_api_key=header_api_key,
        portal_cookie=portal_cookie,
        bearer_token=bearer_token,
        refresh_cookie=refresh_cookie,
    ) is not None


def resolve_websocket_user(
    *,
    header_api_key: str | None,
    portal_cookie: str | None,
    bearer_token: str | None = None,
    refresh_cookie: str | None = None,
) -> User | None:
    if bearer_token:
        payload = decode_access_token(bearer_token)
        if payload and payload.get("type") == "access":
            user = user_from_access_payload(payload)
            if user and user.status == "active":
                return user
    if refresh_cookie and settings.database_url:
        from app.db import user_queries as uq

        user = uq.get_session_user(refresh_cookie)
        if user and user.status == "active":
            return user
    if header_api_key:
        user = resolve_user_from_api_key(header_api_key)
        if user and user.status == "active":
            return user
    if is_valid_portal_session(portal_cookie):
        ctx = legacy_admin_context()
        from app.db import user_queries as uq

        user = uq.get_user_by_id(ctx.user_id)
        if user and user.status == "active":
            return user
        return User(
            id=ctx.user_id,
            email="admin@localhost",
            username="admin",
            role=ctx.role,
            status="active",
            created_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            updated_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        )
    return None


def verify_optional_signature(payload_bytes: bytes, x_signature: str | None) -> None:
    if not settings.openclaw_enable_signature:
        return
    if not x_signature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing signature")

    expected = hmac.new(
        key=settings.openclaw_hmac_secret.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, x_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")
