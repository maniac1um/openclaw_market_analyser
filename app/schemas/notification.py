from pydantic import BaseModel, Field


class NotificationItem(BaseModel):
    id: str
    title: str
    content: str
    notification_type: str | None = None
    created_at: str | None = None
    read: bool


class NotificationListResponse(BaseModel):
    notifications: list[NotificationItem]
    unread_count: int


class NotificationCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=4000)
    target: str = Field(default="all", description="'all' or target user_id UUID")
    notification_type: str | None = Field(default=None, max_length=64)


class NotificationCreatedResponse(BaseModel):
    id: str
    title: str
    content: str
    target: str
    notification_type: str | None = None
    created_at: str | None = None


class MarkReadResponse(BaseModel):
    ok: bool
    unread_count: int
