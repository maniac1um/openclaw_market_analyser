from dataclasses import dataclass
from datetime import datetime


@dataclass
class Subscription:
    id: str
    user_id: str
    plan: str
    status: str
    current_period_end: datetime | None
    created_at: datetime
