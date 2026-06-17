# 首次部署

> 面向零基础运维：1 小时内跑通生产可用实例。细节见 [production.md](production.md)。

## 做什么

从零克隆代码到浏览器可登录、Agent 可调用 API 的完整部署路径。

## 关键组件

| 方式 | 脚本 | 含 PostgreSQL |
|------|------|---------------|
| **Docker（推荐）** | `scripts/deploy/one-click-docker.sh` | ✅ |
| 裸机 | `deploy.sh` | ❌ 需自备 |

| 最低要求 | 值 |
|----------|-----|
| OS | Ubuntu 22.04+ |
| 内存 | 2 GB+ |
| PostgreSQL | 14+，三库 |

| 必配环境变量 | 说明 |
|--------------|------|
| `OPENCLAW_DATABASE_URL` ×3 | 三库 DSN |
| `OPENCLAW_JWT_SECRET` | 生产 ≥32 字符 |
| `OPENCLAW_PRODUCTION=true` | 生产模式 |

## 数据流

```
git clone → cp .env.example .env → 配三库 DSN
    → Docker 一键 / 裸机 pip+npm build
        → uvicorn :8000 → 浏览器 /login
            → admin@localhost → /account 生成 API Key
                → Agent 用 Key 调 /openclaw/*
```

## 示例

### Docker 一键（推荐）

```bash
git clone <repo> /opt/openclaw_news_publisher && cd $_
bash scripts/deploy/one-click-docker.sh
# → http://127.0.0.1:8000/login
```

### 裸机最小 `.env`

```env
OPENCLAW_DATABASE_URL=postgresql://openclaw_app:SECRET@127.0.0.1:5432/openclaw_app
OPENCLAW_MONITORING_DATABASE_URL=postgresql://openclaw_monitor:SECRET@127.0.0.1:5432/openclaw_monitor
OPENCLAW_NEWS_DATABASE_URL=postgresql://openclaw_news:SECRET@127.0.0.1:5432/openclaw_news
OPENCLAW_JWT_SECRET=至少32字符随机串
OPENCLAW_PRODUCTION=true
```

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cd frontend && npm ci && npm run build && cd ..
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

验证：`curl http://127.0.0.1:8000/healthz/db`

| 本地开发 | [local-dev.md](local-dev.md) |
| 生产 TLS/Nginx | [production.md](production.md) |
| Gateway | [openclaw-gateway.md](openclaw-gateway.md) |
