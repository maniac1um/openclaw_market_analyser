# OpenClaw Skills 版本表

| Skill | skill_version | 说明 |
|-------|---------------|------|
| **包整体** | **2.0.1** | 见 [CHANGELOG.md](CHANGELOG.md)；权威路径 `skills/` |
| `openclaw-conversational-assistant` | 2.0.0 | 默认入口 + §10/§11 |
| `openclaw-user-workspace` | 2.0.0 | 工作区只读聚合 |
| `openclaw-report-security` | 2.0.0 | 发布安全门 |
| `openclaw-audit-events` | 2.0.0 | 审计预埋 |
| `openclaw-news-publisher-enhanced` | 2.0.0 | 爬虫 + 报告；§8.6 收敛 |
| `openclaw-price-ingest-external` | 2.0.0 | 外采 ingest |
| `openclaw-price-analysis-reporting` | 2.0.0 | 联合分析 |
| `openclaw-public-news-library` | 2.0.0 | 新闻库 |

**_shared 文档**：与包版本 **2.0.1** 同步，无独立 semver；重大变更记入 CHANGELOG。

**兼容性**：要求 OpenClaw News Publisher 多用户 SaaS（per-user API Key、`QueryContext` 隔离）。Legacy 全局 Key 仅过渡。

**CI**：发布前执行 [`_shared/ci-skill-regression.md`](_shared/ci-skill-regression.md)。
