# API ↔ Skill 对照

> 冲突时：OpenClaw 执行业务以 `skills/` 为准；改 HTTP 契约以 `api.md` + 代码为准。

## 做什么

工程文档与 `_shared` 策略的一行对照，避免两边各说各话。

## 关键组件

| 主题 | 工程文档 | OpenClaw 运行时 |
|------|----------|-----------------|
| HTTP API | [api.md](../02-backend/api.md) | 各 SKILL + api-quickref |
| 报告 JSON | Pydantic / 代码 | `_shared/report-schema.md` |
| 鉴权 | api.md | `_shared/multi-user-auth.md` |
| 内容安全 | 服务端校验 | report-security + report-security/SKILL |
| Gateway | [gateway-isolation.md](../02-backend/gateway-isolation.md) | portal-chat-routing |
| Token 配额 | [billing.md](../04-product/billing.md) | quota-policy |

## 数据流

```
改 API → 更新 api.md + schemas → 检查 skills/_shared 是否需同步
改 Skill 策略 → _shared/*.md → crosswalk 确认工程侧一致
```

## 示例

| 我要确认入站字段 | 读 |
|------------------|-----|
| 后端权威 | `app/schemas/report.py` |
| Agent 侧 | `skills/_shared/report-schema.md` |
| HTTP 细节 | `docs/02-backend/api.md` POST /openclaw/reports |
