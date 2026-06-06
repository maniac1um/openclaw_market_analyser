import json
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.utils.url_validation import validate_public_http_url


class NewsLibraryIn(BaseModel):
    keyword: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1, max_length=20_000)
    source_url: str = Field(min_length=1, max_length=2000)
    title: str | None = Field(default=None, max_length=500)
    source_name: str | None = Field(default=None, max_length=200)
    published_at: datetime | None = None

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, value: str) -> str:
        return validate_public_http_url(value)


class NewsLibraryCreated(BaseModel):
    id: int
    created_at: datetime


class NewsLibraryItem(BaseModel):
    id: int
    keyword: str
    summary: str
    source_url: str
    title: str | None = None
    source_name: str | None = None
    published_at: datetime | None = None
    created_at: datetime
