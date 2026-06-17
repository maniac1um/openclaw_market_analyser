# API 参考

> 基础 URL `/api/v1` · Swagger `/docs` · 实现 `app/api/v1/` + `app/schemas/`

## 做什么

HTTP 契约权威来源：鉴权方式、路由分组、请求/响应约定。

## 关键组件

| 分组 | 前缀 | 鉴权 | 用途 |
|------|------|------|------|
| 健康 | `/healthz` | 无 | 存活探测 |
| 认证 | `/public/auth/*` | — | 注册、登录、API Key |
| Agent | `/openclaw/*` | `X-Api-Key` | 报告、监测、新闻、分析 |
| 门户 | `/public/*` | JWT / Key | 读、工作流、计费、通知 |
| 对话 | `/chat/*` | JWT / Cookie / Key | WS + run 轮询 |

**隔离规则**：除 `/healthz` 外均需鉴权；跨用户 ID → **404**。

| 状态码 | 含义 |
|--------|------|
| 402 | Token 不足 |
| 409 | 幂等冲突 |
| 429 | 速率限制 |

## 数据流

### Agent 发报告

```
POST /openclaw/reports ──202──► GET /openclaw/reports/{id} ──► published
                                      │
GET /public/reports ◄─────────────────┘ SPA 展示
```

### 门户登录 → 调用

```
POST /auth/login → Cookie/JWT → GET /public/reports
                              → POST /public/workflow/analysis/run
```

## 示例

### 报告入站

```bash
curl -X POST http://localhost:8000/api/v1/openclaw/reports \
  -H "X-Api-Key: $KEY" \
  -H "X-Request-Id: $(uuidgen)" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "task-001",
    "keyword": "demo",
    "items": [{"title": "新闻", "url": "https://example.com", "source": "a"}],
    "analysis": "简要分析"
  }'
# → {"ingest_id":"...","status":"queued"}
```

### 常用端点速查

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/openclaw/reports` | 报告入站 |
| GET | `/openclaw/reports/{id}` | 入站状态 |
| POST | `/openclaw/monitoring/bootstrap` | 创建监测 |
| POST | `/openclaw/monitoring/{id}/observations/ingest` | 价格入库 |
| POST | `/openclaw/analysis/news-trigger` | 联合分析 |
| GET | `/public/reports` | 报告列表 |
| GET | `/public/users/balance` | Token 余额 |
| WS | `/chat/ws` | 门户对话 |

完整端点列表见 Swagger `/docs` 或 `app/api/v1/*.py`。

| Skill 对照 | [../_agent/crosswalk.md](../_agent/crosswalk.md) |
