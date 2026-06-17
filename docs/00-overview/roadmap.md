# 演进路线

> 非承诺排期；技术债详情见 [known-issues.md](../05-dev/known-issues.md)。

## 做什么

跟踪平台 backlog 优先级，帮助开发者判断「该不该现在做」。

## 关键组件

| 优先级 | 项 | 状态 |
|--------|-----|------|
| **P0** | OpenClaw API IDOR 修复（monitoring/news） | 进行中 KI-003 |
| **P0** | Gateway 双 Agent 生产配置 | 见 gateway-isolation |
| **P1** | Chat run PostgreSQL 持久化 | 待做 KI-004 |
| **P1** | Alembic 迁移 | 待做 KI-005 |
| **P2** | Service→API 逆依赖修复 | KI-001 |
| **P3** | Skill 物理 `production/` 目录 | 待定 |

## 数据流（决策 → 实施）

```
known-issues → roadmap 优先级 → 代码 PR → ADR/decisions 记录
```

## 示例

| 我要改 chat 持久化 | 先读 |
|--------------------|------|
| 现状 | [system-design.md](../02-backend/system-design.md) §门户对话 |
| 问题 | KI-004 `chat_run_store` 纯内存 |
| 安全约束 | [gateway-isolation.md](../02-backend/gateway-isolation.md) |

**已完成**：多用户 SaaS · Skill 重构 · Token 计费 · docs 分层（2026-06）
