# 项目地图

## 一句话

OpenClaw News Publisher 是多用户 SaaS 门户：OpenClaw Agent 通过 API 提交结构化新闻/分析报告 → 三库持久化 → React SPA 展示；可选 WebSocket 代理 OpenClaw Gateway 做门户对话。

## 仓库目录（5 分钟）

| 路径 | 职责 | 备注 |
|------|------|------|
| `app/` | FastAPI 后端 | **不是** `backend/` |
| `frontend/` | React 18 + Vite SPA | 生产构建输出 `frontend/dist/` |
| `skills/` | OpenClaw Gateway 运行时 Skill | `extraDirs` 权威路径 |
| `docs/` | 人类 / OpenClaw / 报告 / 归档文档 | 本目录 `project-brain/` |
| `scripts/` | 部署、本地启停、DB 初始化 SQL | 见 `deploy/`、`local/`、`docker/` |
| `tests/` | pytest（**115** 项） | `pytest -q` |
| `deploy.sh` | 裸机一键部署编排 | Docker：`deploy.sh --docker` |
| `scripts/local/` | 本地启停、DB 验证、**磁盘清理** | 见下表 |

**`scripts/local/` 常用脚本**

| 脚本 | 用途 |
|------|------|
| `start-server.sh` / `stop-server.sh` | 后台启停 uvicorn |
| `verify-openclaw-databases.sh` | 三库连通性 |
| `cleanup.sh` / `cleanup.ps1` | 安全清理缓存（默认 dry-run，`--apply` 执行） |

**不存在**的顶层目录：`backend/`、`deployment/`、`config/`、`tools/`（Skill 内嵌工具见 `skills/openclaw-news-publisher-enhanced/tools/`）。

## 三受众文档

| 受众 | 读什么 | 不要读什么 |
|------|--------|------------|
| 人类工程师 | `docs/human/`、`project-brain/` | 勿把审计快照当运维手册 |
| OpenClaw Gateway | `skills/**/SKILL.md`、`skills/_shared/` | 非 Cursor 开发手册 |
| Cursor Agent | `docs/AGENT_DOCUMENTATION_RULES.md`、`docs/human/` | 勿在 IDE 内模拟 Agent 发报告 |

## 外部依赖

| 组件 | 必需？ | 说明 |
|------|--------|------|
| PostgreSQL ×3 | **是**（生产） | reports / monitoring / news 可同机不同库 |
| OpenClaw Gateway | 否 | 门户对话、部分工作流诊断需要 `:18789` |
| Git | 否 | 可选 `publish_site.py` 发布 |

## 10 分钟 Docker 路径

```bash
git clone <repo> && cd openclaw_news_publisher
bash scripts/deploy/one-click-docker.sh
# 浏览器 → http://127.0.0.1:8000/login
# admin@localhost / Test_648. → /account 生成 API Key
```

## 链接速查

| 主题 | 文档 |
|------|------|
| 1 小时部署 | [getting-started.md](../human/deployment/getting-started.md) |
| 本地开发 | [local.md](../human/deployment/local.md) |
| 生产 / systemd | [production.md](../human/deployment/production.md) |
| API 契约 | [openclaw-intake.md](../human/api/openclaw-intake.md) |
| Gateway P0 隔离 | [gateway-isolation.md](../human/security/gateway-isolation.md) |
| Skill 索引 | [SKILL_MAP.md](SKILL_MAP.md) |
| 全文档地图 | [PROJECT_DOCUMENT_INDEX.md](../PROJECT_DOCUMENT_INDEX.md) |
