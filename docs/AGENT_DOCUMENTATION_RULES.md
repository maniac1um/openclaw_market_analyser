# Cursor Agent 文档读取规则

**版本**：1.2  
**日期**：2026-06-08（文档迁移已执行）  
**适用范围**：在本仓库工作的 **Cursor Agent**（IDE 内辅助开发的 AI）  
**不适用于**：OpenClaw Gateway 运行时 — 见 [openclaw/README.md](openclaw/README.md)  
**关联**：[PROJECT_DOCUMENT_INDEX.md](PROJECT_DOCUMENT_INDEX.md)（同目录）

---

## 0. 关键区分（必读）

| 受众 | 权威文档 | 用途 |
|------|----------|------|
| **OpenClaw Agent** | `skills/**` | Gateway 运行时业务执行 |
| **Cursor Agent** | `docs/human/**`、本文件、治理元文档 | 开发本仓库（代码/文档/治理） |

**`skills/` 不是 Cursor 操作手册。** 仅当编辑 Skill 源码或理解 OpenClaw 集成时参考 `skills/`。

---

## 1. Cursor 首选文档（`docs/human/`）

| 类别 | 路径 |
|------|------|
| 开发 | `docs/human/development/developer-guide.md` |
| 架构 | `docs/human/architecture/overview.md` |
| 本地部署 | `docs/human/deployment/local.md` |
| 生产部署 | `docs/human/deployment/production.md` |
| Gateway 挂载 | `docs/human/deployment/openclaw-skills-gateway.md` |
| API 契约 | `docs/human/api/openclaw-intake.md` |
| Gateway 隔离 | `docs/human/security/gateway-isolation.md` |
| 门户对话 | `docs/human/features/portal-chat.md` |
| 测试 | `docs/human/testing/multi-user-test-plan.md` |
| 治理 | `docs/PROJECT_DOCUMENT_INDEX.md`、`docs/AGENT_DOCUMENTATION_RULES.md`、`docs/archive/governance/*` |

**旧路径重定向**（仍有效）：`docs/api/openclaw-intake.md`、`docs/security/GATEWAY_ISOLATION.md`

---

## 2. `skills/` 参考读取（非操作依据）

| 场景 | 可读 |
|------|------|
| 编辑 Skill | `skills/**/SKILL.md`、`skills/_shared/**` |
| 理解 OpenClaw 集成 | `skills/README.md`、`openclaw/crosswalk.md` |

---

## 3. 历史 / 快照（禁止当待办）

| 文档 | 说明 |
|------|------|
| `docs/archive/multi-user/migration-plan-2026-06-05.md` | 已实施 |
| `docs/archive/skills/skill-refactor-plan-2026-06-06.md` | 已完成 |
| `docs/reports/security/*` | 审计快照 |
| `docs/archive/skills/skill-refactor-plan-2026-06-06.md` | Skill 重构已完成 |

---

## 4. Cursor 任务阅读顺序

| 任务 | 顺序 |
|------|------|
| 改后端 | `developer-guide.md` → `overview.md` → `openclaw-intake.md`（若涉 API） |
| 改前端 | `developer-guide.md` → `portal-chat.md`（若涉聊天） |
| 部署文档 | `production.md` 或 `local.md` → `gateway-isolation.md` |
| 编辑 Skill | 目标 `SKILL.md` → `_shared/` → `openclaw-intake.md` |
| 文档治理 | `PROJECT_DOCUMENT_INDEX.md` → `archive/governance/documentation-audit-2026-06-08.md` |

---

## 5. 权威优先级（Cursor 开发）

1. 代码（`app/`、`frontend/src/`）
2. `docs/human/api/openclaw-intake.md`
3. `docs/human/architecture/overview.md`、`developer-guide.md`
4. `docs/human/security/gateway-isolation.md`
5. `skills/*`（仅改 Skill 时）
6. `docs/archive/**`、`docs/reports/**`（历史）

---

## 6. 禁止

- 将 `skills/` 流程当作 Cursor 应执行的步骤
- 读取 `.env`、备份内容、device 状态文件
- 将 `frontend/README.md` 当作项目前端指南（见 `docs/archive/frontend/vite-template-readme.md`）

---

## 7. Cursor 自检

- [ ] 改代码是否读了 `docs/human/development/developer-guide.md`？
- [ ] 是否误将 `skills/` 当作 Cursor 操作手册？
- [ ] 是否误将 archive/reports 当作待办？

---

*OpenClaw 运行时阅读顺序：[openclaw/reading-order.md](openclaw/reading-order.md)*
