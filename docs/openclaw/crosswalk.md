# docs/human ↔ skills/_shared 权威对照

| 主题 | 工程契约（人类/Cursor） | OpenClaw 运行时 |
|------|-------------------------|-----------------|
| HTTP 入站 API | [openclaw-intake.md](../human/api/openclaw-intake.md) | 各 `SKILL.md` + `api-quickref.md` |
| 报告 JSON | 以 Pydantic/代码为准 | `skills/_shared/report-schema.md` |
| 鉴权与隔离 | `docs/human/api/openclaw-intake.md` | `skills/_shared/multi-user-auth.md` |
| 报告内容安全 | 服务端校验 | `report-security.md` + `openclaw-report-security` |
| Gateway 运维 | [gateway-isolation.md](../human/security/gateway-isolation.md) | `portal-chat-routing.md`（路由语义） |
| 多用户迁移（历史） | [migration-plan 归档](../archive/multi-user/migration-plan-2026-06-05.md) | 勿作待办；以 `multi-user-auth.md` 为准 |

**冲突解决**：OpenClaw 执行业务以 `skills/` 为准；改后端契约以 `docs/human/api/` + 代码为准。
