# 演进路线

> 非承诺排期；优先级供 backlog 参考。详细技术债见 [KNOWN_ISSUES.md](KNOWN_ISSUES.md)。

## P0 — 安全 / 合规

| 项 | 说明 | 跟踪 |
|----|------|------|
| OpenClaw API IDOR 修复 | monitoring/news 路径缺少归属校验 | [audit-2026-06-08.md](../reports/security/audit-2026-06-08.md) |
| Gateway 双 Agent 生产配置 | USER 不可获得 ADMIN Gateway 能力 | [gateway-isolation.md](../human/security/gateway-isolation.md) |

## P1 — 平台能力

| 项 | 说明 | 来源 |
|----|------|------|
| Chat run PostgreSQL 持久化 | 替代 `chat_run_store` 内存 + localStorage | architecture/overview §演进 |
| Alembic 数据库迁移 | 替代分散 SQL + startup migration | KI-005 |
| 裸机 DB bootstrap 脚本 | 统一三库 + reports DDL | getting-started §裸机 |
| audit-events API 全量实现 | Skill 预埋与后端对齐 | workspace-api-roadmap |

## P2 — 代码健康

| 项 | 说明 |
|----|------|
| Service → API 逆依赖修复 | `news_analysis_service` → `intake_service` |
| `public_queries` 与 Service 边界 | 查询层不应编排 Service |

## P3 — 文档 / Skill 治理

| 项 | 说明 | 状态 |
|----|------|------|
| Project Brain 建立 | onboarding SSOT | ✅ 2026-06-08 |
| 根目录 Agent 报告归档 | reports / archive | ✅ 2026-06-08 |
| Skill 软分区 | README + SKILL_MAP 标注 production | ✅ 2026-06-08 |
| Skill 物理 `production/` 目录 | 需 Gateway 配置变更 | 待定 |
| 兼容 stub 清理 | `docs/api/`、`docs/security/` | 下一发布周期 |

## 已完成的里程碑

- 多用户 SaaS 迁移（2026-06-05）
- Skill 架构重构阶段 0–5（2026-06-06）
- 文档 human / openclaw / reports 三分（2026-06-08）
- 项目治理 ABCDE 执行（2026-06-08）
