# Skill 职责矩阵

> Gateway 权威路径 `skills/` · 阅读顺序 [reading-order.md](reading-order.md)。

## 做什么

一张表看清 8 个生产 Skill 的分工与委派关系。

## 关键组件

| Skill | 一句话 | 委派 |
|-------|--------|------|
| conversational-assistant | 对话入口 + 意图路由 | → 各专项 |
| user-workspace | 「我的 xxx」只读聚合 | ← conversational |
| report-security | POST reports 前五项安全门 | ← news-publisher, price-analysis |
| news-publisher-enhanced | 新闻爬虫 + 报告入站 | → report-security |
| price-ingest-external | 外采价格 ingest | — |
| price-analysis-reporting | 价格+新闻联合分析 | → report-security |
| public-news-library | 新闻库 CRUD | — |
| audit-events | 审计追溯（API 预埋） | → user-workspace |

| `_shared` 必读 | 场景 |
|----------------|------|
| agent-safety-baseline | 全局 |
| multi-user-auth | 任何 API 调用 |
| report-schema + report-security | 发报告 |

## 数据流（发布路径）

```
Agent 持 JSON → report-security 五项校验 → POST /openclaw/reports
news-trigger publish:true → 服务端组装 → 同上
workflow/analysis/run → 同 news-trigger 逻辑
```

## 示例

| 用户说… | 委派 Skill | API |
|---------|------------|-----|
| 发报告 | report-security → news-publisher | POST /openclaw/reports |
| 查我的报告 | user-workspace | GET /public/reports |
| 外采价格 | price-ingest-external | POST .../observations/ingest |
| 联合分析 | price-analysis-reporting | POST .../news-trigger |

版本 **2.0.1** · `skills/VERSIONS.md`
