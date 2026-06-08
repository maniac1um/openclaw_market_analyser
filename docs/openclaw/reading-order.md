# OpenClaw 运行时阅读顺序

面向 **OpenClaw Gateway** 加载 `skills/` 后的业务执行，非 Cursor 开发任务。

## 全局前置

1. `skills/_shared/agent-safety-baseline.md`
2. `skills/_shared/multi-user-auth.md`

## 按任务

| 任务 | 顺序 |
|------|------|
| 发布报告 | `report-schema.md` → `report-security.md` → `openclaw-report-security/SKILL.md` → `docs/human/api/openclaw-intake.md` |
| 调用 API | `multi-user-auth.md` → 相关 `SKILL.md` → `docs/human/api/openclaw-intake.md` |
| 门户对话路由 | `portal-chat-routing.md` → `docs/human/features/portal-chat.md` |
| 外采价格 | `openclaw-price-ingest-external/SKILL.md` |
| 新闻爬虫 | `openclaw-news-publisher-enhanced/SKILL.md` |
| 联合分析 | `openclaw-price-analysis-reporting/SKILL.md` |
| 对话入口 | `openclaw-conversational-assistant/SKILL.md` → `references/api-quickref.md` |

## 发布前

- `skills/_shared/ci-skill-regression.md`
- `skills/VERSIONS.md` / `skills/CHANGELOG.md`
