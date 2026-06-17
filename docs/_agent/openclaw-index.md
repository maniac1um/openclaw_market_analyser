# OpenClaw 运行时索引

> Gateway 加载 `skills/` 后的 Agent 文档入口；Cursor 请读 [documentation-rules.md](documentation-rules.md)。

## 做什么

指向 Skill 正文与工程文档的对照关系，供 OpenClaw cron/外采/对话编排使用。

## 关键组件

```
skills/
├── */SKILL.md      # 业务指令
└── _shared/        # 共用策略
```

| 链接 | 用途 |
|------|------|
| [skills/README.md](../../skills/README.md) | Skill 包入口 |
| [skill-map.md](skill-map.md) | 职责矩阵 |
| [reading-order.md](reading-order.md) | 按任务阅读顺序 |
| [crosswalk.md](crosswalk.md) | API ↔ Skill 对照 |

## 数据流

```
Gateway extraDirs → 读 SKILL.md → Agent 执行 → X-Api-Key → News Publisher API
```

## 示例

全局前置（任何任务）：

1. `skills/_shared/agent-safety-baseline.md`
2. `skills/_shared/multi-user-auth.md`

发报告：

```
report-schema → report-security → openclaw-report-security/SKILL.md → docs/02-backend/api.md
```

| Gateway 挂载 | [../01-getting-started/openclaw-gateway.md](../01-getting-started/openclaw-gateway.md) |
