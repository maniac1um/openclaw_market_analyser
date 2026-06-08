# OpenClaw 运行时文档索引

> **受众**：OpenClaw Gateway 运行时 Agent（cron、外采、门户对话编排等）。  
> **不是** Cursor IDE 开发辅助文档 — Cursor 请读 [AGENT_DOCUMENTATION_RULES.md](../AGENT_DOCUMENTATION_RULES.md)。

## 权威 Skill 根目录

```
skills/          # Gateway extraDirs 指向此处
├── */SKILL.md   # 业务执行指令
└── _shared/     # 共用策略
```

入口：[skills/README.md](../../skills/README.md)

## 阅读顺序

详见 [reading-order.md](reading-order.md)。

## 与工程文档对照

详见 [crosswalk.md](crosswalk.md)（`docs/human/api` ↔ `skills/_shared`）。

## 运维挂载

Gateway 部署：[../human/deployment/openclaw-skills-gateway.md](../human/deployment/openclaw-skills-gateway.md)
