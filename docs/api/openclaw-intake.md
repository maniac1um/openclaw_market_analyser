# OpenClaw 接入接口文档

> **多用户 SaaS（2026-06）**：除 `/healthz` 外，读写 API 须 **JWT**（门户）或 **per-user `X-Api-Key`**（Agent）。Key 在门户 **账户 → API Key 管理** 生成。Legacy 全局 Key 默认关闭（`OPENCLAW_LEGACY_API_KEY_ENABLED=false`）。详见 [multi-user/MULTI_USER_MIGRATION_PLAN.md](../multi-user/MULTI_USER_MIGRATION_PLAN.md) 与 Skill `skills/_shared/multi-user-auth.md`。

## 接口地址

- `POST /api/v1/openclaw/reports`

## 请求头

- `X-Api-Key`（必填）
- `X-Request-Id`（必填，用于幂等键）
- `X-Signature`（可选；仅在开启签名校验时必填）

## 请求体（JSON）

```json
{
  "task_id": "task-20260401-001",
  "keyword": "羽毛球",
  "time_range": {
    "start": "2026-03-01T00:00:00+00:00",
    "end": "2026-04-01T00:00:00+00:00"
  },
  "sources": ["source-a", "source-b"],
  "items": [
    {
      "title": "示例新闻标题",
      "source": "source-a",
      "url": "https://example.com/1",
      "published_at": "2026-03-20T10:00:00+00:00",
      "price": 89.9,
      "currency": "CNY",
      "summary": "..."
    }
  ],
  "analysis": "趋势分析文本",
  "insights": {
    "sentiment": "bullish",
    "risk_level": "medium",
    "market_impact": "短期供需偏紧，价格中枢上移",
    "confidence": "中",
    "forecast": "上行"
  },
  "generated_title": "不同时间段内羽毛球价格变化趋势分析",
  "generated_at": "2026-04-01T11:00:00+00:00"
}
```

`insights` 为可选字段，用于前端 Dashboard 洞察卡片；省略时由服务端/前端从 `analysis` 与 `items` 推导。

## 响应

- 成功：`202 Accepted`

```json
{
  "ingest_id": "uuid",
  "status": "queued"
}
```

## 状态查询

- `GET /api/v1/openclaw/reports/{ingest_id}`
- 状态枚举：`queued`、`processing`、`published`、`failed`

---

## 价格监测（OpenClaw 外采 + 服务端入库）

与报告入站相同前缀下的监测路由均在 **`/api/v1/openclaw/monitoring/...`**。完整说明与 curl 示例见仓库根目录 [README.md](../../README.md) 中的「价格监测」章节。

### 设计约定

- 默认 **`OPENCLAW_MONITORING_ALLOW_SERVER_SCRAPE=false`**：服务端不对监测 URL 做公网 HTTP 抓取；由 OpenClaw 完成采集与解析后 **`POST /api/v1/openclaw/monitoring/{monitor_id}/observations/ingest`** 写入 `price_observations`。
- **`POST .../monitoring/bootstrap`**：默认仅创建监测任务并插入一条占位 URL；`candidate_count` / `platforms` / `source_profile` 仅在开启服务端抓取时用于生成候选 URL。
- **`POST .../monitoring/{monitor_id}/run-once`**：默认返回 `server_scrape_skipped: true`；仅当 `OPENCLAW_MONITORING_ALLOW_SERVER_SCRAPE=true` 时执行 legacy 网页抓取。
- **只读拉库**：`GET /api/v1/public/monitoring/monitors`、`GET .../timeseries`、`GET .../observations` 须带 **per-user `X-Api-Key`** 或 JWT，供 OpenClaw 定时读取本用户已存数据。

### 鉴权（多用户 SaaS）

**Per-user API Key（推荐）**：在门户 **账户 → API Key 管理** 生成，用于：

- 所有 `POST /api/v1/openclaw/*`
- 方案 B 下的 `GET /api/v1/public/*`（须带 `X-Api-Key` 或 `Authorization: Bearer`）

**Legacy 全局 Key**：环境变量 `OPENCLAW_OPENCLAW_API_KEY` 在 `OPENCLAW_LEGACY_API_KEY_ENABLED=true` 时映射 ADMIN；关闭后失效。

**数据隔离**：每个 Key 仅访问所属用户的 `monitor_id` / `ingest_id` / 新闻库条目；跨用户 ID 返回 **404**。

除健康检查外，**不再**假设 public GET 无鉴权可读全库。详见 [`docs/multi-user/MULTI_USER_MIGRATION_PLAN.md`](../multi-user/MULTI_USER_MIGRATION_PLAN.md) 与 Skill [`../skills/_shared/multi-user-auth.md`](../skills/_shared/multi-user-auth.md)。

### 观测入库请求体（ingest）

```json
{
  "price": 523.4,
  "title": "可选",
  "currency": "CNY",
  "captured_at": "2026-04-10T12:00:00+08:00",
  "source_url": "https://example.com/quote",
  "raw_payload": {}
}
```

- `price` 必填；`captured_at` 可省略。

---

## 网页工作流控制台 API（public）

门户 **读/写** 在 multi-user 模式下均需 **JWT**（门户登录）或 **per-user `X-Api-Key`**，数据按用户隔离。

| 方法 | 路径 | 鉴权 |
|------|------|------|
| GET | `/api/v1/public/workflow/state` | JWT 或 `X-Api-Key` |
| GET | `/api/v1/public/workflow/gateway-status` | JWT 或 `X-Api-Key` |
| GET | `/api/v1/public/workflow/diagnostics` | JWT 或 `X-Api-Key` |
| GET | `/api/v1/public/workflow/run-readiness` | JWT 或 `X-Api-Key` |
| GET | `/api/v1/public/workflow/external-runs` | JWT 或 `X-Api-Key` |
| GET | `/api/v1/public/workflow/external-configs` | JWT 或 `X-Api-Key` |
| POST | `/api/v1/public/workflow/external-configs` | JWT 或 `X-Api-Key` |
| POST | `/api/v1/public/workflow/external-configs/{job_name}/toggle` | JWT 或 `X-Api-Key` |
| POST | `/api/v1/public/workflow/monitor/bootstrap` | JWT（`CurrentUser`） |
| POST | `/api/v1/public/workflow/analysis/run` | JWT（`CurrentUser`） |

### 说明

- `workflow/state` 返回统一编排视图：`overview`、`gateway`、`internal_scheduler`、`external_scheduler_configs`、`external_scheduler_runs`。
- `workflow/gateway-status` 单独探测 OpenClaw Gateway sidecar 连通性（握手、延迟、错误详情）。
- `workflow/diagnostics` 提供“一键诊断”聚合结果（Gateway、三库连通、调度配置、最近运行）及修复建议。
- `workflow/run-readiness` 提供“一键可运行性验证”（monitor 观测、调度绑定、心跳新鲜度、联合分析 dry-run）。
- `/workflow` 前端页面已将执行类按钮与诊断/验证按钮分组展示，结果区支持“粘性显示”（避免自动刷新覆盖）。
- `workflow/monitor/bootstrap` 是 `openclaw/monitoring/bootstrap` 的网页封装入口。
- `workflow/analysis/run` 与新闻触发联合分析逻辑保持一致，可选择 `publish=true|false`。

---

## external-heartbeat 持久化语义（更新）

`POST /api/v1/openclaw/monitoring/external-heartbeat` 现在除了维护进程内最近状态外，还会把事件写入监测库：

- `external_scheduler_runs`：运行事件历史（按 `last_seen_at` 排序）
- `external_scheduler_configs`：网页端维护的外部调度配置（job 与 cron 元信息）

因此服务重启后，`public/workflow/external-runs` 仍可回看历史，便于排障与审计。

---

## 新闻库 API

需配置 `OPENCLAW_NEWS_DATABASE_URL`。

| 方法 | 路径 | 鉴权 |
|------|------|------|
| POST | `/api/v1/openclaw/news/library` | API Key |
| GET | `/api/v1/openclaw/news/library` | API Key |
| GET | `/api/v1/public/news/library` | JWT 或 `X-Api-Key` |
| POST | `/api/v1/public/news/library/bulk-delete` | JWT 或 `X-Api-Key` |

---

## 新闻触发联合分析

`POST /api/v1/openclaw/analysis/news-trigger`（需 API Key）

```json
{
  "monitor_id": "<uuid>",
  "keyword": null,
  "window_days": 7,
  "news_hours": 72,
  "horizon": "24h",
  "publish": false
}
```

`publish: true` 时自动组装报告并入队发布。

---

## 公开报告读取（SPA）

| 方法 | 路径 |
|------|------|
| GET | `/api/v1/public/reports` |
| GET | `/api/v1/public/reports/{ingest_id}` |
| GET | `/api/v1/public/topic/cards` |
| POST | `/api/v1/public/reports/bulk-delete` |
