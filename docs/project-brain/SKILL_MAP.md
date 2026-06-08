# Skill 职责地图

> Gateway 权威路径：`skills/`（`extraDirs`）。阅读顺序全文：[openclaw/reading-order.md](../openclaw/reading-order.md)。

## 分区（软分区 — Gateway 路径不变）

| 分区 | 目录 | 说明 |
|------|------|------|
| **production** | `openclaw-*/` | 8 个生产 Skill，默认加载 |
| **shared** | `_shared/` | 策略文档，非独立 Skill |
| **experimental** | — | 暂无；新 Skill 须标注版本与过期日 |
| **deprecated** | — | 暂无 |

## 生产 Skill 矩阵

| Skill | 一句话 | 委派 / 被委派 | 必读 `_shared` |
|-------|--------|---------------|----------------|
| [openclaw-conversational-assistant](../../skills/openclaw-conversational-assistant/SKILL.md) | 对话入口 + 意图路由 §10/§11 | → 各专项 Skill | agent-safety-baseline, multi-user-auth |
| [openclaw-user-workspace](../../skills/openclaw-user-workspace/SKILL.md) | 「我的 xxx」只读聚合 | ← conversational | ownership-policy, portal-chat-routing |
| [openclaw-report-security](../../skills/openclaw-report-security/SKILL.md) | POST reports 前五项安全门 | ← news-publisher, price-analysis | report-schema, report-security |
| [openclaw-news-publisher-enhanced](../../skills/openclaw-news-publisher-enhanced/SKILL.md) | 新闻爬虫 + 报告入站 | → report-security | public-deploy-security |
| [openclaw-price-ingest-external](../../skills/openclaw-price-ingest-external/SKILL.md) | 外采价格 observations/ingest | — | quota-policy |
| [openclaw-price-analysis-reporting](../../skills/openclaw-price-analysis-reporting/SKILL.md) | 价格+新闻联合分析 | → report-security | report-schema |
| [openclaw-public-news-library](../../skills/openclaw-public-news-library/SKILL.md) | 新闻库 CRUD | — | report-security (URL) |
| [openclaw-audit-events](../../skills/openclaw-audit-events/SKILL.md) | 审计追溯（API 预埋） | → user-workspace | workspace-api-roadmap |

## 发布路径（摘要）

| 路径 | 说明 | 安全门 |
|------|------|--------|
| A–C | Agent 持有 report JSON → `POST /openclaw/reports` | **openclaw-report-security** 强制 |
| D | `news-trigger` + `publish:true` | 服务端组装；校验 monitor 归属 |
| E | `workflow/analysis/run` | 同 D |

详见 `skills/_shared/public-deploy-security.md`。

## 阅读顺序（任务导向）

1. 全局：`agent-safety-baseline.md` → `multi-user-auth.md`
2. 发报告：`report-schema.md` → `report-security.md` → `openclaw-report-security/SKILL.md`
3. 外采价格：`openclaw-price-ingest-external/SKILL.md`
4. 门户对话：`portal-chat-routing.md` → [portal-chat.md](../human/features/portal-chat.md)

## 版本

包整体 **2.0.1** — 见 [skills/VERSIONS.md](../../skills/VERSIONS.md)、[CHANGELOG.md](../../skills/CHANGELOG.md)。

## 不合并说明

- **conversational-assistant** 与各专项：路由 vs 执行，保持委派。
- **price-ingest** vs **price-analysis**：cron 高频 ingest vs 低频分析报告。
- **user-workspace** vs **audit-events**：audit API 全量后独立演进。
