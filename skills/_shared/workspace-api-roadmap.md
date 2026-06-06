# 工作区 API 路线图（OpenClaw Skills 共用）

**状态**：**文档预埋** — 描述目标 SaaS API；**当前服务端可能未实现**。Agent 须以实际 HTTP 响应为准，未实现时回退 `openclaw-user-workspace` 现有列表接口。

---

## 1. 目标

| 能力 | 问题 | 目标 |
|------|------|------|
| **归属可见** | POST 报告后不知 `owner_user_id` | 入站响应返回 `owner_user_id` |
| **工作区过滤** | 列表仅全量 scope | 按 `keyword` / `monitor_id` / 时间过滤 |
| **用户爬虫配置** | `whitelist.json` 在共享 Skill 目录 | 每用户服务端存储种子/白名单 |
| **审计** | 无操作追溯 | 审计事件流（见 `openclaw-audit-events`） |

---

## 2. 报告入站响应扩展（预埋）

### 当前

```json
{ "ingest_id": "uuid", "status": "queued" }
```

### 目标 `POST /api/v1/openclaw/reports` 202

```json
{
  "ingest_id": "uuid",
  "status": "queued",
  "owner_user_id": "uuid",
  "task_id": "string",
  "quota_remaining": { "reports_daily": 18 }
}
```

**Skill 规则**：

- 仍 **禁止** 在请求体提交 `owner_user_id`（见 `ownership-policy.md`）。
- 回执给用户时展示 `ingest_id`；`owner_user_id` 仅用于 Agent 自检（应与当前 Key 用户一致）。

### 目标 `GET /api/v1/openclaw/reports/{ingest_id}`

响应增加：`owner_user_id`、`monitor_id`（若已关联）。

---

## 3. 工作区列表过滤（预埋）

### 报告列表

```
GET /api/v1/public/reports
  ?keyword=羽毛球
  &monitor_id={uuid}
  &since=2026-06-01T00:00:00Z
  &until=2026-06-30T23:59:59Z
  &limit=50
  &offset=0
```

| 参数 | 说明 |
|------|------|
| `keyword` | 精确或包含匹配 `keyword` 字段 |
| `monitor_id` | 仅返回关联该监测的报告（需 DB 列或 payload 索引） |
| `since` / `until` | `generated_at` 窗口 |
| `limit` / `offset` | 分页；`limit` 最大 100 |

**当前回退**：`GET /public/reports` 无查询参数 → Agent 在侧过滤（仅小列表）。

### 监测列表

```
GET /api/v1/public/monitoring/monitors?keyword=黄金&limit=20
```

### 统一工作区摘要（预埋）

```
GET /api/v1/public/workspace/summary
```

```json
{
  "owner_user_id": "uuid",
  "counts": {
    "monitors": 3,
    "reports": 12,
    "reports_today": 2,
    "news_items": 45,
    "workflow_jobs": 2
  },
  "quota": {
    "monitors_limit": 10,
    "monitors_remaining": 7,
    "reports_daily_limit": 20,
    "reports_daily_remaining": 18
  }
}
```

**Skill**：实现后 `openclaw-user-workspace` 优先调用此接口。

---

## 4. 用户级爬虫配置 API（预埋）

替代 `openclaw-news-publisher-enhanced` 包内共享 `config/whitelist.json`。

### 端点（建议）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/public/user/crawler-config` | 返回当前用户 `seed_urls`、活跃源、偏好 |
| PUT | `/api/v1/public/user/crawler-config` | 合并更新（JWT 或 Key） |
| POST | `/api/v1/public/user/crawler-config/sources` | 添加并探测 URL |
| DELETE | `/api/v1/public/user/crawler-config/sources` | 按 URL 移除 |

### 存储模型（建议）

```json
{
  "owner_user_id": "uuid",
  "version": 1,
  "user_preferences": { "frequent_keywords": ["badminton"] },
  "active_sources": [
    { "url": "https://...", "category": "sports", "last_tested": "..." }
  ],
  "updated_at": "ISO8601"
}
```

### Skill 迁移规则

| 阶段 | 行为 |
|------|------|
| **现在** | 使用包内 `whitelist.json`；**禁止**多租户共写（见 §0） |
| **API 可用后** | `news_crawler.py` / `cli.py` 优先读服务端配置；本地文件仅缓存 |
| **Agent** | 对话改偏好 → 调 PUT，**不**改 Git 内 `whitelist.json` |

---

## 5. 与 report-schema 对齐

已发布视图字段见 [`report-schema.md`](report-schema.md)：`report_id`、`owner_user_id`、可选 `monitor_id`。

---

## 6. 实现状态检查

Agent 调用预埋接口时：

| 响应 | 处理 |
|------|------|
| **404** / **501** | 回退现有 `GET /public/*` 列表 |
| **200** | 使用新字段 |
| **503** | 数据库未配置；见各 Skill 排查 |

---

## 相关文档

- [`quota-policy.md`](quota-policy.md)
- `openclaw-user-workspace`
- `openclaw-audit-events`
- [`ownership-policy.md`](ownership-policy.md)
