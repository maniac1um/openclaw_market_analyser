# 开发者指南

## 项目结构

```text
openclaw_news_publisher/
├── app/
│   ├── main.py              # App 工厂、SPA 挂载
│   ├── api/v1/
│   │   ├── openclaw.py      # Agent 入站 API
│   │   ├── public.py        # 公开 REST + 工作流 + auth
│   │   └── chat.py          # WebSocket 代理 + /chat/runs 轮询
│   ├── core/                # 配置、鉴权（JWT、per-user API Key、QueryContext）
│   ├── db/                  # 仓储 + public_queries + user_queries
│   ├── schemas/             # Pydantic 模型
│   ├── services/            # 业务逻辑（含 chat_run_store、openclaw_chat_bridge）
│   ├── workers/             # 后台任务
│   └── utils/               # 格式化、情绪分析
├── frontend/                # React SPA (Vite + Tailwind)
│   ├── android/             # Capacitor Android 工程（apk-test 分支）
│   └── src/features/chat/   # ChatProvider、ChatPage、pendingRuns
├── docs/                    # 人类文档
├── scripts/                 # 部署与运维脚本
├── tests/                   # pytest
├── skills/                  # OpenClaw Agent 技能（权威路径）
└── .cursor/skills -> skills/  # Cursor IDE 符号链接
```

## 核心模块

| 模块 | 何时修改 |
|------|----------|
| `schemas/report.py` | 报告入站字段变更 |
| `services/report_service.py` | 渲染 payload 结构 |
| `services/intake_service.py` | 幂等、入队逻辑 |
| `workers/job_runner.py` | 流水线步骤 |
| `api/v1/public.py` | 新增公开 API |
| `frontend/src/pages/` | UI 页面 |
| `frontend/src/features/chat/` | ChatProvider、ChatPage、pending 轮询 |
| `frontend/src/lib/api.ts` | 前端 API 类型 |

## 开发规范

### Python

- Python 3.11+，类型注解
- 配置通过 `app/core/config.py`（`OPENCLAW_` 前缀）
- 测试：`pytest -q`
- Commit message：中文或英文均可；仓库有 `commit-msg` hook 去除 Cursor 署名

### 前端

- React 18 + TypeScript + Tailwind CSS v4
- 数据获取：TanStack Query
- 路由：React Router v6
- 构建：`cd frontend && npm run build`
- Android 内测 APK（Capacitor）：见 [android-app.md](android-app.md)，在 `apk-test` 分支、`frontend/android/`

### 常见任务

**新增公开 API**

1. 在 `app/db/public_queries.py` 添加查询
2. 在 `app/api/v1/public.py` 注册路由
3. 在 `frontend/src/lib/api.ts` 添加类型与 fetch
4. 在对应 page 消费

**扩展报告 schema**

1. 修改 `app/schemas/report.py`（保持向后兼容，新字段 optional）
2. 更新 `ReportService.render_report_payload`
3. 更新 `frontend/src/lib/insights.ts` 或 Dashboard 组件
4. 更新 `skills/` 中 Agent 指引（如需要）

**本地双进程调试**

```bash
# 终端 1
uvicorn app.main:app --reload --port 8000

# 终端 2
cd frontend && npm run dev
```

浏览器访问 `http://localhost:5173`，首次使用请 **注册/登录**。OpenClaw Agent 须在门户 **账户 → API Key 管理** 生成 per-user Key（全局 `dev-openclaw-key` 在 Legacy 关闭后无效）。

**门户对话开发**：Gateway 需在宿主机单独运行；须配置 `portal-readonly` Agent 与 portal device（见 [security/GATEWAY_ISOLATION.md](security/GATEWAY_ISOLATION.md)）。前端 `ChatProvider` 在 `AppShell` 外层维持 WS。行为与 API 见 [portal-chat.md](portal-chat.md)。

## 多用户与鉴权

| 概念 | 说明 |
|------|------|
| 门户登录 | JWT Access + HttpOnly Refresh Cookie；`/api/v1/public/auth/*` |
| Agent 入站 | 请求头 `X-Api-Key: <per-user key>` |
| Public 读 | 方案 B：JWT 或 per-user Key；USER 仅见本用户数据 |
| 门户聊天 | USER → `portal-readonly` Agent；ADMIN → `main`；见 `GatewayPermissionChecker` |
| Legacy Key | `OPENCLAW_LEGACY_API_KEY_ENABLED`（默认 **false**） |
| Bootstrap ADMIN | `admin@localhost` / `Test_648.`（启动时自动创建；生产请尽快改密） |

详见 [multi-user/MULTI_USER_MIGRATION_PLAN.md](multi-user/MULTI_USER_MIGRATION_PLAN.md)。

## 测试

```bash
source .venv/bin/activate
pytest -q                                    # 全量
pytest tests/api/test_gateway_security.py -v # Gateway 权限隔离
pytest tests/api/test_multi_user_*.py -v     # 多用户集成
pytest tests/test_prompt_safety.py -v        # 对话违规词过滤
```

## API 文档

- Swagger UI：`http://localhost:8000/docs`
- 契约文档：[docs/api/openclaw-intake.md](api/openclaw-intake.md)
- 门户对话：[docs/portal-chat.md](portal-chat.md)

## Agent 技能

仓库根目录 **`skills/`** 供 OpenClaw Gateway 与 Cursor（经 `.cursor/skills` 符号链接）使用（**v2.0.1**，8 个 Skill + `_shared/`），**服务运行时不必加载此目录**。  
**生产挂载 Gateway**：见 [openclaw-skills-deploy.md](openclaw-skills-deploy.md)。架构说明：[`skills/SKILL_REFACTOR_PLAN.md`](../skills/SKILL_REFACTOR_PLAN.md)。

| Skill | 用途 |
|-------|------|
| `openclaw-conversational-assistant` | 对话入口、意图路由、调度流水线 |
| `openclaw-user-workspace` | 我的监测/报告/工作流/账户 |
| `openclaw-report-security` | 报告发布前安全门 |
| `openclaw-audit-events` | 操作审计（API 预埋） |
| `openclaw-news-publisher-enhanced` | 新闻抓取 + 报告入站 |
| `openclaw-price-ingest-external` | 外采价格入库 |
| `openclaw-price-analysis-reporting` | 价格+新闻联合分析 |
| `openclaw-public-news-library` | 新闻库管理 |
