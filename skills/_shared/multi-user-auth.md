# 多用户鉴权约定（OpenClaw Skills 共用）

**适用版本**：OpenClaw News Publisher 多用户 SaaS（2026-06 起）

## 凭证模型

| 凭证 | 获取方式 | 用途 |
|------|----------|------|
| **Per-user API Key** | 门户登录 → **账户 → API Key 管理** → 生成 | `POST /api/v1/openclaw/*`、方案 B 的 `GET /api/v1/public/*` |
| **JWT Access Token** | 门户登录后由 SPA 持有（内存） | 门户写操作、`POST /api/v1/public/workflow/*` |
| **Legacy 全局 Key** | 部署环境变量 `OPENCLAW_OPENCLAW_API_KEY` | **过渡期**映射 ADMIN；`OPENCLAW_LEGACY_API_KEY_ENABLED=false` 后失效 |

## 请求头

```bash
# OpenClaw Agent / cron / Cursor Skill（推荐）
-H "X-Api-Key: ${USER_API_KEY}"

# 门户 SPA 或带 Bearer 的客户端
-H "Authorization: Bearer ${ACCESS_TOKEN}"
```

**Public 读接口（方案 B）**：须带 per-user Key 或 JWT，否则 **401**。数据按 `user_id` 过滤。

## 数据隔离

- 每个用户只能读写 **本 Key 所属用户** 的 `monitor_id`、`ingest_id`、新闻库条目。
- 访问他人资源 ID → **404**（非 403）。
- `monitor_id` 必须与生成/使用它的 **同一 API Key** 配对；cron 迁移时须同步更新 Key。

## 禁止假设

- ❌ 不再假设单一全局 `OPENCLAW_OPENCLAW_API_KEY` 代表所有用户
- ❌ 不再假设 `GET /public/*` 无鉴权可读全库
- ❌ 不得将用户 API Key 写入 Skill 文档、Git、聊天回执

## 相关文档

- [`agent-safety-baseline.md`](agent-safety-baseline.md) — Agent 安全基线
- [`portal-chat-routing.md`](portal-chat-routing.md) — 门户 vs Cursor
- [`public-deploy-security.md`](public-deploy-security.md) — 公网部署与 429/422
- [`ownership-policy.md`](ownership-policy.md) — 资源归属
- [`quota-policy.md`](quota-policy.md) — 租户配额（预埋）
- [`workspace-api-roadmap.md`](workspace-api-roadmap.md) — 工作区 API 路线图
- [`ci-skill-regression.md`](ci-skill-regression.md) — CI 回归门禁
- [`docs/02-backend/api.md`](../../docs/02-backend/api.md)
