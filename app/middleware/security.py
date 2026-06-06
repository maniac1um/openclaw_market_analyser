import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from starlette.requests import ClientDisconnect

from app.core.config import settings


class BodyTooLarge(Exception):
    pass


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' ws: wss:; frame-ancestors 'none'",
        )
        return response


class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_bytes: int) -> None:
        super().__init__(app)
        self._max_bytes = max(1, int(max_bytes))

    def _too_large_response(self) -> JSONResponse:
        return JSONResponse(
            status_code=413,
            content={"detail": f"Request body too large (max {self._max_bytes} bytes)"},
        )

    @staticmethod
    def _wrap_receive_with_limit(request: Request, max_bytes: int):
        received = 0
        original_receive = request.receive

        async def limited_receive():
            nonlocal received
            message = await original_receive()
            if message["type"] == "http.request":
                chunk = message.get("body", b"") or b""
                received += len(chunk)
                if received > max_bytes:
                    raise BodyTooLarge()
            return message

        return Request(request.scope, limited_receive)

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method not in {"POST", "PUT", "PATCH"}:
            return await call_next(request)

        content_length = request.headers.get("content-length")
        has_known_length = False
        if content_length is not None:
            try:
                has_known_length = True
                if int(content_length) > self._max_bytes:
                    return self._too_large_response()
            except ValueError:
                has_known_length = False

        wrapped = request
        if not has_known_length:
            wrapped = self._wrap_receive_with_limit(request, self._max_bytes)

        try:
            return await call_next(wrapped)
        except BodyTooLarge:
            return self._too_large_response()
        except ClientDisconnect:
            return self._too_large_response()


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    @staticmethod
    def _client_key(request: Request) -> str:
        if settings.trust_x_forwarded_for:
            forwarded = request.headers.get("x-forwarded-for")
            if forwarded:
                return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    def _allow(self, key: str, *, limit: int) -> bool:
        now = time.monotonic()
        window_start = now - 60.0
        bucket = self._hits[key]
        while bucket and bucket[0] < window_start:
            bucket.popleft()
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True

    async def dispatch(self, request: Request, call_next) -> Response:
        if not settings.rate_limit_enabled:
            return await call_next(request)

        path = request.url.path
        if path in {"/healthz", "/healthz/db"}:
            return await call_next(request)

        client = self._client_key(request)
        is_write = request.method in {"POST", "PUT", "PATCH", "DELETE"}
        bucket_key = f"{client}:{'write' if is_write else 'read'}"
        limit = (
            max(1, int(settings.rate_limit_write_per_minute))
            if is_write
            else max(1, int(settings.rate_limit_read_per_minute))
        )
        if not self._allow(bucket_key, limit=limit):
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
        return await call_next(request)
