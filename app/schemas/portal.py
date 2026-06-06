from pydantic import BaseModel, Field, field_validator

from app.utils.path_safety import parse_uuid


class BulkDeleteRequest(BaseModel):
    ingest_ids: list[str] = Field(min_length=1, max_length=100)

    @field_validator("ingest_ids")
    @classmethod
    def validate_ingest_ids(cls, values: list[str]) -> list[str]:
        out: list[str] = []
        for item in values:
            canonical = parse_uuid(item)
            if not canonical:
                raise ValueError(f"invalid ingest_id UUID: {item}")
            out.append(canonical)
        return out


class ExternalSchedulerHeartbeatRequest(BaseModel):
    job_name: str = Field(min_length=1, max_length=120)
    status: str = Field(default="ok", max_length=32)
    monitor_id: str | None = Field(default=None, max_length=64)
    message: str | None = Field(default=None, max_length=2000)


class WorkflowBootstrapRequest(BaseModel):
    keyword: str = Field(min_length=1, max_length=100)
    cadence: str = Field(default="daily", max_length=20)
    source_profile: str = Field(default="auto", max_length=32)
    platforms: list[str] = Field(default_factory=lambda: ["news"], max_length=20)
    candidate_count: int = Field(default=10, ge=1, le=60)


class WorkflowTriggerRequest(BaseModel):
    monitor_id: str = Field(min_length=1, max_length=64)
    keyword: str | None = Field(default=None, max_length=200)
    keywords: list[str] | None = Field(default=None, max_length=20)
    window_days: int = Field(default=7, ge=1, le=365)
    news_hours: int = Field(default=72, ge=1, le=24 * 30)
    horizon: str = Field(default="24h", max_length=32)
    publish: bool = True


class ExternalSchedulerConfigRequest(BaseModel):
    job_name: str = Field(min_length=1, max_length=120)
    monitor_id: str = Field(min_length=1, max_length=64)
    cron_expr: str = Field(min_length=1, max_length=120)
    timezone: str = Field(default="Asia/Shanghai", max_length=64)
    enabled: bool = True
    retry_policy: str = Field(default="no-retry", max_length=32)
    notes: str | None = Field(default=None, max_length=2000)


class ExternalSchedulerToggleRequest(BaseModel):
    enabled: bool


class NewsBulkDeleteRequest(BaseModel):
    ids: list[int] = Field(min_length=1, max_length=100)


class NewsTriggerAnalysisRequest(BaseModel):
    monitor_id: str = Field(min_length=1, max_length=64)
    keyword: str | None = Field(default=None, max_length=200)
    window_days: int = Field(default=7, ge=1, le=365)
    news_hours: int = Field(default=72, ge=1, le=24 * 30)
    horizon: str = Field(default="24h", max_length=32)
    publish: bool = False
