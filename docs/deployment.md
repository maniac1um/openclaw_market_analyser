# 部署指南

> **生产 / 云服务器部署**（Docker、systemd、Nginx、TLS、防火墙）见 **[server-deployment.md](server-deployment.md)**。本文档侧重本地开发与快速验证。
>
> **Android 内测 APK**（Capacitor，本机构建）：见 **[android-app.md](android-app.md)**（`apk-test` 分支）。

## 本地开发（推荐）

### 1. 后端

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # 编辑三库 DSN
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

或使用脚本：

```bash
bash scripts/local/start-server.sh
```

### 2. 前端（开发模式）

```bash
cd frontend
npm install
npm run dev    # http://localhost:5173，代理 /api → :8000
```

### 3. 验证

```bash
bash scripts/local/verify-openclaw-databases.sh
curl http://127.0.0.1:8000/healthz
curl http://127.0.0.1:8000/healthz/db
```

浏览器访问 `http://localhost:5173`（开发）或 `http://localhost:8000`（生产构建后）。

### 4. 门户账户与 Agent Key

1. 打开 `/login`（bootstrap ADMIN：`admin@localhost` / `Test_648.`；生产环境请尽快改密）
2. 进入 **账户**（`/account`）生成 **per-user API Key**
3. 在 OpenClaw / cron 环境配置 `X-Api-Key`（**不再**使用全局 `dev-openclaw-key`，除非 `OPENCLAW_LEGACY_API_KEY_ENABLED=true`）

### 5. 门户对话与 Gateway 隔离

生产环境须配置双 Agent 与 portal device，否则 USER 可能获得 Gateway 管理员能力。完整步骤见 **[security/GATEWAY_ISOLATION.md](security/GATEWAY_ISOLATION.md)**。

## 生产构建（单体部署）

```bash
cd frontend && npm ci && npm run build
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

FastAPI 自动挂载 `frontend/dist`，访问 `/` 即为 SPA。

环境变量：

```env
OPENCLAW_SERVE_SPA=true
OPENCLAW_CORS_ORIGINS=   # 生产可留空
```

## Docker

### 一键：应用 + PostgreSQL（推荐）

```bash
bash scripts/deploy/one-click-docker.sh
```

脚本会：生成 Docker 用 `.env`、构建镜像、启动 `app` + `postgres`（三库自动初始化）、等待健康检查通过。

停止：`bash scripts/deploy/one-click-docker.sh --down`

### 手动 Compose

`docker-compose.yml` 包含：

- `app`：FastAPI + 预构建 SPA
- `postgres`（profile `full`）：三库初始化（`scripts/docker/init-databases.sql`）

```bash
cp scripts/deploy/env.docker.example .env   # 或自行配置 DSN
docker compose --profile full up -d --build
```

仅启动应用（使用外部数据库）：

```bash
docker compose up app -d
```

## 一键部署脚本

| 场景 | 脚本 |
|------|------|
| **Docker + PostgreSQL** | `bash scripts/deploy/one-click-docker.sh` |
| Linux 裸机（无 PostgreSQL） | `bash scripts/deploy/one-click-linux.sh` |
| Windows 裸机（无 PostgreSQL） | `powershell -File scripts/deploy/one-click-windows.ps1` |

裸机脚本会：创建 venv、安装依赖、生成 `.env`、启动 uvicorn，**需自行安装 PostgreSQL**。

> **OpenClaw Gateway**（`ws://127.0.0.1:18789`）不在本仓库内，对话功能需在宿主机另行启动 Gateway；Docker 部署时应用经 `host.docker.internal` 访问宿主机 Gateway。将仓库根目录 `skills/` 挂载到 Gateway 见 [openclaw-skills-deploy.md](openclaw-skills-deploy.md)。

## PostgreSQL 三库

```bash
# 创建用户与库（示例）
sudo -u postgres psql -c "CREATE USER openclaw_app WITH PASSWORD 'yourpass';"
sudo -u postgres psql -c "CREATE DATABASE openclaw_app OWNER openclaw_app;"
# 同理 openclaw_monitor、openclaw_news

# reports 表（主库）
psql "$OPENCLAW_DATABASE_URL" -f - <<'SQL'
CREATE TABLE IF NOT EXISTS reports (
  id BIGSERIAL PRIMARY KEY,
  ingest_id UUID NOT NULL UNIQUE,
  task_id TEXT,
  keyword TEXT NOT NULL,
  status TEXT CHECK (status IN ('queued','processing','published','failed')),
  generated_title TEXT,
  generated_at TIMESTAMPTZ,
  payload_json JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
SQL
```

监测库与新闻库表由服务首次使用时自动 `CREATE TABLE IF NOT EXISTS`。

## 生产环境

完整步骤（systemd、Nginx/Caddy、TLS、发布清单）见 **[server-deployment.md](server-deployment.md)**。

## 环境变量完整列表

见仓库根目录 [`.env.example`](../.env.example)。
