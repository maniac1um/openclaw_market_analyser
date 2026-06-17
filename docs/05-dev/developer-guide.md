# 开发者指南

> 改代码前读本文 + [architecture.md](../00-overview/architecture.md)。

## 做什么

约定仓库结构、修改入口、开发流程与测试命令。

## 关键组件

| 改什么 | 看哪里 |
|--------|--------|
| 报告 schema | `schemas/report.py` → `services/report_service.py` |
| 入站幂等 | `services/intake_service.py` |
| 公开 API | `db/public_queries.py` → `api/v1/public.py` → `frontend/lib/api.ts` |
| Agent API | `api/v1/openclaw.py` |
| 计费 | `services/token_service.py` |
| 对话 | `api/v1/chat.py` + `features/chat/` |
| UI 页面 | `frontend/src/pages/` |
| 布局/DS | `components/layout/` + `components/ui/ds/` |

| 规范 | 要点 |
|------|------|
| Python | 3.11+，类型注解，`OPENCLAW_` 配置前缀 |
| 前端 | React 19 + TS + Tailwind v4 |
| 测试 | `pytest -q` |
| 分层 | API → Service → DB（见 system-design） |

## 数据流（常见任务）

### 新增公开 API

```
public_queries.py 写 SQL → public.py 注册路由 → api.ts 加类型 → Page 消费
```

### 扩展报告字段

```
schemas/report.py (optional 字段) → report_service 渲染 → 前端 Dashboard → 同步 api.md
```

### 本地双进程

```
uvicorn :8000 ←── Vite :5173 代理 /api
```

## 示例

```bash
# 本地开发
uvicorn app.main:app --reload --port 8000          # 终端 1
cd frontend && npm run dev                          # 终端 2

# 测试
pytest -q
pytest tests/api/test_multi_user_*.py -v

# 清理缓存
bash scripts/local/cleanup.sh --apply
```

| 鉴权 | JWT（门户）+ per-user Key（Agent）；Legacy Key 默认关 |
| Bootstrap | `admin@localhost` / `Test_648.` |

| API | [../02-backend/api.md](../02-backend/api.md) |
| Cursor 规则 | [../_agent/documentation-rules.md](../_agent/documentation-rules.md) |
| Skill（Gateway） | `skills/` — 非 Cursor 操作手册 |
