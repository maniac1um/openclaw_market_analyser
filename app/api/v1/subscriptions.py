from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.core.security import CurrentUser
from app.db import subscription_queries as sub_q
from app.schemas.subscription import SubscriptionResponse

router = APIRouter(tags=["subscriptions"])


@router.get("/public/subscriptions", response_model=SubscriptionResponse, summary="当前订阅")
def get_subscription(user: CurrentUser) -> SubscriptionResponse:
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="User database is not configured")
    sub = sub_q.get_or_create_subscription(str(user.id))
    return SubscriptionResponse(**sub_q.subscription_to_dict(sub))


@router.post("/public/subscriptions/upgrade", response_model=SubscriptionResponse, summary="升级为 Pro")
def upgrade_subscription(user: CurrentUser) -> SubscriptionResponse:
    from app.db.demo_guard import reject_demo_write

    if not settings.database_url:
        raise HTTPException(status_code=503, detail="User database is not configured")
    reject_demo_write(user)
    sub = sub_q.upgrade_subscription(str(user.id))
    return SubscriptionResponse(**sub_q.subscription_to_dict(sub))


@router.post("/public/subscriptions/cancel", response_model=SubscriptionResponse, summary="取消订阅")
def cancel_subscription(user: CurrentUser) -> SubscriptionResponse:
    from app.db.demo_guard import reject_demo_write

    if not settings.database_url:
        raise HTTPException(status_code=503, detail="User database is not configured")
    reject_demo_write(user)
    try:
        sub = sub_q.cancel_subscription(str(user.id))
    except KeyError:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return SubscriptionResponse(**sub_q.subscription_to_dict(sub))
