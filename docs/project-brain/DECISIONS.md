# 架构决策记录（ADR）

| ID | 决策 | 日期 | 状态 |
|----|------|------|------|
| ADR-001 | 后端代码目录命名为 `app/`，不使用 `backend/` | — | 已接受 |
| ADR-002 | PostgreSQL 三库分离（reports / monitoring / news） | — | 已接受 |
| ADR-003 | OpenClaw Skill 权威路径为仓库根 `skills/`，经 Gateway `extraDirs` 加载 | 2026-06 | 已接受 |
| ADR-004 | 文档三分：`docs/human/`（人类）、`docs/openclaw/`（运行时索引）、`docs/reports/` + `archive/` | 2026-06-08 | 已接受 |
| ADR-005 | Legacy 全局 API Key 默认关闭（`OPENCLAW_LEGACY_API_KEY_ENABLED=false`） | 2026-06 | 已接受 |
| ADR-006 | Project Brain（`docs/project-brain/`）为 onboarding 单一真相源 | 2026-06-08 | 已接受 |
| ADR-007 | Skill 软分区先行，物理 `skills/production/` 待 Gateway 回归后迁移 | 2026-06-08 | 已接受 |
| ADR-008 | 兼容 URL stub（`docs/api/`、`docs/security/`）保留一个发布周期 | 2026-06-08 | 已接受 |

## ADR-001 详情：app/ 非 backend/

**背景**：FastAPI 惯例与 Python 包名 `app` 一致。  
**后果**：文档与口头沟通需明确「后端 = app/」。

## ADR-006 详情：Project Brain

**背景**：根目录散落 Agent 报告/plan，新工程师 onboarding 超过 30 分钟。  
**决策**：`project-brain/` 提供精简地图；详细文档仍链到 `human/`。

## 如何新增 ADR

1. 在表末追加 `ADR-NNN` 行。  
2. 重大决策增加「背景 / 决策 / 后果」小节。  
3. 关联 [ROADMAP.md](ROADMAP.md) 或 [KNOWN_ISSUES.md](KNOWN_ISSUES.md) 若引入技术债。
