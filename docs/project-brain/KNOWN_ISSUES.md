# 已知问题与技术债

| ID | 问题 | 严重度 | 跟踪 |
|----|------|--------|------|
| KI-001 | `news_analysis_service.py` 从 `api/v1/openclaw` 导入 `intake_service`（Service→API 逆依赖） | 中 | [ROADMAP P2](ROADMAP.md) |
| KI-002 | `public_queries.py` 调用 `MonitoringService` / Gateway probe | 低 | 分层边界模糊 |
| KI-003 | OpenClaw monitoring/news API IDOR 风险 | 高 | [security audit-2026-06-08](../reports/security/audit-2026-06-08.md) |
| KI-004 | `chat_run_store` 纯内存，重启丢失对话 run | 中 | [ROADMAP P1](ROADMAP.md) |
| KI-005 | 无 Alembic；迁移靠 SQL 片段 + startup | 中 | `scripts/migrations/` |
| KI-006 | `openclaw-audit-events` Skill API 预埋未全实现 | 低 | `skills/_shared/workspace-api-roadmap.md` |
| KI-007 | 裸机 PostgreSQL 初始化步骤分散 | 中 | [getting-started](../human/deployment/getting-started.md) |
| KI-008 | pytest 数量需在索引中同步 | 低 | 当前 **115** 项 |

## 已关闭

| ID | 问题 | 关闭日期 |
|----|------|----------|
| KI-DOC-001 | 根目录 Agent 报告/plan 未归档 | 2026-06-08 |
| KI-DOC-002 | 缺少 Project Brain onboarding 入口 | 2026-06-08 |
| KI-DOC-003 | `DEPLOYMENT_GUIDE` 与 human/deployment 分叉 | 2026-06-08（已合并至 getting-started，根 stub 已删） |

## 报告快照勿当待办

以下文档记录**历史时间点**结论，numbers 可能过时：

- `docs/reports/security/verification-report-v5-2026-06-05.md`（pytest 45/45）
- `docs/archive/product/ux-improvement-plan-2026-06-08.md`
- `docs/archive/frontend/visualization-plan-2026-06-08.md`（多数 UI 已实施）
