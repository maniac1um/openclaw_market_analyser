# OpenClaw News Publisher — Agent Skills

**版本**：2.0.1 · 见 [VERSIONS.md](VERSIONS.md)、[CHANGELOG.md](CHANGELOG.md)

本目录为 **OpenClaw Gateway 运行时权威路径**，包含外采 Agent、cron、门户对话编排等使用的 Skill 与 `_shared` 策略文档。

| 用途 | 路径 |
|------|------|
| Gateway `extraDirs` | `/path/to/repo/skills` |
| 文档索引 | [docs/_agent/openclaw-index.md](../docs/_agent/openclaw-index.md) |
| Skill 职责地图 | [docs/_agent/skill-map.md](../docs/_agent/skill-map.md) |
| 系统架构 | [docs/00-overview/architecture.md](../docs/00-overview/architecture.md) |
| 生产部署 | [docs/01-getting-started/openclaw-gateway.md](../docs/01-getting-started/openclaw-gateway.md) |

**说明**：`skills/` 面向 **OpenClaw 运行时**，不是 Cursor IDE 开发辅助指令。工程师在 Cursor 中开发本仓库请读 [docs/_agent/documentation-rules.md](../docs/_agent/documentation-rules.md)。

---

## 分区（软分区）

Gateway 仍指向 `skills/` 根目录；下表为文档治理分区，**暂不移动物理目录**（见 ADR-007）。

| 分区 | 路径 | 说明 |
|------|------|------|
| **production** | `openclaw-*/` | 8 个生产 Skill |
| **shared** | `_shared/` | 共用策略（非 SKILL.md） |
| **experimental** | — | 暂无 |
| **deprecated** | — | 暂无 |

## 生产 Skill 一览

| Skill | 职责 |
|-------|------|
| [openclaw-conversational-assistant](openclaw-conversational-assistant/SKILL.md) | 对话入口、意图路由 |
| [openclaw-user-workspace](openclaw-user-workspace/SKILL.md) | 用户工作区只读聚合 |
| [openclaw-report-security](openclaw-report-security/SKILL.md) | 报告发布安全门 |
| [openclaw-audit-events](openclaw-audit-events/SKILL.md) | 审计事件（API 预埋） |
| [openclaw-news-publisher-enhanced](openclaw-news-publisher-enhanced/SKILL.md) | 新闻爬虫 + 报告 |
| [openclaw-price-ingest-external](openclaw-price-ingest-external/SKILL.md) | 外采价格 ingest |
| [openclaw-price-analysis-reporting](openclaw-price-analysis-reporting/SKILL.md) | 联合分析 |
| [openclaw-public-news-library](openclaw-public-news-library/SKILL.md) | 新闻库 |

`_shared/` 策略见 [docs/_agent/crosswalk.md](../docs/_agent/crosswalk.md)。
