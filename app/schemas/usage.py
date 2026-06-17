from typing import Any

from pydantic import BaseModel, Field


class UsageSeriesPoint(BaseModel):
    bucket: str
    tokens: int


class UsageStatsResponse(BaseModel):
    today: int
    total: int
    range: str
    range_total: int = Field(description="Sum of tokens in the selected time range")
    series: list[UsageSeriesPoint]


class UsageEntryMetadata(BaseModel):
    type: str | None = None
    action: str | None = None
    keyword: str | None = None


class UsageEntry(BaseModel):
    id: str
    tokens_used: int
    endpoint: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    label: str
    created_at: str


class UsageEntriesResponse(BaseModel):
    range: str
    entries: list[UsageEntry]
