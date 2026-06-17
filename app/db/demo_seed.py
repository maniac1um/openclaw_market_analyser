"""Seed fictional demo data for the trial portal account."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher

from app.core.config import settings
from app.db import user_queries as uq
from app.services.monitoring_service import MonitoringService

DEMO_USER_ID = "00000000-0000-4000-8000-000000000001"
DEMO_MONITOR_ID = "00000000-0000-4000-8000-000000000002"
DEMO_REPORT_IDS = (
    "00000000-0000-4000-8000-000000000011",
    "00000000-0000-4000-8000-000000000012",
)

_ph = PasswordHasher()


def demo_password_hash() -> str:
    return _ph.hash(settings.demo_user_password)


def _report_payloads() -> list[dict]:
    return [
        {
            "ingest_id": DEMO_REPORT_IDS[0],
            "task_id": "demo-nebula-q1",
            "keyword": "星云电池",
            "title": "虚构 · 星云电池 — Q1 市场研判",
            "generated_at": "2026-03-28T02:00:00+00:00",
            "rendered": {
                "ingest_id": DEMO_REPORT_IDS[0],
                "title": "虚构 · 星云电池 — Q1 市场研判",
                "keyword": "星云电池",
                "time_range": {
                    "start": "2026-01-01T00:00:00+08:00",
                    "end": "2026-03-31T23:59:59+08:00",
                },
                "analysis": (
                    "本报告为**完全虚构的演示内容**，不代表任何真实市场或企业。\n\n"
                    "综合虚构新闻与价格信号，星云电池板块 Q1 呈现**供给端扩张、需求端平稳**格局。"
                ),
                "insights": {
                    "sentiment": "bearish",
                    "risk_level": "medium",
                    "market_impact": "短期供应宽松，价格承压",
                    "confidence": "高",
                    "forecast": "偏弱震荡",
                    "news_sentiment_counts": {"bullish": 1, "bearish": 2, "neutral": 1},
                },
                "sources": ["虚构行业观察", "虚构供应链周报"],
                "items_count": 3,
                "items": [
                    {
                        "title": "虚构 · 星云三号产线试产进度超前",
                        "source": "虚构行业观察",
                        "published_at": "2026-03-20T01:00:00+00:00",
                        "summary": "完全虚构：某演示产线试产顺利，市场担忧供给增加。",
                        "url": "https://example.com/fictional/nebula-line3",
                    },
                    {
                        "title": "虚构 · 渠道库存周转天数上升",
                        "source": "虚构供应链周报",
                        "published_at": "2026-03-15T06:30:00+00:00",
                        "summary": "虚构数据显示经销商库存压力上升，补库意愿减弱。",
                        "url": "https://example.com/fictional/channel-stock",
                    },
                    {
                        "title": "虚构 · 演示级原材料成本小幅回落",
                        "source": "虚构行业观察",
                        "published_at": "2026-03-10T03:00:00+00:00",
                        "summary": "虚构原料指数走弱，成本端对价格形成拖累。",
                        "url": "https://example.com/fictional/raw-material",
                    },
                ],
                "generated_at": "2026-03-28T02:00:00+00:00",
            },
        },
        {
            "ingest_id": DEMO_REPORT_IDS[1],
            "task_id": "demo-stellar-supply",
            "keyword": "曜光组件",
            "title": "虚构 · 曜光组件 — 供应链动态",
            "generated_at": "2026-04-25T01:30:00+00:00",
            "rendered": {
                "ingest_id": DEMO_REPORT_IDS[1],
                "title": "虚构 · 曜光组件 — 供应链动态",
                "keyword": "曜光组件",
                "time_range": {
                    "start": "2026-02-01T00:00:00+08:00",
                    "end": "2026-04-30T23:59:59+08:00",
                },
                "analysis": "本报告为**完全虚构的演示内容**。曜光组件为编造品类，用于展示中性情绪与低风险组合。",
                "insights": {
                    "sentiment": "neutral",
                    "risk_level": "low",
                    "market_impact": "产业链运行平稳，波动有限",
                    "confidence": "中",
                    "forecast": "窄幅整理",
                    "news_sentiment_counts": {"bullish": 1, "bearish": 0, "neutral": 2},
                },
                "sources": ["虚构新能源评论", "虚构贸易监测"],
                "items_count": 2,
                "items": [
                    {
                        "title": "虚构 · 曜光演示园区扩产计划公布",
                        "source": "虚构新能源评论",
                        "published_at": "2026-04-18T02:00:00+00:00",
                        "summary": "虚构扩产消息，市场反应平淡。",
                        "url": "https://example.com/fictional/stellar-expansion",
                    },
                    {
                        "title": "虚构 · 组件封装工序自动化升级",
                        "source": "虚构贸易监测",
                        "published_at": "2026-04-12T00:00:00+00:00",
                        "summary": "虚构技改新闻，对短期价格影响有限。",
                        "url": "https://example.com/fictional/stellar-automation",
                    },
                ],
                "generated_at": "2026-04-25T01:30:00+00:00",
            },
        },
    ]


def _news_rows() -> list[dict]:
    return [
        {
            "keyword": "星云电池",
            "title": "虚构 · 星云三号产线试产进度超前",
            "summary": "完全虚构新闻，仅供演示。",
            "source_url": "https://example.com/fictional/nebula-line3",
            "source_name": "虚构行业观察",
            "published_at": "2026-03-20T01:00:00+00:00",
        },
        {
            "keyword": "曜光组件",
            "title": "虚构 · 曜光演示园区扩产计划公布",
            "summary": "完全虚构新闻，仅供演示。",
            "source_url": "https://example.com/fictional/stellar-expansion",
            "source_name": "虚构新能源评论",
            "published_at": "2026-04-18T02:00:00+00:00",
        },
        {
            "keyword": "虚构 · 示例电芯",
            "title": "虚构 · 演示电芯批发价窄幅波动",
            "summary": "完全虚构价格相关新闻。",
            "source_url": "https://example.com/fictional/cell-price",
            "source_name": "虚构贸易监测",
            "published_at": "2026-06-07T22:00:00+00:00",
        },
    ]


def ensure_demo_user() -> str | None:
    """Create demo user and seed fictional data. Returns demo user id."""
    if not settings.database_url:
        return None
    uq.ensure_user_tables()
    user_id = DEMO_USER_ID
    with uq._connect() as conn, conn.cursor() as cur:  # noqa: SLF001
        cur.execute("SELECT id FROM users WHERE email = %s", (settings.demo_user_email,))
        row = cur.fetchone()
        if row:
            user_id = str(row[0])
            cur.execute(
                "UPDATE users SET password_hash = %s, updated_at = NOW() WHERE id = %s::uuid",
                (demo_password_hash(), user_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO users (id, email, username, password_hash, role, status)
                VALUES (%s::uuid, %s, %s, %s, 'USER', 'active')
                ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash, updated_at = NOW()
                RETURNING id
                """,
                (user_id, settings.demo_user_email, "demo", demo_password_hash()),
            )
            inserted = cur.fetchone()
            if inserted:
                user_id = str(inserted[0])
        conn.commit()
    from app.db.token_queries import set_token_balance

    set_token_balance(user_id, int(settings.default_token_balance))
    seed_demo_data(user_id)
    return user_id


def seed_demo_data(user_id: str) -> None:
    _seed_reports(user_id)
    _seed_monitoring(user_id)
    _seed_news(user_id)


def _seed_reports(user_id: str) -> None:
    import psycopg

    with psycopg.connect(settings.database_url) as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM reports WHERE user_id = %s::uuid", (user_id,))
        for spec in _report_payloads():
            payload_json = {
                "request_id": f"demo-{spec['ingest_id']}",
                "raw_path": "",
                "rendered_path": None,
                "error": None,
                "rendered_payload": spec["rendered"],
            }
            cur.execute(
                """
                INSERT INTO reports (
                    ingest_id, task_id, keyword, status, generated_title, generated_at, payload_json, user_id, updated_at
                ) VALUES (%s::uuid, %s, %s, 'published', %s, %s::timestamptz, %s::jsonb, %s::uuid, NOW())
                """,
                (
                    spec["ingest_id"],
                    spec["task_id"],
                    spec["keyword"],
                    spec["title"],
                    spec["generated_at"],
                    json.dumps(payload_json, ensure_ascii=False),
                    user_id,
                ),
            )
        conn.commit()


def _seed_monitoring(user_id: str) -> None:
    if not settings.monitoring_database_url:
        return
    import psycopg

    svc = MonitoringService(settings.monitoring_database_url)
    svc.ensure_tables()
    keyword = "虚构 · 示例电芯"
    now = datetime.now(timezone.utc)

    with psycopg.connect(settings.monitoring_database_url) as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM price_observations WHERE user_id = %s::uuid", (user_id,))
        cur.execute("DELETE FROM price_monitor_urls WHERE user_id = %s::uuid", (user_id,))
        cur.execute("DELETE FROM price_monitors WHERE user_id = %s::uuid", (user_id,))
        cur.execute(
            """
            INSERT INTO price_monitors (monitor_id, keyword, cadence, source_mode, created_at, user_id)
            VALUES (%s::uuid, %s, 'daily', 'openclaw_auto', %s, %s::uuid)
            ON CONFLICT (monitor_id) DO UPDATE SET keyword = EXCLUDED.keyword, user_id = EXCLUDED.user_id
            """,
            (DEMO_MONITOR_ID, keyword, now, user_id),
        )
        cur.execute(
            """
            INSERT INTO price_monitor_urls (monitor_id, platform, url, discovered_at, metadata_json, user_id)
            VALUES (%s::uuid, 'demo', 'https://example.com/fictional/demo-price', %s, '{}'::jsonb, %s::uuid)
            RETURNING id
            """,
            (DEMO_MONITOR_ID, now, user_id),
        )
        url_row = cur.fetchone()
        if not url_row:
            conn.commit()
            return
        monitor_url_id = int(url_row[0])

        base_price = 118.0
        for day_offset in range(30):
            captured = now - timedelta(days=29 - day_offset)
            price = round(base_price + (day_offset % 7) * 0.6 - (day_offset // 10) * 0.3, 2)
            cur.execute(
                """
                INSERT INTO price_observations (
                    monitor_id, monitor_url_id, captured_at, title, price, currency, status, user_id
                ) VALUES (%s::uuid, %s, %s, %s, %s, 'CNY', 'ok', %s::uuid)
                """,
                (
                    DEMO_MONITOR_ID,
                    monitor_url_id,
                    captured,
                    f"虚构 · 演示电芯 {'ABC'[day_offset % 3]} 型",
                    price,
                    user_id,
                ),
            )
        conn.commit()


def _seed_news(user_id: str) -> None:
    if not settings.news_database_url:
        return
    import psycopg

    from app.db.public_queries import ensure_news_library_tables

    ensure_news_library_tables()
    with psycopg.connect(settings.news_database_url) as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM news_library WHERE user_id = %s::uuid", (user_id,))
        for row in _news_rows():
            cur.execute(
                """
                INSERT INTO news_library (keyword, summary, source_url, title, source_name, published_at, user_id)
                VALUES (%s, %s, %s, %s, %s, %s::timestamptz, %s::uuid)
                """,
                (
                    row["keyword"],
                    row["summary"],
                    row["source_url"],
                    row["title"],
                    row["source_name"],
                    row["published_at"],
                    user_id,
                ),
            )
        conn.commit()


def maybe_reset_demo_data() -> None:
    """Reset demo seed once per UTC day (best-effort on startup)."""
    if not settings.database_url:
        return
    user = uq.get_user_by_email(settings.demo_user_email)
    if not user:
        return
    marker_path = settings.demo_reset_marker_path
    today = datetime.now(timezone.utc).date().isoformat()
    try:
        if marker_path.is_file() and marker_path.read_text(encoding="utf-8").strip() == today:
            return
    except OSError:
        pass
    seed_demo_data(user.id)
    try:
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text(today, encoding="utf-8")
    except OSError:
        pass
