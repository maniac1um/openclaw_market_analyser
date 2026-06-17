# Cursor Agent 规则

> 在本仓库写代码的 Cursor Agent 专用；OpenClaw 运行时见 [openclaw-index.md](openclaw-index.md)。

## 做什么

规定 Cursor 读哪些文档、以什么优先级改代码，避免把 `skills/` 当 IDE 操作手册。

## 关键组件

| 受众 | 权威来源 |
|------|----------|
| Cursor | `docs/00-overview` … `05-dev`、本文件 |
| OpenClaw Gateway | `skills/**/SKILL.md` |

| 优先级 | 来源 |
|--------|------|
| 1 | 代码 `app/`、`frontend/src/` |
| 2 | `02-backend/api.md` |
| 3 | `architecture.md`、`developer-guide.md` |
| 4 | `gateway-isolation.md` |
| 5 | `skills/*`（仅改 Skill 时） |

## 数据流（按任务选文档）

```
改后端 → developer-guide → architecture → api.md
改前端 → developer-guide → portal-ui → (portal-chat)
改计费 → billing → system-design → api.md
改 Skill → SKILL.md → _shared → api.md
```

## 示例

| 任务 | 第一步打开 |
|------|------------|
| 新增 REST | `05-dev/developer-guide.md` |
| 改入站契约 | `02-backend/api.md` + `schemas/report.py` |
| 部署文档 | `01-getting-started/production.md` |

**禁止**：读 `.env` · 把 skills 流程当 Cursor 步骤 · 用 `frontend/README.md` 当前端 SSOT。

API 变更须同步 `02-backend/api.md`。
