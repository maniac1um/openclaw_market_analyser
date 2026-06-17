# 资源归属策略（OpenClaw Skills 共用）

**适用版本**：OpenClaw News Publisher 多用户 SaaS（2026-06 起）  
**原则**：所有租户资源必须可追溯到 `owner_user_id`；默认拒绝跨用户访问。

---

## Ownership Rules

### 规则 1 — 服务端为归属真源

- 资源的 `owner_user_id`（DB 列名通常为 `user_id`）**仅由服务端**在创建时根据鉴权上下文写入。
- Agent / 客户端 **不得** 在请求体中提交 `owner_user_id` 或 `user_id` 试图冒充他人。
- 读取、修改、删除均通过 `QueryContext.user_id` 过滤（实现见 `app/db/query_context.py`）。

### 规则 2 — 须归属的资源类型

| 资源 | 标识字段 | 存储 | 创建 API 示例 |
|------|----------|------|----------------|
| **Monitor** | `monitor_id` | 监测库 `price_monitors.user_id` | `POST /openclaw/monitoring/bootstrap` |
| **Observation** | `observation_id` | 监测库 `price_observations.user_id` | `POST .../observations/ingest` |
| **Report** | `ingest_id` / `report_id` | 主库 `reports.user_id` | `POST /openclaw/reports` |
| **Workflow 配置** | `job_name` | `external_scheduler_configs.user_id` | `POST /public/workflow/external-configs` |
| **API Key** | `key_id` | `api_keys.user_id` | `POST /public/auth/api-keys` |
| **News 库条目** | `id` | 新闻库 `news_library.user_id` | `POST /openclaw/news/library` |

### 规则 3 — 关联资源级联归属

- `price_monitor_urls`、`price_observations` 须与父 `monitor_id` 的 `user_id` 一致。
- `observations/ingest` 时，若 `monitor_id` 不属于当前用户 → **404**（`Monitor not found`）。
- Workflow 的 `monitor_id` 引用须为本用户 monitor，否则保存失败或后续执行 404。

### 规则 4 — 跨用户语义：404 而非 403

- 访问他人资源 ID 时，响应 **404**（或 bulk 操作中 `not_found` 计数增加），**不** 返回 403。
- **目的**：防止通过 ID 枚举探测他人物资是否存在。
- Agent **不得** 向用户暗示「该 ID 存在但无权限」。

### 规则 5 — ADMIN 角色

- `role=ADMIN` 可绕过 `owner_clause` 查询全库（运维/过渡 Legacy Key）。
- 普通 USER Skill **默认按 USER 行为**编写；不得指导普通用户获取 ADMIN 能力。

### 规则 6 — API Key 与 Monitor 配对

- 每个 `monitor_id` 由创建它的 API Key 所属用户拥有。
- Cron / 外部调度须使用 **与创建 monitor 时相同的 per-user Key**。
- 换 Key 不转移旧 monitor 归属；须用新 Key 重新 bootstrap 或门户迁移（若未来支持）。

---

## 禁止行为

| 禁止 | 说明 |
|------|------|
| **跨用户访问** | 不得用用户 A 的 Key 读取用户 B 的 `monitor_id`、`ingest_id`、`job_name` |
| **跨用户修改** | 不得更新他人 workflow 配置、追加他人 monitor URL |
| **跨用户删除** | `bulk-delete` 中他人 ID 不计入 `deleted`，且不应泄露存在性 |
| **伪造归属字段** | 请求体携带 `user_id` / `owner_user_id` |
| **猜测 UUID** | 不得暴力遍历 `ingest_id`；仅使用列表 API 返回的 ID |
| **共享 Key** | 多用户不得共用同一 API Key |

---

## Ownership Validation

Agent 在读写资源前应执行以下校验（逻辑校验；服务端为最终裁判）。

### 读操作前

1. 确认已设置 per-user `X-Api-Key` 或有效 JWT。
2. 若资源 ID 来自用户口述，先 `GET` 列表接口确认 ID 出现在本用户结果中。
3. 若 `GET` 返回 404，停止并提示「请从您的监测/报告列表中选取」。

### 写操作前

1. 写操作前须用户明确确认（见 conversational-assistant 安全准则）。
2. `monitor_id`：先 `GET /public/monitoring/monitors` 验证存在且属于当前用户。
3. `ingest` / `summary` / `news-trigger`：使用的 `monitor_id` 须通过上一步。
4. Workflow 保存：`job_name` 在同一用户下唯一；`monitor_id` 须本用户所有。

### 发布报告前

1. 不要求提交 `owner_user_id`。
2. 若 payload 含 `monitor_id`（扩展字段），须校验 monitor 归属。
3. 发布成功后，记录响应中的 `ingest_id`；该报告归属当前 Key 用户。

### 删除前

1. 仅删除列表接口返回且用户明确确认的 ID。
2. bulk-delete：仅提交本用户确认的 `ingest_ids` 数组。
3. 不得尝试路径穿越或非 UUID 字符串（服务端 422）。

---

## Ownership Examples

### 示例 1 — 正确：本用户监测入库

```bash
# 用户 A 的 Key
export API_KEY="oc_live_aaa..."

# 列出自己的 monitors
curl -sS "$BASE_URL/api/v1/public/monitoring/monitors" -H "X-Api-Key: $API_KEY"
# → 返回含 monitor_id: m-111

# 入库
curl -sS -X POST "$BASE_URL/api/v1/openclaw/monitoring/m-111/observations/ingest" \
  -H "X-Api-Key: $API_KEY" -d '{"price":100,"currency":"CNY"}'
# → 200
```

### 示例 2 — 拒绝：跨用户 monitor

```bash
# 用户 B 的 Key，却使用用户 A 的 monitor_id（m-111）
export API_KEY="oc_live_bbb..."
curl -sS -X POST "$BASE_URL/api/v1/openclaw/monitoring/m-111/observations/ingest" \
  -H "X-Api-Key: $API_KEY" -d '{"price":100,"currency":"CNY"}'
# → 404 Monitor not found
# Agent 应回复：该监测不属于当前账户，请在我的监测列表中创建或选择。
```

### 示例 3 — 正确：报告发布与查询

```bash
# POST 报告（无 owner_user_id 字段）
curl -sS -X POST "$BASE_URL/api/v1/openclaw/reports" \
  -H "X-Api-Key: $API_KEY" \
  -H "X-Request-Id: $(uuidgen)" \
  -d @report.json
# → 202 { "ingest_id": "r-222", ... }

# 本用户可查
curl -sS "$BASE_URL/api/v1/public/reports/r-222" -H "X-Api-Key: $API_KEY"
# → 200

# 他人 Key 查同一 ingest_id
# → 404
```

### 示例 4 — Workflow 与 monitor 配对

```json
{
  "job_name": "my-gold-6h",
  "monitor_id": "<本用户 bootstrap 返回的 uuid>",
  "cron_expr": "0 */6 * * *",
  "enabled": true
}
```

若 `monitor_id` 为他人所有 → 保存失败或后续 heartbeat/ingest 404。

### 示例 5 — API Key 仅本人管理

- Agent **拒绝**：「帮我列出用户 xyz 的 API Key」
- **引导**：门户 → 账户 → API Key 管理（仅 JWT 登录本人可操作）

---

## 相关文档

- [`multi-user-auth.md`](multi-user-auth.md)
- [`report-schema.md`](report-schema.md)
- [`multi-user-auth.md`](multi-user-auth.md) — 多用户鉴权与隔离
