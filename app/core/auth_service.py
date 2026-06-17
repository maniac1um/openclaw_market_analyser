"""Authentication: password hashing, JWT, registration, login."""

from __future__ import annotations

import re
import secrets
import time
from dataclasses import dataclass

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.rate_limit import count as rate_limit_count, record as rate_limit_record
from app.db import user_queries as uq
from app.db.query_context import ADMIN_ROLE, LEGACY_ADMIN_USER_ID, QueryContext, USER_ROLE
from app.db.user_models import User

_ph = PasswordHasher()
# Allow bootstrap/dev addresses such as admin@localhost (no TLD required).
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+$")

REFRESH_COOKIE = "openclaw_refresh"


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def validate_password_strength(password: str) -> None:
    if len(password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise HTTPException(status_code=422, detail="Password must contain letters and digits")


def validate_username(username: str) -> None:
    u = username.strip()
    if len(u) < 3 or len(u) > 32:
        raise HTTPException(status_code=422, detail="Username must be 3-32 characters")
    if not re.match(r"^[a-zA-Z0-9_-]+$", u):
        raise HTTPException(status_code=422, detail="Username may only contain letters, digits, _ and -")


def is_valid_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(email.strip()))


def validate_email(email: str) -> None:
    if not is_valid_email(email):
        raise HTTPException(status_code=422, detail="Invalid email address")


def _check_login_rate_limit(key: str) -> None:
    window = float(settings.login_lockout_seconds)
    bucket = f"login-fail:{key}"
    if rate_limit_count(bucket, window_seconds=window) >= settings.login_max_attempts:
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")


def _record_login_failure(key: str) -> None:
    rate_limit_record(f"login-fail:{key}", window_seconds=float(settings.login_lockout_seconds))


def user_to_public(user: User) -> dict:
    from app.db.demo_guard import is_demo_user
    from app.db.token_queries import get_user_balance_detail

    balance_detail = get_user_balance_detail(user.id)
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "role": user.role,
        "status": user.status,
        "is_demo": is_demo_user(user),
        "token_balance": balance_detail["balance"],
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
    }


def create_access_token(user: User) -> str:
    payload = {
        "sub": user.id,
        "role": user.role,
        "email": user.email,
        "username": user.username,
        "type": "access",
        "exp": int(time.time()) + settings.jwt_access_ttl_seconds,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


def issue_tokens(user: User, *, ip: str | None = None, user_agent: str | None = None) -> TokenPair:
    access = create_access_token(user)
    refresh = secrets.token_urlsafe(48)
    uq.create_session(
        user_id=user.id,
        refresh_token=refresh,
        ttl_seconds=settings.jwt_refresh_ttl_seconds,
        ip_address=ip,
        user_agent=user_agent,
    )
    return TokenPair(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.jwt_access_ttl_seconds,
    )


def refresh_access_token(refresh_token: str) -> tuple[TokenPair, User]:
    user = uq.get_session_user(refresh_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    uq.revoke_session(refresh_token)
    tokens = issue_tokens(user)
    return tokens, user


def register_user(*, email: str, username: str, password: str) -> tuple[User, TokenPair]:
    if not settings.allow_registration:
        raise HTTPException(status_code=403, detail="Registration is disabled")
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="User database is not configured")

    validate_email(email)
    validate_username(username)
    validate_password_strength(password)

    from app.db.demo_guard import is_demo_email

    if is_demo_email(email):
        raise HTTPException(status_code=409, detail="该邮箱为演示账号保留，请使用其他邮箱注册")

    uq.ensure_user_tables()
    if uq.get_user_by_email(email):
        raise HTTPException(status_code=409, detail="Email already registered")
    if uq.get_user_by_username(username):
        raise HTTPException(status_code=409, detail="Username already taken")

    password_hash = hash_password(password)
    user = uq.register_new_user(email=email, username=username, password_hash=password_hash)
    tokens = issue_tokens(user)
    return user, tokens


def login_user(*, email: str, password: str, ip: str | None = None) -> tuple[User, TokenPair]:
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="User database is not configured")

    rate_key = f"{uq.normalize_email(email)}:{ip or 'unknown'}"
    _check_login_rate_limit(rate_key)

    user = uq.get_user_by_email(email)
    if not user or user.status != "active":
        _record_login_failure(rate_key)
        raise HTTPException(status_code=401, detail="Invalid email or password")

    stored_hash = uq.get_password_hash(user.id)
    if not stored_hash or not verify_password(stored_hash, password):
        _record_login_failure(rate_key)
        raise HTTPException(status_code=401, detail="Invalid email or password")

    uq.update_last_login(user.id)
    user = uq.get_user_by_id(user.id) or user
    tokens = issue_tokens(user, ip=ip)
    return user, tokens


def logout_user(refresh_token: str | None) -> None:
    if refresh_token:
        uq.revoke_session(refresh_token)


def user_from_access_payload(payload: dict) -> User | None:
    user_id = payload.get("sub")
    if not user_id:
        return None
    return uq.get_user_by_id(str(user_id))


def legacy_admin_context() -> QueryContext:
    admin_id = LEGACY_ADMIN_USER_ID
    if settings.database_url:
        try:
            uq.ensure_bootstrap_admin()
            with uq._connect() as conn, conn.cursor() as cur:  # noqa: SLF001
                cur.execute("SELECT id FROM users WHERE role = 'ADMIN' ORDER BY created_at ASC LIMIT 1")
                row = cur.fetchone()
                if row:
                    admin_id = str(row[0])
        except Exception:
            pass
    return QueryContext(user_id=admin_id, role=ADMIN_ROLE)


def resolve_user_from_api_key(raw_key: str | None) -> User | None:
    if not raw_key:
        return None
    if not settings.database_url:
        return None
    return uq.get_user_by_api_key(raw_key)


def user_to_context(user: User) -> QueryContext:
    return QueryContext(user_id=user.id, role=user.role)
