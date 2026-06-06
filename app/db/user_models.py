from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: str
    email: str
    username: str
    role: str
    status: str
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None


@dataclass
class UserApiKey:
    id: str
    user_id: str
    key_prefix: str
    label: str
    created_at: datetime
    last_used_at: datetime | None = None
