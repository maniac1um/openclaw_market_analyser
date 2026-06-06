"""Public portal read/write queries against the three PostgreSQL databases."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException

from app.core.config import settings
from app.db.query_context import QueryContext
from app.schemas.portal import ExternalSchedulerConfigRequest
from app.services.monitoring_service import MonitoringService
from app.services.openclaw_chat_bridge import probe_openclaw_gateway
from app.utils.formatting import format_cn_local_datetime, parse_iso_dt
from app.utils.path_safety import parse_uuid, safe_child_path
from app.utils.public_errors import public_error_detail, sanitize_gateway_probe_detail
from app.utils.sentiment import sentiment_from_text


def rendered_root() -> Path:
    return Path(settings.content_rendered_dir)


def raw_root() -> Path:
    return Path(settings.content_raw_dir)


def require_public_reports_db() -> None:
    if not settings.database_url:
        raise HTTPException(
            status_code=503,
            detail="未配置 OPENCLAW_DATABASE_URL，新闻动态接口仅从数据库提供服务。",
        )


def require_public_news_db() -> None:
    if not settings.news_database_url:
        raise HTTPException(
            status_code=503,
            detail="未配置 OPENCLAW_NEWS_DATABASE_URL，新闻库接口不可用。",
        )


def ensure_news_library_tables() -> None:
    """Create news_library schema on first portal read (matches openclaw intake init)."""
    if not settings.news_database_url:
        return
    import psycopg

    sql = """
    CREATE TABLE IF NOT EXISTS news_library (
      id BIGSERIAL PRIMARY KEY,
      keyword TEXT NOT NULL,
      summary TEXT NOT NULL,
      source_url TEXT NOT NULL,
      title TEXT,
      source_name TEXT,
      published_at TIMESTAMPTZ,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_news_library_keyword_created_at
      ON news_library (keyword, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_news_library_source_url
      ON news_library (source_url);
    ALTER TABLE news_library ADD COLUMN IF NOT EXISTS user_id UUID;
    """
    with psycopg.connect(settings.news_database_url) as conn, conn.cursor() as cur:
        cur.execute(sql)
        conn.commit()


def ensure_monitoring_tables() -> None:
    if settings.monitoring_database_url:
        MonitoringService(settings.monitoring_database_url).ensure_tables()


def list_reports_from_db(ctx: QueryContext) -> list[dict]:
    import psycopg

    clause, params = ctx.owner_clause()
    sql = f"""
    SELECT ingest_id, payload_json->'rendered_payload' AS rendered_payload, generated_at
    FROM reports
    WHERE status = 'published'
      AND payload_json ? 'rendered_payload'{clause}
    ORDER BY generated_at DESC NULLS LAST, id DESC
    """
    out: list[dict] = []
    with psycopg.connect(settings.database_url) as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        for ingest_id, rendered_payload, generated_at in cur.fetchall():
            payload = rendered_payload or {}
            out.append(
                {
                    "ingest_id": str(ingest_id),
                    "title": payload.get("title"),
                    "keyword": payload.get("keyword"),
                    "generated_at": payload.get("generated_at") or (generated_at.isoformat() if generated_at else None),
                }
            )
    return out


def report_to_markdown(report: dict) -> str:
    lines: list[str] = []
    lines.append(f"# {report.get('title') or '未命名报告'}")
    lines.append("")
    lines.append(f"- **关键词**：{report.get('keyword') or '-'}")
    time_range = report.get("time_range") or {}
    lines.append(
        f"- **时间范围**：{format_cn_local_datetime(time_range.get('start'))} ~ {format_cn_local_datetime(time_range.get('end'))}"
    )
    lines.append(f"- **来源**：{'、'.join(report.get('sources') or []) or '-'}")
    lines.append(f"- **条目数**：{report.get('items_count') or 0}")
    lines.append("")
    lines.append("## 趋势分析")
    lines.append(report.get("analysis") or "暂无分析内容")
    lines.append("")
    lines.append("## 关键条目")
    items = report.get("items") or []
    if not items:
        lines.append("- 暂无条目")
    else:
        for item in items[:12]:
            lines.append(f"- **{item.get('title') or '未命名'}**（{item.get('source') or '-'}）")
            lines.append(f"  - 发布时间：{format_cn_local_datetime(item.get('published_at'))}")
            if item.get("price") is not None:
                lines.append(f"  - 价格：{item.get('price')} {item.get('currency') or ''}".rstrip())
            if item.get("summary"):
                lines.append(f"  - 摘要：{item.get('summary')}")
            if item.get("url"):
                lines.append(f"  - 链接：[查看原文]({item.get('url')})")
    return "\n".join(lines)


def get_report_detail_from_db(ingest_id: str, ctx: QueryContext) -> dict | None:
    import psycopg

    clause, params = ctx.owner_clause()
    sql = f"""
    SELECT payload_json->'rendered_payload' AS rendered_payload
    FROM reports
    WHERE ingest_id = %s::uuid
      AND status = 'published'{clause}
    LIMIT 1
    """
    with psycopg.connect(settings.database_url) as conn, conn.cursor() as cur:
        cur.execute(sql, (ingest_id, *params))
        row = cur.fetchone()
    if not row:
        return None
    payload = row[0] or {}
    if not payload:
        return None
    payload["report_markdown"] = report_to_markdown(payload)
    return payload


def delete_reports_from_db(ingest_ids: list[str], ctx: QueryContext) -> dict:
    import psycopg

    deleted: list[str] = []
    not_found: list[str] = []
    clause, owner_params = ctx.owner_clause()
    sql = f"DELETE FROM reports WHERE ingest_id = %s::uuid{clause} RETURNING ingest_id"
    raw, rendered = raw_root(), rendered_root()
    with psycopg.connect(settings.database_url) as conn, conn.cursor() as cur:
        for ingest_id in ingest_ids:
            canonical = parse_uuid(ingest_id)
            if not canonical:
                not_found.append(ingest_id)
                continue
            cur.execute(sql, (canonical, *owner_params))
            row = cur.fetchone()
            if row:
                iid = str(row[0])
                deleted.append(iid)
                for root in (raw, rendered):
                    safe_path = safe_child_path(root, iid, suffix=".json")
                    if safe_path and safe_path.is_file():
                        safe_path.unlink()
            else:
                not_found.append(canonical)
        conn.commit()
    return {"requested": len(ingest_ids), "deleted": deleted, "not_found": not_found}


def list_news_library_from_db(limit: int = 100, keyword: str | None = None, *, ctx: QueryContext) -> list[dict]:
    import psycopg

    ensure_news_library_tables()
    clause, params = ctx.owner_clause()
    sql = """
    SELECT id, keyword, summary, source_url, title, source_name, published_at, created_at
    FROM news_library
    WHERE 1=1
    """
    qparams: list = []
    if keyword and keyword.strip():
        sql += " AND keyword ILIKE %s"
        qparams.append(f"%{keyword.strip()}%")
    sql += clause
    qparams.extend(params)
    sql += " ORDER BY created_at DESC LIMIT %s"
    qparams.append(limit)

    out: list[dict] = []
    with psycopg.connect(settings.news_database_url) as conn, conn.cursor() as cur:
        cur.execute(sql, tuple(qparams))
        for row in cur.fetchall():
            out.append(
                {
                    "id": int(row[0]),
                    "keyword": row[1],
                    "summary": row[2],
                    "source_url": row[3],
                    "title": row[4],
                    "source_name": row[5],
                    "published_at": row[6].isoformat() if row[6] else None,
                    "created_at": row[7].isoformat() if row[7] else None,
                }
            )
    return out


def delete_news_library_from_db(ids: list[int], ctx: QueryContext) -> dict:
    import psycopg

    ensure_news_library_tables()
    if not settings.news_database_url:
        return {"requested": len(ids), "deleted": [], "not_found": ids}
    deleted: list[int] = []
    not_found: list[int] = []
    clause, owner_params = ctx.owner_clause()
    sql = f"DELETE FROM news_library WHERE id = %s{clause} RETURNING id"
    with psycopg.connect(settings.news_database_url) as conn, conn.cursor() as cur:
        for item_id in ids:
            cur.execute(sql, (int(item_id), *owner_params))
            row = cur.fetchone()
            if row:
                deleted.append(int(row[0]))
            else:
                not_found.append(int(item_id))
        conn.commit()
    return {"requested": len(ids), "deleted": deleted, "not_found": not_found}


def list_news_items_from_db(limit: int = 120, *, ctx: QueryContext) -> list[dict]:
    import psycopg

    clause, params = ctx.owner_clause()
    sql = f"""
    SELECT ingest_id, payload_json->'rendered_payload' AS rendered_payload, generated_at
    FROM reports
    WHERE status = 'published'
      AND payload_json ? 'rendered_payload'{clause}
    ORDER BY generated_at DESC NULLS LAST, id DESC
    LIMIT 200
    """
    out: list[dict] = []
    with psycopg.connect(settings.database_url) as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    for ingest_id, rendered_payload, generated_at in rows:
        payload = rendered_payload or {}
        items = payload.get("items") or []
        for item in items:
            out.append(
                {
                    "ingest_id": str(ingest_id),
                    "report_title": payload.get("title") or payload.get("generated_title") or "未命名报告",
                    "keyword": payload.get("keyword"),
                    "generated_at": payload.get("generated_at") or (generated_at.isoformat() if generated_at else None),
                    "title": item.get("title"),
                    "source": item.get("source"),
                    "url": item.get("url"),
                    "published_at": item.get("published_at"),
                    "summary": item.get("summary"),
                    "price": item.get("price"),
                    "currency": item.get("currency"),
                }
            )
            if len(out) >= limit:
                return out
    return out


def topic_analysis_cards_from_db(limit: int = 60, *, ctx: QueryContext) -> list[dict]:
    import psycopg

    clause, params = ctx.owner_clause()
    sql = f"""
    SELECT ingest_id, payload_json->'rendered_payload' AS rendered_payload, generated_at
    FROM reports
    WHERE status = 'published'
      AND payload_json ? 'rendered_payload'{clause}
    ORDER BY generated_at DESC NULLS LAST, id DESC
    LIMIT %s
    """
    out: list[dict] = []
    with psycopg.connect(settings.database_url) as conn, conn.cursor() as cur:
        cur.execute(sql, (*params, limit))
        for ingest_id, rendered_payload, generated_at in cur.fetchall():
            payload = rendered_payload or {}
            out.append(
                {
                    "ingest_id": str(ingest_id),
                    "title": payload.get("title") or payload.get("generated_title") or "未命名专题",
                    "keyword": payload.get("keyword"),
                    "generated_at": payload.get("generated_at") or (generated_at.isoformat() if generated_at else None),
                    "analysis": payload.get("analysis") or "暂无分析内容",
                    "items_count": payload.get("items_count") or len(payload.get("items") or []),
                    "sources": payload.get("sources") or [],
                    "insights": payload.get("insights"),
                }
            )
    return out


def monitor_accessible(monitor_id: str, ctx: QueryContext) -> bool:
    import psycopg

    if not settings.monitoring_database_url:
        return False
    clause, params = ctx.monitor_owner_clause("m")
    sql = f"SELECT 1 FROM price_monitors m WHERE m.monitor_id = %s::uuid{clause} LIMIT 1"
    with psycopg.connect(settings.monitoring_database_url) as conn, conn.cursor() as cur:
        cur.execute(sql, (monitor_id, *params))
        return cur.fetchone() is not None


def list_monitors_public(ctx: QueryContext) -> list[dict]:
    import psycopg

    ensure_monitoring_tables()
    if not settings.monitoring_database_url:
        return []
    clause, params = ctx.monitor_owner_clause("m")
    sql = f"""
    SELECT
      m.monitor_id, m.keyword, m.cadence, m.created_at,
      COUNT(DISTINCT u.id) AS url_count,
      COUNT(o.id) AS observation_count,
      MAX(o.captured_at) AS last_captured_at
    FROM price_monitors m
    LEFT JOIN price_monitor_urls u ON u.monitor_id = m.monitor_id
    LEFT JOIN price_observations o ON o.monitor_id = m.monitor_id
    WHERE 1=1{clause}
    GROUP BY m.monitor_id, m.keyword, m.cadence, m.created_at
    ORDER BY m.created_at DESC
    """
    out: list[dict] = []
    with psycopg.connect(settings.monitoring_database_url) as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        for row in cur.fetchall():
            out.append(
                {
                    "monitor_id": str(row[0]),
                    "keyword": row[1],
                    "cadence": row[2],
                    "created_at": row[3].isoformat() if row[3] else None,
                    "url_count": int(row[4] or 0),
                    "observation_count": int(row[5] or 0),
                    "last_captured_at": row[6].isoformat() if row[6] else None,
                }
            )
    return out


def monitor_timeseries_public(monitor_id: str, window_days: int, ctx: QueryContext) -> dict:
    import psycopg

    if not settings.monitoring_database_url:
        return {"monitor_id": monitor_id, "points": []}
    if not monitor_accessible(monitor_id, ctx):
        return {"monitor_id": monitor_id, "points": []}
    sql = """
    SELECT DATE_TRUNC('day', captured_at) AS day,
           MIN(price), MAX(price), AVG(price), COUNT(*)
    FROM price_observations
    WHERE monitor_id = %s::uuid
      AND captured_at >= NOW() - (%s || ' days')::interval
      AND price IS NOT NULL
    GROUP BY DATE_TRUNC('day', captured_at)
    ORDER BY day ASC
    """
    points: list[dict] = []
    with psycopg.connect(settings.monitoring_database_url) as conn, conn.cursor() as cur:
        cur.execute(sql, (monitor_id, int(window_days)))
        for day, min_price, max_price, avg_price, priced_count in cur.fetchall():
            points.append(
                {
                    "date": day.date().isoformat(),
                    "min_price": float(min_price) if min_price is not None else None,
                    "max_price": float(max_price) if max_price is not None else None,
                    "avg_price": float(avg_price) if avg_price is not None else None,
                    "priced_count": int(priced_count or 0),
                }
            )
    return {"monitor_id": monitor_id, "window_days": int(window_days), "points": points}


def monitor_observations_public(monitor_id: str, limit: int = 200, *, ctx: QueryContext) -> dict:
    import psycopg

    if not settings.monitoring_database_url:
        return {"monitor_id": monitor_id, "rows": []}
    if not monitor_accessible(monitor_id, ctx):
        return {"monitor_id": monitor_id, "rows": []}
    sql = """
    SELECT o.captured_at, o.title, o.price
    FROM price_observations o
    WHERE o.monitor_id = %s::uuid AND o.price IS NOT NULL
    ORDER BY o.captured_at ASC
    LIMIT %s
    """
    rows: list[dict] = []
    prev_price: float | None = None
    with psycopg.connect(settings.monitoring_database_url) as conn, conn.cursor() as cur:
        cur.execute(sql, (monitor_id, int(limit)))
        for idx, (captured_at, title, price) in enumerate(cur.fetchall(), start=1):
            p = float(price) if price is not None else None
            delta = p - prev_price if p is not None and prev_price is not None else None
            if p is not None:
                prev_price = p
            rows.append(
                {
                    "index": idx,
                    "item_name": title or "未命名商品",
                    "captured_at": captured_at.isoformat() if captured_at else None,
                    "price": p,
                    "delta_from_prev": delta,
                }
            )
    return {"monitor_id": monitor_id, "rows": rows}


def monitoring_scheduler_status_public(app_obj: FastAPI) -> dict:
    started = bool(getattr(app_obj.state, "monitoring_scheduler_started", False))
    has_db = bool(settings.monitoring_database_url)
    has_monitor = bool(settings.monitoring_scheduler_monitor_id)
    enabled = bool(settings.monitoring_scheduler_enabled)
    return {
        "mode": "internal",
        "enabled": enabled,
        "started": started,
        "configured": enabled and has_db and has_monitor,
        "monitor_id": settings.monitoring_scheduler_monitor_id,
        "interval_minutes": settings.monitoring_scheduler_interval_minutes,
        "run_on_start": settings.monitoring_scheduler_run_on_start,
        "has_monitoring_database_url": has_db,
        "allow_server_scrape": settings.monitoring_allow_server_scrape,
    }


def ensure_external_scheduler_tables() -> None:
    import psycopg

    if not settings.monitoring_database_url:
        return
    with psycopg.connect(settings.monitoring_database_url) as conn, conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS external_scheduler_runs (
              id BIGSERIAL PRIMARY KEY,
              job_name TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'ok',
              monitor_id UUID NULL,
              message TEXT NULL,
              last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
              source TEXT NOT NULL DEFAULT 'heartbeat'
            );
            """
        )
        cur.execute("ALTER TABLE external_scheduler_runs ADD COLUMN IF NOT EXISTS user_id UUID")
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_external_scheduler_runs_job_last_seen
              ON external_scheduler_runs (job_name, last_seen_at DESC);
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS external_scheduler_configs (
              job_name TEXT PRIMARY KEY,
              monitor_id UUID NOT NULL,
              cron_expr TEXT NOT NULL,
              timezone TEXT NOT NULL DEFAULT 'Asia/Shanghai',
              enabled BOOLEAN NOT NULL DEFAULT TRUE,
              retry_policy TEXT NOT NULL DEFAULT 'no-retry',
              notes TEXT NULL,
              updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        )
        cur.execute("ALTER TABLE external_scheduler_configs ADD COLUMN IF NOT EXISTS user_id UUID")
        conn.commit()


def save_external_scheduler_run(
    *,
    job_name: str,
    status: str,
    monitor_id: str | None,
    message: str | None,
    source: str = "heartbeat",
    user_id: str | None = None,
) -> str:
    now = datetime.now(timezone.utc).isoformat()
    if not settings.monitoring_database_url:
        return now
    import psycopg

    ensure_external_scheduler_tables()
    with psycopg.connect(settings.monitoring_database_url) as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO external_scheduler_runs (job_name, status, monitor_id, message, last_seen_at, source, user_id)
            VALUES (%s, %s, NULLIF(%s, '')::uuid, %s, NOW(), %s, NULLIF(%s, '')::uuid)
            RETURNING last_seen_at
            """,
            (job_name, status, monitor_id or "", message, source, user_id or ""),
        )
        row = cur.fetchone()
        conn.commit()
    return row[0].isoformat() if row and row[0] else now


def external_scheduler_jobs_from_db(limit: int = 120) -> list[dict]:
    if not settings.monitoring_database_url:
        return []
    import psycopg

    ensure_external_scheduler_tables()
    with psycopg.connect(settings.monitoring_database_url) as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT r.job_name, r.status, r.monitor_id, r.message, r.last_seen_at
            FROM external_scheduler_runs r
            JOIN (
              SELECT job_name, MAX(last_seen_at) AS mx
              FROM external_scheduler_runs GROUP BY job_name
            ) t ON t.job_name = r.job_name AND t.mx = r.last_seen_at
            ORDER BY r.last_seen_at DESC
            LIMIT %s
            """,
            (int(limit),),
        )
        rows = cur.fetchall()
    return [
        {
            "job_name": job_name,
            "status": status,
            "monitor_id": str(monitor_id) if monitor_id else None,
            "message": message,
            "last_seen_at": last_seen_at.isoformat() if last_seen_at else None,
        }
        for job_name, status, monitor_id, message, last_seen_at in rows
    ]


def external_scheduler_jobs_public(app_obj: FastAPI) -> dict:
    out = external_scheduler_jobs_from_db(limit=120)
    if not out:
        jobs = getattr(app_obj.state, "external_scheduler_jobs", {})
        for job_name, item in jobs.items():
            out.append(
                {
                    "job_name": job_name,
                    "status": item.get("status"),
                    "monitor_id": item.get("monitor_id"),
                    "message": item.get("message"),
                    "last_seen_at": item.get("last_seen_at"),
                }
            )
        out.sort(key=lambda x: x.get("last_seen_at") or "", reverse=True)
    return {"jobs": out}


def external_scheduler_run_history_public(limit: int = 120, *, ctx: QueryContext | None = None) -> dict:
    if not settings.monitoring_database_url:
        return {"runs": []}
    import psycopg

    clause, params = ("", ())
    if ctx is not None:
        clause, params = ctx.owner_clause()
    ensure_external_scheduler_tables()
    with psycopg.connect(settings.monitoring_database_url) as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT job_name, status, monitor_id, message, last_seen_at, source
            FROM external_scheduler_runs
            WHERE 1=1{clause}
            ORDER BY last_seen_at DESC, id DESC
            LIMIT %s
            """,
            (*params, int(limit)),
        )
        rows = cur.fetchall()
    return {
        "runs": [
            {
                "job_name": job_name,
                "status": status,
                "monitor_id": str(monitor_id) if monitor_id else None,
                "message": message,
                "last_seen_at": last_seen_at.isoformat() if last_seen_at else None,
                "source": source,
            }
            for job_name, status, monitor_id, message, last_seen_at, source in rows
        ]
    }


def external_scheduler_configs_public(*, ctx: QueryContext | None = None) -> dict:
    if not settings.monitoring_database_url:
        return {"configs": []}
    import psycopg

    clause, params = ("", ())
    if ctx is not None:
        clause, params = ctx.owner_clause()
    ensure_external_scheduler_tables()
    with psycopg.connect(settings.monitoring_database_url) as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT job_name, monitor_id, cron_expr, timezone, enabled, retry_policy, notes, updated_at
            FROM external_scheduler_configs
            WHERE 1=1{clause}
            ORDER BY updated_at DESC, job_name ASC
            """,
            params,
        )
        rows = cur.fetchall()
    return {
        "configs": [
            {
                "job_name": job_name,
                "monitor_id": str(monitor_id),
                "cron_expr": cron_expr,
                "timezone": tz,
                "enabled": bool(enabled),
                "retry_policy": retry_policy,
                "notes": notes,
                "updated_at": updated_at.isoformat() if updated_at else None,
            }
            for job_name, monitor_id, cron_expr, tz, enabled, retry_policy, notes, updated_at in rows
        ]
    }


def upsert_external_scheduler_config(payload: ExternalSchedulerConfigRequest, ctx: QueryContext) -> dict:
    if not settings.monitoring_database_url:
        raise HTTPException(status_code=503, detail="未配置 OPENCLAW_MONITORING_DATABASE_URL。")
    if not monitor_accessible(payload.monitor_id, ctx):
        raise HTTPException(status_code=404, detail="Monitor not found")
    import psycopg

    owner_clause, owner_params = ctx.owner_clause()
    ensure_external_scheduler_tables()
    with psycopg.connect(settings.monitoring_database_url) as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT job_name FROM external_scheduler_configs WHERE job_name = %s{owner_clause} LIMIT 1",
            (payload.job_name, *owner_params),
        )
        existing = cur.fetchone()
        if existing is None and not ctx.is_admin:
            cur.execute("SELECT job_name FROM external_scheduler_configs WHERE job_name = %s LIMIT 1", (payload.job_name,))
            if cur.fetchone():
                raise HTTPException(status_code=404, detail="Job not found")
        cur.execute(
            """
            INSERT INTO external_scheduler_configs (
              job_name, monitor_id, cron_expr, timezone, enabled, retry_policy, notes, updated_at, user_id
            )
            VALUES (%s, %s::uuid, %s, %s, %s, %s, %s, NOW(), %s::uuid)
            ON CONFLICT (job_name) DO UPDATE SET
              monitor_id = EXCLUDED.monitor_id,
              cron_expr = EXCLUDED.cron_expr,
              timezone = EXCLUDED.timezone,
              enabled = EXCLUDED.enabled,
              retry_policy = EXCLUDED.retry_policy,
              notes = EXCLUDED.notes,
              updated_at = NOW(),
              user_id = EXCLUDED.user_id
            RETURNING updated_at
            """,
            (
                payload.job_name,
                payload.monitor_id,
                payload.cron_expr,
                payload.timezone,
                payload.enabled,
                payload.retry_policy,
                payload.notes,
                ctx.user_id,
            ),
        )
        row = cur.fetchone()
        conn.commit()
    return {"ok": True, "job_name": payload.job_name, "updated_at": row[0].isoformat() if row else None}


def toggle_external_scheduler_config(job_name: str, enabled: bool, ctx: QueryContext) -> dict:
    if not settings.monitoring_database_url:
        raise HTTPException(status_code=503, detail="未配置 OPENCLAW_MONITORING_DATABASE_URL。")
    import psycopg

    owner_clause, owner_params = ctx.owner_clause()
    ensure_external_scheduler_tables()
    with psycopg.connect(settings.monitoring_database_url) as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            UPDATE external_scheduler_configs SET enabled = %s, updated_at = NOW()
            WHERE job_name = %s{owner_clause} RETURNING updated_at
            """,
            (enabled, job_name, *owner_params),
        )
        row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(status_code=404, detail="job_name not found")
    return {"ok": True, "job_name": job_name, "enabled": enabled, "updated_at": row[0].isoformat()}


def openclaw_gateway_status_public() -> dict:
    checked_at = datetime.now(timezone.utc).isoformat()
    ws_url = (settings.openclaw_ws_url or "").strip()
    if not ws_url:
        return {
            "ok": False,
            "ready": False,
            "checked_at": checked_at,
            "ws_url": "",
            "latency_ms": None,
            "detail": "OPENCLAW_OPENCLAW_WS_URL is empty",
        }
    try:
        probe = asyncio.run(
            probe_openclaw_gateway(
                openclaw_ws_url=ws_url,
                timeout_seconds=settings.openclaw_gateway_probe_timeout_seconds,
            )
        )
    except Exception:  # noqa: BLE001
        probe = {"ok": False, "ready": False, "latency_ms": None, "detail": "gateway unreachable"}
    detail = sanitize_gateway_probe_detail(str(probe.get("detail") or ""))
    return {
        "ok": bool(probe.get("ok")),
        "ready": bool(probe.get("ready")),
        "checked_at": checked_at,
        "ws_url": ws_url if settings.expose_gateway_ws_url else ("configured" if ws_url else ""),
        "latency_ms": probe.get("latency_ms"),
        "detail": detail,
    }


def openclaw_work_overview_public(app_obj: FastAPI, ctx: QueryContext | None = None) -> dict:
    ext = external_scheduler_jobs_public(app_obj)
    jobs = ext.get("jobs") or []

    reports_clause, reports_params = ("", ())
    monitor_clause, monitor_params = ("", ())
    news_clause, news_params = ("", ())
    if ctx is not None:
        reports_clause, reports_params = ctx.owner_clause()
        monitor_clause, monitor_params = ctx.monitor_owner_clause("m")
        news_clause, news_params = ctx.owner_clause()

    reports: dict = {"available": False, "published_count": 0, "last_generated_at": None, "recent": []}
    if settings.database_url:
        import psycopg

        try:
            with psycopg.connect(settings.database_url) as conn, conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT COUNT(*), MAX(generated_at) FROM reports
                    WHERE status = 'published' AND payload_json ? 'rendered_payload'{reports_clause}
                    """,
                    reports_params,
                )
                cnt, mx = cur.fetchone()
                reports["available"] = True
                reports["published_count"] = int(cnt or 0)
                reports["last_generated_at"] = mx.isoformat() if mx else None
                cur.execute(
                    f"""
                    SELECT ingest_id, payload_json->'rendered_payload', generated_at
                    FROM reports WHERE status = 'published' AND payload_json ? 'rendered_payload'{reports_clause}
                    ORDER BY generated_at DESC NULLS LAST, id DESC LIMIT 4
                    """,
                    reports_params,
                )
                recent: list[dict] = []
                for ingest_id, rendered_payload, generated_at in cur.fetchall():
                    payload = rendered_payload or {}
                    recent.append(
                        {
                            "ingest_id": str(ingest_id),
                            "title": payload.get("title") or payload.get("generated_title") or "未命名报告",
                            "generated_at": payload.get("generated_at") or (generated_at.isoformat() if generated_at else None),
                        }
                    )
                reports["recent"] = recent
        except Exception as exc:  # noqa: BLE001
            reports["error"] = str(exc)

    price: dict = {"available": False, "monitor_count": 0, "observation_count": 0, "last_captured_at": None, "recent": []}
    if settings.monitoring_database_url:
        import psycopg

        try:
            with psycopg.connect(settings.monitoring_database_url) as conn, conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM price_monitors m WHERE 1=1{monitor_clause}", monitor_params)
                price["monitor_count"] = int(cur.fetchone()[0] or 0)
                obs_clause, obs_params = ctx.owner_clause("o") if ctx is not None else ("", ())
                cur.execute(
                    f"SELECT COUNT(*), MAX(captured_at) FROM price_observations o WHERE 1=1{obs_clause}",
                    obs_params,
                )
                oc, lc = cur.fetchone()
                price["observation_count"] = int(oc or 0)
                price["last_captured_at"] = lc.isoformat() if lc else None
                cur.execute(
                    f"""
                    SELECT m.monitor_id, m.keyword, COUNT(o.id), MAX(o.captured_at)
                    FROM price_monitors m
                    LEFT JOIN price_observations o ON o.monitor_id = m.monitor_id
                    WHERE 1=1{monitor_clause}
                    GROUP BY m.monitor_id, m.keyword, m.created_at
                    ORDER BY MAX(o.captured_at) DESC NULLS LAST, m.created_at DESC
                    LIMIT 6
                    """,
                    monitor_params,
                )
                price["recent"] = [
                    {
                        "monitor_id": str(monitor_id),
                        "keyword": keyword,
                        "observation_count": int(obs_count or 0),
                        "last_captured_at": last_ts.isoformat() if last_ts else None,
                    }
                    for monitor_id, keyword, obs_count, last_ts in cur.fetchall()
                ]
                price["available"] = True
        except Exception as exc:  # noqa: BLE001
            price["error"] = str(exc)

    news: dict = {"available": False, "item_count": 0, "last_created_at": None, "recent_keywords": []}
    if settings.news_database_url:
        import psycopg

        try:
            with psycopg.connect(settings.news_database_url) as conn, conn.cursor() as cur:
                cur.execute(
                    f"SELECT COUNT(*), MAX(created_at) FROM news_library WHERE 1=1{news_clause}",
                    news_params,
                )
                ic, mx = cur.fetchone()
                news["item_count"] = int(ic or 0)
                news["last_created_at"] = mx.isoformat() if mx else None
                cur.execute(
                    f"""
                    SELECT keyword, COUNT(*), MAX(COALESCE(published_at, created_at)), MAX(created_at)
                    FROM news_library WHERE 1=1{news_clause}
                    GROUP BY keyword
                    ORDER BY MAX(COALESCE(published_at, created_at)) DESC NULLS LAST LIMIT 6
                    """,
                    news_params,
                )
                news["recent_keywords"] = [
                    {
                        "keyword": keyword,
                        "item_count": int(item_count or 0),
                        "last_event_at": last_event_at.isoformat() if last_event_at else None,
                        "last_created_at": last_created_at.isoformat() if last_created_at else None,
                    }
                    for keyword, item_count, last_event_at, last_created_at in cur.fetchall()
                ]
                news["available"] = True
        except Exception as exc:  # noqa: BLE001
            news["error"] = str(exc)

    return {
        "gateway": openclaw_gateway_status_public(),
        "reports": reports,
        "price_monitoring": price,
        "news_library": news,
        "external_cron": {"job_count": len(jobs), "jobs": jobs},
        "workflow": {
            "scheduler_configs": external_scheduler_configs_public(ctx=ctx).get("configs", []),
            "recent_runs": external_scheduler_run_history_public(limit=12, ctx=ctx).get("runs", []),
        },
        "refresh_hint_seconds": 1800,
    }


def check_postgres_dsn_public(*, key: str, label: str, dsn: str | None) -> dict:
    if not (dsn or "").strip():
        return {
            "key": key,
            "label": label,
            "ok": False,
            "severity": "warn",
            "detail": "未配置数据库连接串",
            "hint": f"请设置环境变量并重启服务：{key.upper()} 对应 DSN",
        }
    try:
        import psycopg

        with psycopg.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return {"key": key, "label": label, "ok": True, "severity": "ok", "detail": "连接正常", "hint": ""}
    except Exception:  # noqa: BLE001
        return {
            "key": key,
            "label": label,
            "ok": False,
            "severity": "error",
            "detail": "数据库连接失败",
            "hint": "检查 PostgreSQL 是否运行、账号权限与 DSN 是否一致",
        }


def workflow_diagnostics_public(app_obj: FastAPI) -> dict:
    checked_at = datetime.now(timezone.utc).isoformat()
    checks: list[dict] = []
    gateway = openclaw_gateway_status_public()
    checks.append(
        {
            "key": "gateway",
            "label": "OpenClaw Gateway",
            "ok": bool(gateway.get("ok")),
            "severity": "ok" if gateway.get("ok") else "error",
            "detail": gateway.get("detail") or "-",
            "hint": "确认 OpenClaw Gateway sidecar 已启动，且 OPENCLAW_OPENCLAW_WS_URL 可访问",
            "extra": {"ws_url": gateway.get("ws_url"), "latency_ms": gateway.get("latency_ms")},
        }
    )
    checks.append(check_postgres_dsn_public(key="openclaw_database_url", label="报告数据库（openclaw_app）", dsn=settings.database_url))
    checks.append(check_postgres_dsn_public(key="openclaw_monitoring_database_url", label="价格数据库（openclaw_monitor）", dsn=settings.monitoring_database_url))
    checks.append(check_postgres_dsn_public(key="openclaw_news_database_url", label="新闻数据库（openclaw_news）", dsn=settings.news_database_url))

    configs = external_scheduler_configs_public().get("configs", [])
    enabled_configs = [row for row in configs if bool(row.get("enabled"))]
    checks.append(
        {
            "key": "external_scheduler_configs",
            "label": "外部调度配置",
            "ok": bool(configs),
            "severity": "ok" if configs else "warn",
            "detail": f"总配置数={len(configs)}，启用中={len(enabled_configs)}",
            "hint": "建议至少配置 1 个外部调度任务，并绑定 monitor_id",
        }
    )
    recent_runs = external_scheduler_run_history_public(limit=1).get("runs", [])
    if not recent_runs:
        checks.append(
            {
                "key": "external_scheduler_recent_run",
                "label": "最近调度运行",
                "ok": not enabled_configs,
                "severity": "warn" if enabled_configs else "ok",
                "detail": "无运行历史",
                "hint": "若已启用调度，请确认外部任务执行后会调用 external-heartbeat",
            }
        )
    else:
        row = recent_runs[0]
        status = str(row.get("status") or "unknown").lower()
        checks.append(
            {
                "key": "external_scheduler_recent_run",
                "label": "最近调度运行",
                "ok": status == "ok",
                "severity": "ok" if status == "ok" else "warn",
                "detail": f"job={row.get('job_name') or '-'} status={status} at={row.get('last_seen_at') or '-'}",
                "hint": "当 status 非 ok 时，先检查采集脚本日志与 API 返回错误",
            }
        )
    errors = sum(1 for item in checks if item.get("severity") == "error")
    warns = sum(1 for item in checks if item.get("severity") == "warn")
    return {"checked_at": checked_at, "ok": errors == 0, "error_count": errors, "warn_count": warns, "checks": checks}


def workflow_run_readiness_public(app_obj: FastAPI, monitor_id: str | None = None) -> dict:
    from app.services.news_analysis_service import build_news_price_analysis

    checked_at = datetime.now(timezone.utc).isoformat()
    checks: list[dict] = []
    overview = openclaw_work_overview_public(app_obj)
    selected_monitor_id = (
        (monitor_id or "").strip()
        or str(((overview.get("price_monitoring") or {}).get("recent") or [{}])[0].get("monitor_id") or "").strip()
    )
    gateway = openclaw_gateway_status_public()
    checks.append(
        {
            "key": "gateway",
            "label": "OpenClaw Gateway",
            "ok": bool(gateway.get("ok")),
            "severity": "ok" if gateway.get("ok") else "error",
            "detail": gateway.get("detail") or "-",
            "hint": "请先确保 OpenClaw Gateway sidecar 已启动并可访问",
        }
    )
    if not selected_monitor_id:
        checks.append(
            {
                "key": "monitor_selection",
                "label": "monitor 选择",
                "ok": False,
                "severity": "error",
                "detail": "未找到可用 monitor_id",
                "hint": "请先在网页创建监测任务，或在请求中传入 monitor_id",
            }
        )
        errors = sum(1 for item in checks if item.get("severity") == "error")
        warns = sum(1 for item in checks if item.get("severity") == "warn")
        return {
            "checked_at": checked_at,
            "ok": errors == 0,
            "error_count": errors,
            "warn_count": warns,
            "selected_monitor_id": "",
            "checks": checks,
        }
    summary: dict = {}
    if not settings.monitoring_database_url:
        checks.append(
            {
                "key": "monitoring_db",
                "label": "价格数据库",
                "ok": False,
                "severity": "error",
                "detail": "未配置 OPENCLAW_MONITORING_DATABASE_URL",
                "hint": "请先配置 monitoring DB 并重启服务",
            }
        )
    else:
        try:
            summary = MonitoringService(settings.monitoring_database_url).get_summary(
                monitor_id=selected_monitor_id,
                window_days=7,
            )
            obs_count = int(summary.get("observation_count") or 0)
            checks.append(
                {
                    "key": "monitor_observations",
                    "label": "monitor 观测数据",
                    "ok": obs_count > 0,
                    "severity": "ok" if obs_count > 0 else "warn",
                    "detail": f"monitor={selected_monitor_id} 最近7天观测={obs_count}",
                    "hint": "若为 0，请先让 OpenClaw/外部任务写入 observations/ingest",
                }
            )
        except Exception:  # noqa: BLE001
            checks.append(
                {
                    "key": "monitor_observations",
                    "label": "monitor 观测数据",
                    "ok": False,
                    "severity": "error",
                    "detail": public_error_detail(context="monitor summary check"),
                    "hint": "确认 monitor_id 是否存在且 monitoring DB 可访问",
                }
            )
    configs = external_scheduler_configs_public().get("configs", [])
    monitor_cfg = [
        row for row in configs if str(row.get("monitor_id") or "").strip() == selected_monitor_id and bool(row.get("enabled"))
    ]
    checks.append(
        {
            "key": "scheduler_binding",
            "label": "外部调度绑定",
            "ok": bool(monitor_cfg),
            "severity": "ok" if monitor_cfg else "warn",
            "detail": f"monitor 绑定的启用配置数={len(monitor_cfg)}",
            "hint": "建议至少存在 1 条 enabled 调度配置，确保持续采集",
        }
    )
    recent_runs = external_scheduler_run_history_public(limit=200).get("runs", [])
    monitor_runs = [row for row in recent_runs if str(row.get("monitor_id") or "").strip() == selected_monitor_id]
    if not monitor_runs:
        checks.append(
            {
                "key": "scheduler_heartbeat",
                "label": "最近心跳",
                "ok": False,
                "severity": "warn",
                "detail": "该 monitor 暂无 external-heartbeat 记录",
                "hint": "请检查外部任务执行后是否调用了 external-heartbeat",
            }
        )
    else:
        latest = monitor_runs[0]
        status = str(latest.get("status") or "unknown").lower()
        seen_at = parse_iso_dt(str(latest.get("last_seen_at") or ""))
        stale = seen_at is None or (datetime.now(timezone.utc) - seen_at.astimezone(timezone.utc)) > timedelta(hours=24)
        ok = status == "ok" and not stale
        checks.append(
            {
                "key": "scheduler_heartbeat",
                "label": "最近心跳",
                "ok": ok,
                "severity": "ok" if ok else "warn",
                "detail": f"status={status} last_seen_at={latest.get('last_seen_at') or '-'} stale={stale}",
                "hint": "建议至少每24小时有一次 status=ok 的心跳",
            }
        )
    try:
        analysis = build_news_price_analysis(
            monitor_id=selected_monitor_id,
            keyword=None,
            keywords=None,
            window_days=7,
            news_hours=72,
            horizon="24h",
        )
        checks.append(
            {
                "key": "analysis_dry_run",
                "label": "联合分析链路",
                "ok": True,
                "severity": "ok",
                "detail": "dry-run 成功："
                + f"forecast={analysis.get('forecast') or '-'} "
                + f"news_count={analysis.get('news_count') or 0}",
                "hint": "链路可执行；如需产出报告可点击“立即生成联合分析”",
            }
        )
    except Exception:  # noqa: BLE001
        checks.append(
            {
                "key": "analysis_dry_run",
                "label": "联合分析链路",
                "ok": False,
                "severity": "error",
                "detail": public_error_detail(context="analysis dry-run"),
                "hint": "请先修复数据库配置、monitor 数据或新闻库连接后重试",
            }
        )
    errors = sum(1 for item in checks if item.get("severity") == "error")
    warns = sum(1 for item in checks if item.get("severity") == "warn")
    return {
        "checked_at": checked_at,
        "ok": errors == 0,
        "error_count": errors,
        "warn_count": warns,
        "selected_monitor_id": selected_monitor_id,
        "selected_keyword": str(summary.get("keyword") or ""),
        "checks": checks,
    }


def derive_insights_from_report(report: dict) -> dict:
    """Client-compatible insight derivation for legacy reports without insights field."""
    insights = report.get("insights")
    if isinstance(insights, dict) and insights:
        return insights

    analysis = str(report.get("analysis") or "")
    items = report.get("items") or []
    bullish = bearish = neutral = 0
    for item in items[:12]:
        txt = f"{item.get('title') or ''} {item.get('summary') or ''}"
        s = sentiment_from_text(txt)
        if s == "bullish":
            bullish += 1
        elif s == "bearish":
            bearish += 1
        else:
            neutral += 1
    if bullish > bearish:
        sentiment = "bullish"
    elif bearish > bullish:
        sentiment = "bearish"
    else:
        sentiment = sentiment_from_text(analysis)

    risk_level = "medium"
    risk_tokens_high = ("暴跌", "危机", "制裁", "违约", "中断")
    risk_tokens_low = ("平稳", "稳定", "缓和", "复苏")
    if any(t in analysis for t in risk_tokens_high):
        risk_level = "high"
    elif any(t in analysis for t in risk_tokens_low):
        risk_level = "low"

    confidence = "中"
    if "置信度" in analysis:
        if "高" in analysis:
            confidence = "高"
        elif "低" in analysis:
            confidence = "低"

    forecast = "震荡"
    if "上行" in analysis or "偏强" in analysis:
        forecast = "上行"
    elif "下行" in analysis or "偏弱" in analysis:
        forecast = "下行"

    return {
        "sentiment": sentiment,
        "risk_level": risk_level,
        "market_impact": analysis[:200] + ("…" if len(analysis) > 200 else ""),
        "confidence": confidence,
        "forecast": forecast,
        "news_sentiment_counts": {"bullish": bullish, "bearish": bearish, "neutral": neutral},
    }
