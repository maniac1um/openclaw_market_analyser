from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.utils.url_validation import validate_public_http_url

_MAX_ITEMS = 200
_MAX_SOURCES = 50


class ReportInsights(BaseModel):
    sentiment: Literal["bullish", "bearish", "neutral"] | None = Field(
        default=None, description="情绪方向：利多/利空/中性"
    )
    risk_level: Literal["low", "medium", "high"] | None = Field(default=None, description="风险等级")
    market_impact: str | None = Field(default=None, max_length=2000, description="市场影响摘要")
    confidence: Literal["低", "中", "高"] | None = Field(default=None, description="结论置信度")
    forecast: str | None = Field(default=None, max_length=500, description="短期走势预判")


class TimeRange(BaseModel):
    start: datetime = Field(description="采集时间范围起点（ISO 8601）")
    end: datetime = Field(description="采集时间范围终点（ISO 8601）")


class NewsItem(BaseModel):
    title: str = Field(min_length=1, max_length=500, description="新闻标题")
    source: str = Field(min_length=1, max_length=200, description="来源站点或媒体名")
    url: str = Field(min_length=1, max_length=2000, description="原文链接")
    published_at: datetime = Field(description="发布时间（ISO 8601）")
    price: float | None = Field(default=None, description="提取到的价格（可选）")
    currency: str | None = Field(default=None, max_length=16, description="币种（可选）")
    summary: str | None = Field(default=None, max_length=4000, description="摘要（可选）")

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        return validate_public_http_url(value)


class OpenClawReportIn(BaseModel):
    task_id: str = Field(min_length=1, max_length=128, description="OpenClaw 任务 ID")
    keyword: str = Field(min_length=1, max_length=200, description="查询关键词，例如：羽毛球")
    time_range: TimeRange = Field(description="采集时间范围")
    sources: list[str] = Field(min_length=0, max_length=_MAX_SOURCES, description="来源列表")
    items: list[NewsItem] = Field(min_length=0, max_length=_MAX_ITEMS, description="抽取后的结构化条目")
    analysis: str = Field(min_length=1, max_length=50_000, description="模型生成的分析结论")
    insights: ReportInsights | None = Field(default=None, description="结构化洞察（可选，用于 Dashboard 卡片）")
    generated_title: str = Field(min_length=1, max_length=500, description="生成的报告标题")
    generated_at: datetime = Field(description="报告生成时间（ISO 8601）")

    @field_validator("sources")
    @classmethod
    def validate_sources(cls, values: list[str]) -> list[str]:
        out: list[str] = []
        for item in values:
            text = str(item).strip()
            if not text:
                continue
            if len(text) > 200:
                raise ValueError("each source name must be <= 200 characters")
            out.append(text)
        return out


class IngestAccepted(BaseModel):
    ingest_id: str = Field(description="入站记录 ID")
    status: str = Field(description="当前状态，例如 queued")


class IngestStatusResponse(BaseModel):
    ingest_id: str = Field(description="入站记录 ID")
    request_id: str = Field(description="请求幂等键")
    task_id: str = Field(description="OpenClaw 任务 ID")
    status: str = Field(description="任务状态：queued/processing/published/failed")
    error: str | None = Field(default=None, description="失败原因")
