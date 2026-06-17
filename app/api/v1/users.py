from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.core.security import CurrentUser
from app.db.token_queries import get_user_balance_detail
from app.schemas.balance import UserBalanceResponse

router = APIRouter(tags=["users"])


@router.get("/public/users/balance", response_model=UserBalanceResponse, summary="Token 余额")
def get_user_balance(user: CurrentUser) -> UserBalanceResponse:
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="User database is not configured")
    detail = get_user_balance_detail(str(user.id))
    return UserBalanceResponse(**detail)
