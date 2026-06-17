# 系统设计

> 后端分层与服务边界。概览见 [architecture.md](../00-overview/architecture.md)。

## 做什么

描述 FastAPI 后端如何组织代码、编排业务、连接三库与 Gateway。

## 关键组件

```
API (api/v1/) → Service (services/) → DB (db/)
```

| 服务 | 路径 | 职责 |
|------|------|------|
| IntakeService | `services/intake_service.py` | 报告幂等、入队 |
| JobRunner | `workers/job_runner.py` | 渲染、可选 Git 发布 |
| TokenService | `services/token_service.py` | 余额预检、扣费 |
| MonitoringService | `services/monitoring_service.py` | 价格监测 |
| NewsAnalysisService | `services/news_analysis_service.py` | 联合分析 |
| openclaw_chat_bridge | `services/openclaw_chat_bridge.py` | Gateway WS 桥 |
| chat_run_store | `services/chat_run_store.py` | 对话 run 内存态 |

| 鉴权 | 机制 |
|------|------|
| JWT | Access + HttpOnly Refresh Cookie |
| Agent | per-user `X-Api-Key` |
| Legacy | `OPENCLAW_LEGACY_API_KEY_ENABLED`（默认 false） |

**例外 KI-001**：`news_analysis_service` 逆依赖 `intake_service`，待注入重构。

## 数据流

### 报告流水线

```
OpenClawReportIn → IntakeService → raw JSON → JobRunner → rendered + DB → published
```

### 联合分析

| 触发 | 入口 |
|------|------|
| Agent | `POST /openclaw/analysis/news-trigger` |
| 门户 | `POST /public/workflow/analysis/run` |

→ `NewsAnalysisService` 聚合新闻+价格 → 可选 `publish:true` 入队报告。

### 门户对话

```
SPA ─WSS─► chat.py ─► openclaw_chat_bridge ─► Gateway
              └── chat_run_store ◄── GET /chat/runs/{key}
```

USER → `portal-readonly` + portal device；ADMIN → `main` + admin device。

## 示例

```python
# 分层：API 只做路由，业务在 Service
# app/api/v1/openclaw.py
ingest_id, status = intake_service.ingest(report, request_id, user_id=user.id)
```

```bash
# 外采价格写入（默认不服务端 scrape）
curl -X POST "$BASE/api/v1/openclaw/monitoring/$MID/observations/ingest" \
  -H "X-Api-Key: $KEY" -d '{"price": 100.5, "currency": "CNY"}'
```

| 相关 | 文档 |
|------|------|
| API | [api.md](api.md) |
| 计费 | [../04-product/billing.md](../04-product/billing.md) |
| Gateway 隔离 | [gateway-isolation.md](gateway-isolation.md) |
