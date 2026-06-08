# 零基础部署指南

面向**第一次部署** OpenClaw News Publisher 的运维人员。假设你有一台 Linux 服务器（或本机），能使用终端，**不需要**预先了解 Python / Node / Docker 细节。

更完整的生产说明见 [production.md](production.md)。本地开发双进程见 [local.md](local.md)。

---

## 你需要准备什么

| 项目 | 最低要求 |
|------|----------|
| 操作系统 | Linux（Ubuntu 22.04+ 推荐）或 Windows（开发/内网） |
| 内存 | 2 GB+ |
| 磁盘 | 5 GB+（含依赖与数据库） |
| 网络 | 能 `git clone`；若用门户对话，需能访问 OpenClaw Gateway |
| 数据库 | PostgreSQL 14+，三个库（或用 Docker 一键自带） |

**前置检查（裸机）**：Python 3.11+、`node --version` ≥20、PostgreSQL 可连接。

---

## 第一步：获取代码

```bash
git clone <你的仓库地址> /opt/openclaw_news_publisher
cd /opt/openclaw_news_publisher
```

Windows 可用 Git Bash 或 PowerShell，路径示例：`C:\openclaw_news_publisher`。

---

## 第二步：配置环境变量

```bash
cp .env.example .env
```

用文本编辑器打开 `.env`，**至少**修改这三行数据库连接（把 `REPLACE_ME` 换成真实密码）：

```env
OPENCLAW_DATABASE_URL=postgresql://openclaw_app:你的密码@127.0.0.1:5432/openclaw_app
OPENCLAW_MONITORING_DATABASE_URL=postgresql://openclaw_monitor:你的密码@127.0.0.1:5432/openclaw_monitor
OPENCLAW_NEWS_DATABASE_URL=postgresql://openclaw_news:你的密码@127.0.0.1:5432/openclaw_news
```

生产环境还需设置：

```env
OPENCLAW_PRODUCTION=true
OPENCLAW_JWT_SECRET=至少32字符的随机字符串
```

**不要**把 `.env` 提交到 Git 或发给他人。

### 裸机 PostgreSQL 初始化

Docker 一键部署会自动执行 `scripts/docker/init-databases.sql`（三库 + `reports` 表）。

裸机需自行创建三库与用户，并执行主库 DDL。完整示例见 [local.md](local.md#postgresql-三库) 或参考 `scripts/docker/init-databases.sql`。

---

## 第三步：选择部署方式

### 方式 A：Docker（最简单，推荐新手）

适合：想快速跑起来、自带 PostgreSQL、不想手动装 Python/Node。

**前置**：安装 [Docker Engine](https://docs.docker.com/engine/install/) 与 Compose v2。

```bash
cd /opt/openclaw_news_publisher
bash deploy.sh --docker
```

或等价于：

```bash
bash scripts/deploy/one-click-docker.sh
```

脚本会：构建镜像 → 启动应用 + 数据库 → 等待健康检查通过。

验证：

```bash
curl http://127.0.0.1:8000/healthz
curl http://127.0.0.1:8000/healthz/db
```

浏览器打开：`http://服务器IP:8000/`

停止服务：

```bash
bash scripts/deploy/one-click-docker.sh --down
```

---

### 方式 B：裸机部署（已有 PostgreSQL）

适合：公司已有数据库、习惯 systemd 管理进程。

**前置**：Python 3.11+、Node.js 20+、PostgreSQL 三库已创建（见上文 DDL）。

```bash
cd /opt/openclaw_news_publisher
bash deploy.sh
```

`deploy.sh` 会自动执行：

1. `git pull` — 拉最新代码  
2. 创建/更新 `.venv` 并 `pip install` — 后端构建  
3. `cd frontend && npm ci && npm run build` — 前端构建  
4. 重启服务 — 启动时自动跑数据库迁移  
5. 访问 `/healthz` 与 `/healthz/db` — 健康检查  

若已配置 systemd（见 [production.md](production.md#4-systemd-服务单元)）：

```bash
bash deploy.sh --systemd
```

---

### 方式 C：Windows 开发机

```powershell
cd C:\openclaw_news_publisher
Copy-Item .env.example .env
# 编辑 .env 后：
bash deploy.sh
```

PowerShell 下若 `deploy.sh` 无法直接运行，可分步执行：

```powershell
git pull
python -m venv .venv
.\.venv\Scripts\pip install -e .
cd frontend; npm ci; npm run build; cd ..
bash scripts/local/restart-server.sh
```

或使用已有脚本：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/deploy/one-click-windows.ps1
```

---

## 第四步：首次登录

1. 浏览器打开 `http://127.0.0.1:8000/register` 或 `/login`  
2. 首次启动会自动创建 ADMIN：`admin@localhost` / `Test_648.`  
3. **生产环境请立即修改密码**  
4. 在 **账户** 页生成 per-user API Key，供 OpenClaw Agent 调用  
5. 普通用户：访问 `/register` 注册（需 `OPENCLAW_ALLOW_REGISTRATION=true`）

---

## 第五步：验证部署成功

| 检查项 | 命令 / 操作 | 期望结果 |
|--------|-------------|----------|
| 进程存活 | `curl http://127.0.0.1:8000/healthz` | `{"status":"ok"}` 类响应 |
| 数据库 | `curl http://127.0.0.1:8000/healthz/db` | `"ok":true` |
| 首页 | 浏览器打开 `/` | 看到门户界面 |
| 三库连通 | `bash scripts/local/verify-openclaw-databases.sh` | 全部 PASS |
| 工作流 | 打开 `/workflow` | 诊断页可加载 |

---

## 日常更新（发布后）

在服务器项目目录执行：

```bash
cd /opt/openclaw_news_publisher
bash deploy.sh
```

Docker 环境：

```bash
bash deploy.sh --docker
```

等价于：`git pull` → 重新构建 → 重启 → 健康检查。

---

## 磁盘清理（可选）

开发机或长期运行后，缓存与临时文件可能占空间。详见 [存储审计报告](../../reports/operations/storage-audit-2026-06-08.md)。

**务必先预览，再执行：**

```bash
# Linux / macOS — 仅显示将删除的内容
bash scripts/local/cleanup.sh

# 确认无误后
bash scripts/local/cleanup.sh --apply
```

```powershell
# Windows
powershell -File scripts/local/cleanup.ps1
powershell -File scripts/local/cleanup.ps1 -Apply
```

清理脚本**不会**删除：数据库、`.env`、Gateway 凭证（`openclaw-state/`）、用户备份、`content/reports/` 业务报告。

---

## 常见问题

### 1. `healthz/db` 失败

- 检查 `.env` 中三个 `OPENCLAW_*_DATABASE_URL` 是否正确  
- PostgreSQL 是否运行：`systemctl status postgresql`  
- 防火墙是否允许本机连接 5432  
- 运行：`bash scripts/local/verify-openclaw-databases.sh`

### 2. 首页空白或 404

- 确认已构建前端：`ls frontend/dist/index.html`  
- `.env` 中 `OPENCLAW_SERVE_SPA=true`  
- 重新执行：`cd frontend && npm ci && npm run build`

### 3. 门户对话连不上

- OpenClaw Gateway 是否在本机或内网运行  
- `.env` 中 `OPENCLAW_OPENCLAW_WS_URL` 地址是否正确  
- 生产需配置 Gateway 隔离，见 [gateway-isolation.md](../security/gateway-isolation.md)

### 4. Docker 构建很慢

- 首次构建需下载 Node/Python 镜像，属正常现象  
- 后续更新可用 `bash deploy.sh --docker`（利用缓存）

### 5. 端口 8000 被占用

```bash
export OPENCLAW_BIND_PORT=8080
bash deploy.sh
```

并在 `.env` 中同步修改 `OPENCLAW_BIND_PORT=8080`。

---

## 文件速查

| 文件 | 用途 |
|------|------|
| [deploy.sh](../../../deploy.sh) | 一键部署（pull + build + 重启 + 健康检查） |
| [cleanup.sh](../../../scripts/local/cleanup.sh) | 安全清理缓存与临时文件（Linux/macOS） |
| [cleanup.ps1](../../../scripts/local/cleanup.ps1) | 同上（Windows） |
| [storage-audit-2026-06-08.md](../../reports/operations/storage-audit-2026-06-08.md) | 磁盘与临时文件审计报告 |
| [one-click-docker.sh](../../../scripts/deploy/one-click-docker.sh) | Docker 首次安装 |
| [verify-openclaw-databases.sh](../../../scripts/local/verify-openclaw-databases.sh) | 三库连通性检查 |
| [production.md](production.md) | 生产环境完整指南 |

---

## 安全提醒（生产必做）

1. 修改默认 ADMIN 密码  
2. 设置 `OPENCLAW_PRODUCTION=true` 与强 JWT 密钥  
3. `.env` 权限：`chmod 600 .env`  
4. 公网用 Nginx/Caddy 做 HTTPS，不要直接暴露 `:8000`  
5. 不要把 `.env`、数据库备份提交到 Git  

---

*如有问题，先查看应用日志：*

- *Docker：`docker compose --profile full logs -f app`*  
- *systemd：`journalctl -u openclaw-news-publisher -f`*  
- *本地脚本：`tail -f /tmp/openclaw_news_publisher.server.log`*
