# OpenClaw News Publisher

多用户市场分析 SaaS：OpenClaw Agent 抓取新闻与价格，生成 AI 研判报告；FastAPI 入站渲染，React 门户展示。  
支持自动工作流编排、Token 计费、多租户隔离；可选 WebSocket 对接 OpenClaw Gateway 做门户对话。

## 核心功能

| 功能 | 说明 |
|------|------|
| **AI 分析** | 新闻 + 价格联合分析；门户对话经 Gateway 流式回复 |
| **自动工作流** | 监测 bootstrap、定时外采、联合分析、一键诊断与可运行性验证 |
| **Token 计费** | 对话 / 工作流 / 报告按 Token 扣费；订阅月发、模拟充值 |
| **报告系统** | Agent 入站 JSON → 幂等渲染 → 门户 Dashboard 展示与专题卡片 |

## 架构

```
┌─────────────┐     JWT      ┌──────────────────┐     SQL     ┌──────────────┐
│  React SPA  │─────────────►│  FastAPI :8000   │────────────►│ PostgreSQL×3 │
│  (门户)     │◄─────────────│  app/            │             │ reports      │
└─────────────┘              │  ├ public/      │             │ monitoring   │
       ▲                     │  ├ openclaw/    │             │ news         │
       │ WSS (可选)           │  └ chat/ws ────┼──► Gateway  └──────────────┘
       │                     └────────▲─────────┘      :18789
┌──────┴──────┐                      │
│ OpenClaw    │──── X-Api-Key ───────┘
│ Agent/skills│
└─────────────┘
```

## 快速启动

### Install

```bash
git clone <repo> && cd openclaw_news_publisher
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # 编辑三库 DSN
cd frontend && npm install && cd ..
```

Docker 一键（含 PostgreSQL）：`bash scripts/deploy/one-click-docker.sh`

### Run

```bash
# 终端 1 — 后端
uvicorn app.main:app --reload --port 8000

# 终端 2 — 前端
cd frontend && npm run dev
# → http://localhost:5173
```

浏览器注册/登录 → **账户** 页生成 `X-Api-Key`（Agent 调用用）。

## 示例：生成一次分析

**路径 A — 门户工作流**（需先有监测任务）：

```bash
# 1. 登录拿 JWT，或 export KEY=账户页生成的 Api Key

# 2. 创建监测（网页「工作流」或 API）
curl -X POST http://localhost:8000/api/v1/public/workflow/monitor/bootstrap \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"keyword":"羽毛球","cadence":"daily"}'
# 记下返回的 monitor_id

# 3. 触发联合分析（扣 Token，可选发布报告）
curl -X POST http://localhost:8000/api/v1/public/workflow/analysis/run \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"monitor_id":"<uuid>","window_days":7,"publish":true}'
```

**路径 B — OpenClaw Agent**（cron / Skill）：

```bash
curl -X POST http://localhost:8000/api/v1/openclaw/analysis/news-trigger \
  -H "X-Api-Key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{"monitor_id":"<uuid>","window_days":7,"publish":true}'
```

`publish: true` 时系统自动组装报告并入队；门户 **专题分析** 页查看结果。  
完整 API：[docs/02-backend/api.md](docs/02-backend/api.md) · Swagger：`http://localhost:8000/docs`（开发需 `OPENCLAW_EXPOSE_OPENAPI=true`）

## 技术栈

Python 3.11 · FastAPI · React 19 · PostgreSQL ×3 · OpenClaw `skills/`

## 文档

| 读者 | 入口 |
|------|------|
| 5 分钟懂项目 | [docs/00-overview/project-map.md](docs/00-overview/project-map.md) |
| 部署 | [docs/01-getting-started/getting-started.md](docs/01-getting-started/getting-started.md) |
| 架构 | [docs/00-overview/architecture.md](docs/00-overview/architecture.md) |

## License

内部项目 — 按组织规范使用。
