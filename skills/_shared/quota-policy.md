# 配额策略（OpenClaw Skills 共用）

**适用版本**：SaaS Skill 架构 v2.0（2026-06 起）  
**状态**：**文档预埋** — 服务端 `quota_exceeded` 未全面实现前，Agent 按本策略 **自律** 并正确回执；与现有 **Rate limit（429）** 并存。

---

## 1. 配额层级

| 层级 | 机制 | 现状 |
|------|------|------|
| **L1 全站 Rate limit** | `OPENCLAW_RATE_LIMIT_*` | ✅ 已实现 → HTTP **429** |
| **L2 租户资源配额** | 每用户 monitors / reports / ingest 频率 | ⏳ 本文档定义；待后端 `402`/`429` + `quota_exceeded` |
| **L3 Agent 自律** | 测试请求 ≤3、写操作确认 | ✅ `agent-safety-baseline.md` |

---

## 2. 默认配额（建议值 · FREE 档）

运维可在未来按 `plan` 字段覆盖；Agent **默认按 FREE 执行**：

| 资源 | 周期 | 上限 | 触顶时 Agent 行为 |
|------|------|------|-------------------|
| **监测任务** `monitor` | 每用户累计 | **10** | 拒绝 bootstrap；建议归档旧任务 |
| **报告入站** `POST /openclaw/reports` | 每用户 / 日 | **20** | 拒绝发布；建议合并分析 |
| **价格 ingest** `observations/ingest` | 每 `monitor_id` / 小时 | **120** | 停止该 monitor 本小时入库；上报 heartbeat `status=error` |
| **新闻库写入** `POST /news/library` | 每用户 / 日 | **200** | 暂停写入；提示去重 |
| **外采工作流** `external-configs` | 每用户累计 | **15** `job_name` | 拒绝新建；建议合并 cron |
| **API Key** | 每用户累计 | **5** 活跃 | 引导门户撤销旧 Key |
| **bulk-delete** 单次 | 每请求 | **50** `ingest_ids` | 分批删除 |

**ingest 频率换算**：cron 不低于 `*/1 * * * *`（每分钟）除非用户书面确认运维放行。

---

## 3. 预检（Agent 自律 · 后端未强制时）

写操作前建议（可用 `openclaw-user-workspace` 列表接口估算）：

```text
[ ] GET /public/monitoring/monitors → count < 监测上限
[ ] GET /public/reports → 今日条数 < 报告日上限（按 generated_at 本地日）
[ ] 本小时 ingest 次数 < 120（若无法统计则依赖 cron 间隔 ≥5min）
[ ] external-configs 列表 < 15
```

触顶时 **不** 盲目 POST；使用 §6 回执模板。

---

## 4. 与未来服务端对齐

### 期望响应（预埋）

| HTTP | `detail` 示例 | Agent |
|------|---------------|-------|
| **402** 或 **429** | `quota_exceeded: monitors` | 停止写；§6 模板 |
| **429** | Rate limit（无 quota 字段） | `public-deploy-security.md` 429 模板 |

### 期望响应头（可选）

```http
X-Quota-Limit: 10
X-Quota-Remaining: 2
X-Quota-Reset: 2026-06-07T00:00:00Z
```

### 与 Rate limit 区别

| | Rate limit | Quota |
|--|------------|-------|
| 目的 | 防滥用、防 DDoS | 防单租户资源耗尽 |
| 窗口 | 短（分钟） | 长（日/累计） |
| Skill | `public-deploy-security` | 本文档 |

---

## 5. 各 Skill 配额触点

| Skill | 触点 |
|-------|------|
| `openclaw-price-ingest-external` | bootstrap、ingest 频率 |
| `openclaw-news-publisher-enhanced` | 日报告数、爬虫 `max_items` |
| `openclaw-price-analysis-reporting` | 日报告数、news-trigger publish |
| `openclaw-public-news-library` | 日新闻写入 |
| `openclaw-conversational-assistant` | 创建监测/工作流前预检 |
| `openclaw-user-workspace` | 列表返回 count 供预检 |

---

## 6. 回执模板

### 配额触顶（自律或 402/429 quota）

```markdown
已达到当前账户配额上限，已停止写入。
- 类型：{monitors | reports_daily | ingest_hourly | news_daily | workflows}
- 上限：{n}（FREE 档；升级或联系运维）
- 建议：{归档旧监测 / 降低 cron 频率 / 合并报告}

列表与用量可查：门户对应页面，或 Cursor 中 `openclaw-user-workspace`。
```

---

## 相关文档

- [`workspace-api-roadmap.md`](workspace-api-roadmap.md) — 工作区 API 与用量查询
- [`public-deploy-security.md`](public-deploy-security.md) — 429 Rate limit
- [`agent-safety-baseline.md`](agent-safety-baseline.md)
