from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.security import verify_csrf_for_cookie_writes

_CSRF_EXEMPT_PREFIXES = (
    "/api/v1/public/auth/login",
    "/api/v1/public/auth/register",
    "/api/v1/public/auth/refresh",
    "/api/v1/public/auth/session",
    "/api/v1/openclaw/",
    "/healthz",
)


class CsrfMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            path = request.url.path.rstrip("/") or "/"
            if not any(path.startswith(prefix.rstrip("/")) for prefix in _CSRF_EXEMPT_PREFIXES):
                verify_csrf_for_cookie_writes(request)
        return await call_next(request)
