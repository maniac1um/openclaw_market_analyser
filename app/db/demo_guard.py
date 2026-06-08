"""Demo trial user guard — read-only portal writes."""

from __future__ import annotations

from fastapi import HTTPException

from app.core.config import settings
from app.db.user_models import User


def is_demo_email(email: str) -> bool:
    return email.strip().lower() == settings.demo_user_email.strip().lower()


def is_demo_user(user: User) -> bool:
    return is_demo_email(user.email)


def reject_demo_write(user: User) -> None:
    if is_demo_user(user):
        raise HTTPException(
            status_code=403,
            detail="演示账号为只读，请注册正式账号以进行此操作",
        )
