# OpenClaw 阅读顺序

> Gateway 运行时任务导向；非 Cursor 开发任务。

## 做什么

按任务类型给出 Skill + 工程文档的最短阅读链。

## 关键组件

| 任务 | 顺序 |
|------|------|
| 全局前置 | agent-safety-baseline → multi-user-auth |
| 发报告 | report-schema → report-security → report-security/SKILL → api.md |
| 调 API | multi-user-auth → 相关 SKILL → api.md |
| 门户对话 | portal-chat-routing → portal-chat.md |
| 外采价格 | price-ingest-external/SKILL |
| 新闻爬虫 | news-publisher-enhanced/SKILL |
| 联合分析 | price-analysis-reporting/SKILL |

## 数据流

```
任务触发 → 读 _shared 策略 → 读专项 SKILL.md → 调 HTTP API → 轮询/确认
```

## 示例

**发布报告**（路径 A–C）：

```
1. skills/_shared/report-schema.md
2. skills/openclaw-report-security/SKILL.md（五项校验）
3. POST /openclaw/reports + X-Request-Id
4. GET /openclaw/reports/{id} 直到 published
```

发布前：`ci-skill-regression.md` + `VERSIONS.md`
