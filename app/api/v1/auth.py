from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.core.auth_service import (
    REFRESH_COOKIE,
    issue_tokens,
    login_user,
    logout_user,
    refresh_access_token,
    register_user,
    user_to_public,
)
from app.core.config import settings
from app.core.security import CurrentUser, get_current_user, verify_user_api_key
from app.db import user_queries as uq
from app.db.user_models import User
from app.schemas.auth import (
    ApiKeyCreateRequest,
    ApiKeyCreatedResponse,
    ApiKeyListItem,
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    UserPublic,
)

router = APIRouter(tags=["auth"])


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        httponly=True,
        samesite="lax",
        max_age=settings.jwt_refresh_ttl_seconds,
        path="/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE, path="/")


@router.post("/public/auth/register", response_model=AuthResponse, summary="用户注册")
def auth_register(payload: RegisterRequest, response: Response) -> AuthResponse:
    user, tokens = register_user(email=payload.email, username=payload.username, password=payload.password)
    _set_refresh_cookie(response, tokens.refresh_token)
    return AuthResponse(
        user=UserPublic(**user_to_public(user)),
        access_token=tokens.access_token,
        expires_in=tokens.expires_in,
    )


@router.post("/public/auth/login", response_model=AuthResponse, summary="用户登录")
def auth_login(payload: LoginRequest, request: Request, response: Response) -> AuthResponse:
    ip = request.client.host if request.client else None
    user, tokens = login_user(email=payload.email, password=payload.password, ip=ip)
    _set_refresh_cookie(response, tokens.refresh_token)
    return AuthResponse(
        user=UserPublic(**user_to_public(user)),
        access_token=tokens.access_token,
        expires_in=tokens.expires_in,
    )


@router.post("/public/auth/refresh", response_model=AuthResponse, summary="刷新访问令牌")
def auth_refresh(request: Request, response: Response) -> AuthResponse:
    refresh = request.cookies.get(REFRESH_COOKIE)
    if not refresh:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    tokens, user = refresh_access_token(refresh)
    _set_refresh_cookie(response, tokens.refresh_token)
    return AuthResponse(
        user=UserPublic(**user_to_public(user)),
        access_token=tokens.access_token,
        expires_in=tokens.expires_in,
    )


@router.delete("/public/auth/logout", summary="退出登录")
def auth_logout(request: Request, response: Response) -> dict:
    refresh = request.cookies.get(REFRESH_COOKIE)
    logout_user(refresh)
    _clear_refresh_cookie(response)
    return {"ok": True}


@router.get("/public/auth/me", response_model=UserPublic, summary="当前用户信息")
def auth_me(user: CurrentUser) -> UserPublic:
    return UserPublic(**user_to_public(user))


@router.get("/public/auth/status", summary="认证状态")
def auth_status(request: Request) -> dict:
    from app.core.security import _user_from_request

    user = _user_from_request(request)
    if user:
        method = "jwt" if request.headers.get("authorization") else "api_key" if request.headers.get("x-api-key") else "cookie"
        return {"authenticated": True, "method": method, "user": user_to_public(user)}
    return {"authenticated": False, "method": None}


@router.post("/public/auth/session", summary="Legacy: API Key 换会话（兼容旧 SPA dev bootstrap）")
def auth_session_legacy(response: Response, user: User = Depends(verify_user_api_key)) -> dict:
    tokens = issue_tokens(user)
    _set_refresh_cookie(response, tokens.refresh_token)
    return {"ok": True, "expires_in_seconds": settings.jwt_refresh_ttl_seconds, "access_token": tokens.access_token}


@router.post("/public/auth/api-keys", response_model=ApiKeyCreatedResponse, summary="生成 OpenClaw API Key")
def auth_create_api_key(payload: ApiKeyCreateRequest, user: CurrentUser) -> ApiKeyCreatedResponse:
    raw, record = uq.create_api_key(user_id=user.id, label=payload.label)
    return ApiKeyCreatedResponse(
        id=record.id,
        key_prefix=record.key_prefix,
        label=record.label,
        api_key=raw,
    )


@router.get("/public/auth/api-keys", response_model=list[ApiKeyListItem], summary="列出 API Key")
def auth_list_api_keys(user: CurrentUser) -> list[ApiKeyListItem]:
    keys = uq.list_api_keys(user.id)
    return [
        ApiKeyListItem(
            id=k.id,
            key_prefix=k.key_prefix,
            label=k.label,
            created_at=k.created_at.isoformat(),
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
        )
        for k in keys
    ]


@router.delete("/public/auth/api-keys/{key_id}", summary="撤销 API Key")
def auth_revoke_api_key(key_id: str, user: CurrentUser) -> dict:
    ok = uq.revoke_api_key(user_id=user.id, key_id=key_id)
    if not ok:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"ok": True}
