# 项目地图

> **一句话**：OpenClaw Agent 提交分析报告 → FastAPI 三库持久化 → React SPA 展示；可选 Gateway 门户对话。

## 做什么

5 分钟建立对仓库目录、外部依赖和文档入口的整体认知。

## 关键组件

| 路径 | 职责 |
|------|------|
| `app/` | FastAPI 后端（**不是** `backend/`） |
| `frontend/` | React SPA → 生产输出 `frontend/dist/` |
| `skills/` | OpenClaw Gateway 运行时（`extraDirs`） |
| `docs/` | 人类文档 + `_agent/` |
| `scripts/` | 部署、DB 迁移、本地脚本 |
| `tests/` | pytest |

| 外部依赖 | 必需？ |
|----------|--------|
| PostgreSQL ×3 | 生产必需 |
| OpenClaw Gateway `:18789` | 对话/诊断可选 |
| Git | 可选发布 |

## 数据流（核心业务）

```
OpenClaw Skill ──POST /openclaw/reports──► FastAPI ──► PostgreSQL
                                              │
浏览器 SPA ◄──GET /public/reports─────────────┘
```

## 示例

```bash
# 10 分钟 Docker 体验
git clone <repo> && cd openclaw_news_publisher
bash scripts/deploy/one-click-docker.sh
# → http://127.0.0.1:8000/login
# admin@localhost / Test_648. → /account 生成 API Key
```

| 下一步 | 文档 |
|--------|------|
| 架构细节 | [architecture.md](architecture.md) |
| 本地开发 | [../01-getting-started/local-dev.md](../01-getting-started/local-dev.md) |
| API | [../02-backend/api.md](../02-backend/api.md) |
