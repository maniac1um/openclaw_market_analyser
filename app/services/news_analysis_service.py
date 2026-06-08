from datetime import datetime, timedelta, timezone

from fastapi import BackgroundTasks, HTTPException

from app.api.v1.openclaw import intake_service
from app.core.config import settings
from app.db.public_queries import list_news_library_from_db, monitor_accessible, require_public_news_db
from app.db.query_context import QueryContext
from app.schemas.report import OpenClawReportIn
from app.services.monitoring_service import MonitoringService
from app.utils.formatting import parse_iso_dt
from app.utils.sentiment import sentiment_from_text


def build_news_price_analysis(
    monitor_id: str,
    keyword: str | None,
    keywords: list[str] | None,
    window_days: int,
    news_hours: int,
    horizon: str,
    ctx: QueryContext,
) -> dict:
    if not settings.monitoring_database_url:
        raise HTTPException(status_code=503, detail="未配置 OPENCLAW_MONITORING_DATABASE_URL。")
    require_public_news_db()
    if not monitor_accessible(monitor_id, ctx):
        raise HTTPException(status_code=404, detail="Monitor not found")

    summary = MonitoringService(settings.monitoring_database_url).get_summary(
        monitor_id=monitor_id,
        window_days=window_days,
    )
    effective_keyword = (keyword or summary.get("keyword") or "").strip() or "未命名关键词"
    keywords_used = [str(x).strip() for x in (keywords or []) if str(x).strip()]
    if effective_keyword and effective_keyword not in keywords_used:
        keywords_used.insert(0, effective_keyword)
    if not keywords_used:
        keywords_used = [effective_keyword]

    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=max(1, news_hours))
    news_pool: list[dict] = []
    for kw in keywords_used:
        news_pool.extend(list_news_library_from_db(limit=180, keyword=kw, ctx=ctx))
    seen_ids: set[int] = set()
    seen_urls: set[str] = set()
    deduped_news: list[dict] = []
    for item in news_pool:
        iid = int(item.get("id") or 0)
        url = str(item.get("source_url") or "").strip()
        if iid and iid in seen_ids:
            continue
        if url and url in seen_urls:
            continue
        if iid:
            seen_ids.add(iid)
        if url:
            seen_urls.add(url)
        deduped_news.append(item)

    recent_news: list[dict] = []
    for item in deduped_news:
        ts = parse_iso_dt(item.get("published_at")) or parse_iso_dt(item.get("created_at"))
        if not ts:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if ts >= since:
            recent_news.append(item)
    recent_news.sort(
        key=lambda x: (parse_iso_dt(x.get("published_at")) or parse_iso_dt(x.get("created_at")) or now),
        reverse=True,
    )
    key_news = recent_news[:5]

    bullish = bearish = neutral = 0
    for row in key_news:
        txt = f"{row.get('title') or ''} {row.get('summary') or ''}"
        s = sentiment_from_text(txt)
        if s == "bullish":
            bullish += 1
        elif s == "bearish":
            bearish += 1
        else:
            neutral += 1

    min_price = summary.get("min_price")
    max_price = summary.get("max_price")
    latest_price = summary.get("latest_price")
    trend = "震荡"
    if isinstance(min_price, (int, float)) and isinstance(max_price, (int, float)) and isinstance(latest_price, (int, float)):
        mid = (float(min_price) + float(max_price)) / 2.0
        if latest_price > mid * 1.02:
            trend = "偏强"
        elif latest_price < mid * 0.98:
            trend = "偏弱"

    forecast = "震荡"
    if bullish > bearish:
        forecast = "上行"
    elif bearish > bullish:
        forecast = "下行"
    elif trend == "偏强":
        forecast = "上行"
    elif trend == "偏弱":
        forecast = "下行"

    priced_obs = int(summary.get("priced_observations") or 0)
    confidence = "低"
    if priced_obs >= 20 and len(key_news) >= 2:
        confidence = "高"
    elif priced_obs >= 5 and len(key_news) >= 1:
        confidence = "中"

    evidence_lines = []
    for row in key_news[:3]:
        evidence_lines.append(
            f"- {row.get('title') or '未命名新闻'} | {row.get('source_name') or '未知来源'} | {row.get('source_url') or '-'}"
        )
    news_evidence = "\n".join(evidence_lines) if evidence_lines else "- 最近窗口无高相关新增新闻。"
    analysis = (
        f"{effective_keyword} 在近{window_days}天价格区间为 {summary.get('min_price')}~{summary.get('max_price')}，"
        f"最新价格 {summary.get('latest_price')}，当前走势判断为{trend}。"
        f"结合近{news_hours}小时新闻（关键词：{'、'.join(keywords_used)}；利多{bullish} / 利空{bearish} / 中性{neutral}），"
        f"预测未来{horizon}倾向{forecast}，置信度{confidence}。"
        f"若后续出现与当前判断相反的高优先级事件，结论可能快速失效。\n\n关键新闻证据：\n{news_evidence}"
    )

    risk_level = "medium"
    if confidence == "低":
        risk_level = "high"
    elif confidence == "高" and forecast in ("上行", "下行"):
        risk_level = "low"

    sentiment = "neutral"
    if bullish > bearish:
        sentiment = "bullish"
    elif bearish > bullish:
        sentiment = "bearish"

    return {
        "monitor_id": monitor_id,
        "keyword": effective_keyword,
        "window_days": window_days,
        "news_hours": news_hours,
        "horizon": horizon,
        "summary": summary,
        "news_count": len(recent_news),
        "keywords_used": keywords_used,
        "key_news": key_news,
        "forecast": forecast,
        "confidence": confidence,
        "analysis": analysis,
        "insights": {
            "sentiment": sentiment,
            "risk_level": risk_level,
            "market_impact": f"价格{trend}，新闻情绪利多{bullish}/利空{bearish}",
            "confidence": confidence,
            "forecast": forecast,
        },
    }


def run_news_trigger_analysis(
    *,
    monitor_id: str,
    keyword: str | None,
    keywords: list[str] | None,
    window_days: int,
    news_hours: int,
    horizon: str,
    publish: bool,
    background_tasks: BackgroundTasks,
    user_id: str | None = None,
    ctx: QueryContext | None = None,
) -> dict:
    if ctx is None:
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication context required")
        ctx = QueryContext(user_id=user_id, role="USER")
    result = build_news_price_analysis(
        monitor_id=monitor_id,
        keyword=keyword,
        keywords=keywords,
        window_days=window_days,
        news_hours=news_hours,
        horizon=horizon,
        ctx=ctx,
    )
    ingest_id = None
    ingest_status = None
    if publish:
        now = datetime.now(timezone.utc)
        report = OpenClawReportIn(
            task_id=f"news-trigger-{monitor_id}-{int(now.timestamp())}",
            keyword=result["keyword"],
            time_range={"start": (now - timedelta(days=window_days)), "end": now},
            sources=["monitoring-summary", "news-library"],
            items=[
                {
                    "title": n.get("title") or "未命名新闻",
                    "source": n.get("source_name") or "unknown",
                    "url": n.get("source_url") or "",
                    "published_at": parse_iso_dt(n.get("published_at"))
                    or parse_iso_dt(n.get("created_at"))
                    or now,
                    "summary": n.get("summary"),
                }
                for n in result["key_news"]
                if n.get("source_url")
            ],
            analysis=result["analysis"],
            generated_title=f"{result['keyword']} 新闻触发价格分析（{horizon}）",
            generated_at=now,
            insights=result.get("insights"),
        )
        ingest_id, ingest_status = intake_service.ingest(
            report=report,
            request_id=f"news-trigger-{monitor_id}-{int(now.timestamp())}",
            background_tasks=background_tasks,
            user_id=user_id,
        )
    return {
        "ok": True,
        "mode": "event_triggered",
        "publish": publish,
        "ingest_id": ingest_id,
        "ingest_status": ingest_status,
        **result,
    }
