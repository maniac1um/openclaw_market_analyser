# 本地开发

> 双进程：后端 `:8000` + Vite `:5173`。首次部署见 [getting-started.md](getting-started.md)。

## 做什么

在本机快速启动开发环境，支持热重载与前端 API 代理。

## 关键组件

| 进程 | 命令 | 端口 |
|------|------|------|
| 后端 | `uvicorn app.main:app --reload --port 8000` | 8000 |
| 前端 | `cd frontend && npm run dev` | 5173 |

| 脚本 | 用途 |
|------|------|
| `scripts/local/start-server.sh` | 后台启停 uvicorn |
| `scripts/local/verify-openclaw-databases.sh` | 三库连通 |
| `scripts/local/cleanup.sh` | 缓存清理（`--apply` 执行） |

| 配置 | 说明 |
|------|------|
| `.env` | 从 `.env.example` 复制，填三库 DSN |
| Bootstrap | 空库自动创建 `admin@localhost` / `Test_648.` |

## 数据流

```
浏览器 :5173 ──/api 代理──► uvicorn :8000 ──► PostgreSQL ×3
                                    │
OpenClaw Agent ──X-Api-Key──────────┘
```

## 示例

```bash
# 终端 1
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # 编辑三库 DSN
uvicorn app.main:app --reload --port 8000

# 终端 2
cd frontend && npm install && npm run dev

# 验证
bash scripts/local/verify-openclaw-databases.sh
curl http://127.0.0.1:8000/healthz
pytest -q
```

浏览器 → `http://localhost:5173/register` → 账户页生成 per-user API Key。

| 生产部署 | [production.md](production.md) |
| 开发规范 | [../05-dev/developer-guide.md](../05-dev/developer-guide.md) |
