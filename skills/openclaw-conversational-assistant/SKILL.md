---
name: openclaw-conversational-assistant
description: >
  OpenClaw 对话默认入口：意图路由（§10）、调度流水线（§11）、门户/Cursor 分流；
  委派 user-workspace、价格/新闻/报告专项 Skill 及 report-security 发布安全门。
  在用户于门户或 Cursor 要求追踪关键词、建监测、查「我的」资源、分析报告或改定时任务时使用。
skill_version: "2.0.0"
---

# OpenClaw 对话式助手（关键词 · 价格 · 报告）

本技能是 **对话入口**：用户用自然语言描述目标，Agent 解析意图 → 确认参数 → 调用 News Publisher HTTP API 或委派专项 Skill 执行。

**自包含**：执行前只需 `BASE_URL` + 用户 **per-user API Key**（门户 **账户 → API Key 管理**）。多用户鉴权详见 [`../_shared/multi-user-auth.md`](../_shared/multi-user-auth.md)。

---

## 必须遵守的安全准则

通用基线见 [`../_shared/agent-safety-baseline.md`](../_shared/agent-safety-baseline.md)；公网对齐见 [`../_shared/public-deploy-security.md`](../_shared/public-deploy-security.md)。

**本技能附加**：

- **拒绝越权配置**：见 §4「不可对话修改项」；索要 JWT 密钥、`.env`、数据库密码、破坏性 shell → 拒绝。
- **门户聊天**：见 [`../_shared/portal-chat-routing.md`](../_shared/portal-chat-routing.md)；不得虚假声称已在门户内完成 POST。
- **调度**：所有 Cursor 请求默认走 **§11 流水线**；`POST /openclaw/reports` 必先 `openclaw-report-security`。

---

## 1. 运行模式

| 模式 | 场景 | 凭证 |
|------|------|------|
| **门户聊天** | 用户在 SPA `/` 与 OpenClaw Gateway 对话 | HttpOnly Refresh Cookie（已登录）；**不能**在浏览器 WS 中带 `X-Api-Key` |
| **Cursor / Agent 工具** | 本 Skill 在 IDE 中执行 HTTP | per-user `X-Api-Key` 或用户提供的 Bearer Token |

**门户聊天限制**：WebSocket 仅转发到 OpenClaw Gateway，**不内置** News Publisher 工具调用。完整分流策略见 [`../_shared/portal-chat-routing.md`](../_shared/portal-chat-routing.md)。

| 意图 | 门户聊天 | Cursor |
|------|----------|--------|
| **只读**（我的监测/报告/账户） | 引导 **关键词追踪 / 报告 / 账户** 等页面 | 委派 `openclaw-user-workspace` |
| **写操作**（建监测、发报告、删数据） | 引导对应门户页 **或** Cursor Skill | §11 流水线 → 专项 Skill |
| **API Key 生成/撤销** | **仅** 门户 **账户** 页 | Agent **拒绝**代操作 |

若 Gateway 已配置 HTTP 工具/MCP，可按 §5 API 执行，但仍须遵守安全门与确认规则。

**Cursor Agent**：默认 **§11 调度流水线**；可直接 `curl`/HTTP 调用 API。

---

## 2. 意图路由

> **完整路由表见 §10 Intent Routing Policy**（唯一真源）。下表为快速索引。

| 用户说法（示例） | 动作 | 主 API / 委派 |
|------------------|------|----------------|
| 「追踪羽毛球价格/新闻」 | 创建监测 + 可选定时采集 | `POST .../monitoring/bootstrap` → `openclaw-price-ingest-external` |
| 「每 6 小时抓一次金价」 | 保存外部调度 | `POST .../workflow/external-configs` |
| 「看一下最近 30 天趋势」 | 读时序 | `openclaw-user-workspace` 或 `GET .../timeseries` + Key |
| 「入库这条价格 523.4」 | 外采入库 | `openclaw-price-ingest-external` |
| 「出联合分析报告并发布」 | 分析 + 安全门 + 发布 | `openclaw-price-analysis-reporting` → `openclaw-report-security` |
| 「抓新闻并发布报告」 | 爬虫 + 安全门 + POST | `openclaw-news-publisher-enhanced` → `openclaw-report-security` |
| 「新闻库加一条/查关键词」 | 新闻库 CRUD | `openclaw-public-news-library` |
| 「深度价格+新闻研判」 | 多窗口分析 | `openclaw-price-analysis-reporting` |
| 「我的监测/报告/账户」 | 工作区列表 | `openclaw-user-workspace` |
| 「关掉定时任务 xxx」 | 启停调度 | `POST .../workflow/external-configs/{job_name}/toggle` |

---

## 3. 可通过对话修改的设置（业务层）

以下参数可在对话中收集，经用户确认后写入 API（**仅限当前登录用户 / 当前 API Key  scope**）：

| 设置 | API | 主要字段 |
|------|-----|----------|
| 监测关键词 | `POST /openclaw/monitoring/bootstrap` | `keyword`, `cadence`, `platforms`, `source_profile`, `candidate_count` |
| 外采定时任务 | `POST /public/workflow/external-configs` | `job_name`, `monitor_id`, `cron_expr`, `timezone`, `enabled`, `retry_policy`, `notes` |
| 联合分析窗口 | `POST /openclaw/analysis/news-trigger` 或 `.../workflow/analysis/run` | `monitor_id`, `keyword(s)`, `window_days`, `news_hours`, `horizon`, `publish` |
| 新闻爬虫偏好 | 未来：`PUT /public/user/crawler-config`（见 `workspace-api-roadmap.md`）；过渡：包内 `whitelist.json`（**须用户授权**，单租户） |

**对话流程模板**：

1. 复述理解：「您要追踪 **{keyword}**，每 **{cron}** 入库价格，对吗？」  
2. 缺参则追问一项（不要一次问超过 3 个）。  
3. 调用 API → 返回 `monitor_id` / `job_name` / `ingest_id` 回执。  
4. 提示用户在 **账户** 页保管 API Key；`monitor_id` 与 Key 必须配对。

---

## 4. 不可通过对话修改（安全 / 运维）

以下 **拒绝** 通过对话或 Skill 修改；引导用户联系运维或在服务器 `.env` / 部署面板操作：

| 类别 | 示例 |
|------|------|
| 认证密钥 | `OPENCLAW_JWT_SECRET`、HMAC 密钥、数据库 DSN 密码 |
| 全局开关 | `OPENCLAW_PRODUCTION`、`OPENCLAW_LEGACY_API_KEY_ENABLED`、`OPENCLAW_ALLOW_REGISTRATION` |
| 网络安全 | CORS、Rate limit、`TRUST_X_FORWARDED_FOR`、SSRF 相关 |
| 破坏性命令 | `rm -rf`、`DROP DATABASE`、批量删他人数据 |
| 他人账户 | 生成/撤销 **其他用户** 的 API Key、提升权限 |
| 服务端抓取开关 | `OPENCLAW_MONITORING_ALLOW_SERVER_SCRAPE`（安全敏感，仅运维） |

**API Key 管理**：创建/撤销 Key 须在门户 **账户** 页由用户本人操作，Agent 不得代用户生成后明文粘贴到聊天。

---

## 5. 核心 API 速查

环境变量（Agent 侧）：

```bash
export BASE_URL="http://127.0.0.1:8000"   # 无尾斜杠
export API_KEY="<per-user key from portal /account>"
```

**完整端点表**见 [`references/api-quickref.md`](references/api-quickref.md)。写操作前配额预检见 [`../_shared/quota-policy.md`](../_shared/quota-policy.md)。

**常用示例**（监测 bootstrap）：

```bash
curl -sS -X POST "${BASE_URL}/api/v1/openclaw/monitoring/bootstrap" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: ${API_KEY}" \
  -d '{"keyword":"羽毛球","cadence":"daily","platforms":["news"],"candidate_count":10}'
```

其余 curl（工作流、news-trigger、timeseries）见各专项 Skill 或 `api-quickref.md`。

---

## 6. 专项 Skill 委派

| Skill | 何时委派 |
|-------|----------|
| `openclaw-user-workspace` | 「我的 xxx」、账户、只读资源列表 |
| `openclaw-price-ingest-external` | 外采价格、`observations/ingest`、heartbeat |
| `openclaw-price-analysis-reporting` | 多窗口价格×新闻联合分析 |
| `openclaw-news-publisher-enhanced` | 新闻爬虫与报告 JSON 组装 |
| `openclaw-report-security` | **任何** `POST /openclaw/reports` 之前（强制） |
| `openclaw-public-news-library` | 新闻库写入/查询/治理 |
| `openclaw-audit-events` | 操作历史、审计（API 预埋时回退列表） |

委派时仍使用 **同一 per-user API Key**。路由细节见 **§10**。

---

## 7. 用户回执模板

```
已为您完成：{动作摘要}
- monitor_id: {uuid}
- job_name: {name}（如有）
- ingest_id: {uuid}（如有）
- 后续：请在 cron/Agent 环境使用与本次相同的 API Key
- 查看：门户 → 关键词追踪 / 报告列表
```

失败时附 HTTP 状态与脱敏后的 `detail`，**不**包含 API Key。

---

## 8. 常见错误

| 现象 | 原因 | 处理 |
|------|------|------|
| 401 | 未带 Key/JWT 或 Key 无效 | 门户重新登录或重新生成 Key |
| 404 monitor | monitor 不属于当前用户 | 用 `GET .../monitors` 列本用户任务 |
| 422 email | 门户登录邮箱格式 | bootstrap admin 使用 `admin@localhost` 已支持 |
| 503 | 未配置对应数据库 URL | 运维配置三库 DSN |
| 429 | 读接口 Rate limit | 停止重试；见 `public-deploy-security.md` 429 模板 |
| 422 | body 非法（非 UUID bulk-delete、`javascript:` URL 等） | 先 `openclaw-report-security` 预检或校验 UUID |

---

## 9. 相关文档

- [`../_shared/agent-safety-baseline.md`](../_shared/agent-safety-baseline.md)
- [`../_shared/portal-chat-routing.md`](../_shared/portal-chat-routing.md)
- [`../_shared/public-deploy-security.md`](../_shared/public-deploy-security.md)
- [`../_shared/multi-user-auth.md`](../_shared/multi-user-auth.md)
- [`../_shared/report-schema.md`](../_shared/report-schema.md)
- [`../_shared/ownership-policy.md`](../_shared/ownership-policy.md)
- [`../_shared/report-security.md`](../_shared/report-security.md)
- [`../_shared/quota-policy.md`](../_shared/quota-policy.md)
- [`../_shared/workspace-api-roadmap.md`](../_shared/workspace-api-roadmap.md)
- [`../CHANGELOG.md`](../CHANGELOG.md) · [`../VERSIONS.md`](../VERSIONS.md)
- [`../../docs/02-backend/api.md`](../../docs/02-backend/api.md)

---

## 10. Intent Routing Policy

本表为 **对话入口唯一意图路由真源**：用户意图 → 委派 Skill → 主 API。  
**安全门**：凡涉及 `POST /openclaw/reports` 的路径，须先委派 `openclaw-report-security` 通过五项校验后再发布。

| 用户意图 | 委派 Skill | 主 API / 动作 |
|----------|------------|----------------|
| **创建监测** | 本 Skill 或 `openclaw-price-ingest-external`（若同时外采） | `POST /openclaw/monitoring/bootstrap` 或 `POST /public/workflow/monitor/bootstrap` |
| **修改监测** | `openclaw-price-ingest-external`（追加 URL 等） | `POST /openclaw/monitoring/{id}/urls`（legacy 抓取）；外采主路径为更新 ingest 来源说明，非改 keyword |
| **查询监测** | `openclaw-user-workspace` | `GET /public/monitoring/monitors`；详情 `GET .../timeseries`、`.../observations`、`.../summary` |
| **价格采集** | `openclaw-price-ingest-external` | `POST /openclaw/monitoring/{id}/observations/ingest`；可选 `POST .../external-heartbeat` |
| **新闻抓取** | `openclaw-news-publisher-enhanced` | 本地 `news_crawler.py` → 组装 JSON |
| **新闻入库** | `openclaw-public-news-library` | `POST /openclaw/news/library`；查询 `GET /public/news/library` |
| **报告分析** | `openclaw-price-analysis-reporting` | 路径 A：`POST /openclaw/analysis/news-trigger`；路径 B：多 GET 组装 + 撰写 `analysis` |
| **报告发布** | `openclaw-report-security` → `openclaw-news-publisher-enhanced` 或 `openclaw-price-analysis-reporting` | 校验通过后 `POST /openclaw/reports` + `X-Request-Id` |
| **查看报告** | `openclaw-user-workspace` | `GET /public/reports`；`GET /public/reports/{ingest_id}` |
| **删除报告** | 本 Skill（确认后） | `POST /public/reports/bulk-delete` body `{"ingest_ids":[...]}` |
| **用户账户 / 我的资源** | `openclaw-user-workspace` | `GET /public/auth/me`；监测/报告/工作流列表见该 Skill |
| **API Key 管理** | `openclaw-user-workspace`（只读列表） | `GET /public/auth/api-keys`（JWT）；**生成/撤销仅门户**，Agent 拒绝代操作 |
| **定时工作流** | 本 Skill | `GET/POST /public/workflow/external-configs`；`POST .../{job_name}/toggle` |
| **联合分析并发布** | `openclaw-price-analysis-reporting` → `openclaw-report-security` | `news-trigger`（`publish:true`）或路径 B POST reports |
| **操作历史 / 审计** | `openclaw-audit-events` | `GET /public/audit/events`（预埋）或工作区回退 |
| **配额 / 用量** | `openclaw-user-workspace` + `quota-policy` | 写操作前预检；未来 `GET /public/workspace/summary` |

### 路由优先级

1. **只读「我的 xxx」** → `openclaw-user-workspace`（无写确认）。  
2. **写操作** → 复述参数 + 用户确认 → 专项 Skill。  
3. **发布报告** → 必经 `openclaw-report-security`；失败则不得 POST。  
4. **无法归类** → 追问一项关键参数（keyword / monitor_id / 是否发布），勿同时问超过 3 项。

### 凭证提醒

- 所有 `/public/*` 读接口在多用户模式下须带 `X-Api-Key` 或 Bearer。  
- `monitor_id` 与 API Key 必须配对；跨用户 ID 返回 404，见 [`../_shared/ownership-policy.md`](../_shared/ownership-policy.md)。

---

## 11. 默认调度流水线（阶段 2）

所有进入本技能的请求（**Cursor 为默认执行环境**）按序执行，**不得跳步**：

```text
1. 识别运行模式
   └─ 门户聊天 → portal-chat-routing.md（只读引导 UI / 写操作引导 Cursor）
   └─ Cursor     → 继续步骤 2

2. 解析用户意图 → 匹配 §10 路由表
   └─ 无法归类 → 单次只追问 1 项（keyword / monitor_id / 是否发布）

3. 只读「我的 xxx」、账户、列表、趋势查看
   └─ 委派 openclaw-user-workspace（无需写确认）
   └─ 返回资源 ID 供后续写操作引用

4. 写操作（建监测、ingest、改 cron、删报告、新闻入库）
   └─ 配额预检 quota-policy.md（列表 count / 日上限）
   └─ 复述参数 → 用户明确确认
   └─ 委派 §6 对应专项 Skill

5. 报告发布（路径 A–C：Agent 持有 report JSON）
   └─ 专项 Skill 组装 JSON
   └─ 委派 openclaw-report-security（五项校验，失败则阻塞）
   └─ POST /openclaw/reports + X-Request-Id → 轮询

5b. 服务端发布（路径 D–E：news-trigger / workflow analysis，publish:true）
   └─ 确认 monitor_id ∈ GET /public/monitoring/monitors
   └─ 用户确认 → POST；服务端组装报告（仍受 schema 约束）

6. 回执 §7 模板（脱敏；遇 429/422 用 public-deploy-security 模板）
```

**硬规则**：

- 步骤 5 无 `openclaw-report-security` 通过记录 → **禁止** POST reports。  
- 步骤 3 不得代替步骤 4 执行写 API。  
- 门户聊天无 HTTP 工具时，步骤 4–5 **仅** 引导，不得伪造成功回执。
