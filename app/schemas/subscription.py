from pydantic import BaseModel, Field


class SubscriptionResponse(BaseModel):
    id: str
    user_id: str
    plan: str = Field(description="free or pro")
    status: str = Field(description="active or cancelled")
    current_period_end: str | None = None
    created_at: str | None = None
