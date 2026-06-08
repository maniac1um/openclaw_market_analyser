# 存储审计报告（Storage Audit）

**项目**：OpenClaw News Publisher  
**扫描日期**：2026-06-08  
**扫描范围**：`app/`（后端）、`frontend/`、`docs/`、`skills/`、`logs/`（若存在）、`scripts/`  
**说明**：本仓库后端代码目录为 `app/`，非 `backend/`；下文「后端」均指 `app/`。

---

## 1. 持续增长目录

以下目录在正常运行、开发或 Agent 任务执行后会持续写入，需纳入磁盘监控与定期清理策略。

| 路径 | 来源 | 增长机制 | 典型体量（本机快照） |
|------|------|----------|---------------------|
| `content/reports/raw/` | 报告入站 (`intake_service`) | 每份 Agent 报告写入 `{id}.json` | 运行时创建；当前未检出文件 |
| `content/reports/rendered/` | 报告渲染 (`report_service`) | 每份报告渲染后写入 JSON | 运行时创建；当前未检出文件 |
| `frontend/node_modules/` | `npm install` / `npm ci` | 依赖安装 | ~241 MB |
| `.venv/` | `pip install -e .` | Python 虚拟环境与包 | 视环境而定 |
| `frontend/dist/` | `npm run build` | 前端构建产物（每次 build 覆盖） | ~612 KB |
| `skills/*/runs/` | OpenClaw Skill / 爬虫 | `--output` 或任务中间 JSON | 按需创建 |
| `skills/*/.openclaw/` | OpenClaw 在 Skill 副本下的运行时缓存 | Agent 会话/任务态 | 按需创建 |
| `openclaw-state/` | Gateway ADMIN device 凭证 | Docker 挂载或本地配对 | ~32 KB（含密钥，**禁止清理**） |
| `openclaw-portal-state/` | Gateway USER 受限 device 凭证 | 同上 | ~32 KB（含密钥，**禁止清理**） |
| `backups/` | 运维手动快照 | 数据库 dump、配置备份 | 当前仅 README |
| Docker `pgdata` 卷 | `docker compose --profile full` | PostgreSQL 数据文件 | 随业务增长 |
| `/tmp/openclaw_news_publisher.server.log` | `scripts/local/start-server.sh` | uvicorn 标准输出追加 | 无上限（需轮转） |
| `$TEMP/openclaw_news_publisher.server.log` (Windows) | 同上 | 同上 | 无上限 |

**PostgreSQL 三库**（不在仓库目录内，但为最大持久化存储）：

- `openclaw_app` — 用户、报告、会话
- `openclaw_monitor` — 价格监测
- `openclaw_news` — 新闻库

---

## 2. 缓存目录

可安全再生的构建/测试/工具缓存，删除后下次运行会自动重建。

| 路径 | 类型 | 再生方式 |
|------|------|----------|
| `**/__pycache__/` | Python 字节码 | 下次 import / pytest |
| `.pytest_cache/` | pytest 缓存 | 下次 `pytest` |
| `.mypy_cache/` | mypy 类型检查缓存 | 下次 mypy |
| `.ruff_cache/` | Ruff linter 缓存 | 下次 ruff |
| `htmlcov/` | coverage HTML 报告 | 下次 `pytest --cov` |
| `.coverage` | coverage 数据文件 | 下次测试 |
| `frontend/node_modules/.cache/` | 部分前端工具缓存 | 下次 build |
| `frontend/.vite/` | Vite 开发缓存（若存在） | 下次 `npm run dev` |
| `skills/*/tools/__pycache__/` | Skill 工具字节码 | 下次执行 |
| `skills/*/scripts/__pycache__/` | Skill 脚本字节码 | 下次执行 |
| `skills/*/.openclaw/` | Skill 本地 OpenClaw 缓存 | 下次 Agent 任务 |
| `*.egg-info/` | setuptools 元数据 | 下次 `pip install -e .` |
| `.cursor/` | Cursor IDE 本地索引 | IDE 自动重建 |

**本机快照**：检出 13 处 `__pycache__`、1 处 `.pytest_cache`（~40 KB）。

---

## 3. 临时文件

生命周期短、任务结束后可删除的文件。

| 路径 / 模式 | 来源 | 说明 |
|-------------|------|------|
| `/tmp/tmp_*.json` 或仓库根 `tmp_*.json` | 测试/调试 | `.gitignore` 已忽略 |
| `skills/*/report_payload.json` | `news_crawler.py` 默认输出 | Skill 任务产物 |
| `skills/*/runs/*` | 爬虫/Agent 建议输出目录 | 见 `skills/openclaw-news-publisher-enhanced/SKILL.md` §13 |
| `skills/*/gold_price_report.json` | Skill 示例 payload | `skill_cleanup.py` 默认可删 |
| `skills/*/badminton_price_report.json` | 同上 | 同上 |
| `app/services/openclaw_chat_bridge.py` | `tempfile.TemporaryDirectory()` | **进程内临时**，不落盘 |
| `.env.bak.*` | `one-click-docker.sh --force-env` | Docker 部署备份的旧 env |

**注意**：`content/reports/{raw,rendered}/*.json` 为**持久化业务副本**（同时入 PostgreSQL），不属于「临时文件」，默认清理脚本**不删除**。

---

## 4. 日志文件

| 路径 | 写入方 | 轮转策略 | 清理建议 |
|------|--------|----------|----------|
| `/tmp/openclaw_news_publisher.server.log` | 本地 `start-server.sh` | 无内置轮转 | 超过 30 天可截断或删除 |
| `$TEMP/openclaw_news_publisher.server.log` | Windows 本地启动 | 无 | 同上 |
| `/tmp/openclaw_news_publisher.uvicorn.pid` | PID 文件 | 进程退出后残留 | stop 脚本会删；可安全清理 stale pid |
| `frontend/logs/`（若存在） | npm / Vite | 前端 `.gitignore` 忽略 | 可清空 |
| 项目根 `logs/` | **当前不存在** | — | 若未来创建，纳入过期清理 |
| `journalctl -u openclaw-news-publisher` | systemd 生产部署 | 系统 journald 策略 | 用 `journalctl --vacuum-time` |
| `docker compose logs` | Docker 部署 | Docker 日志驱动 | `docker compose logs` 只读；清理用 Docker 日志策略 |

应用内日志：`app/main.py` 使用 `logging.basicConfig` 输出到 **stdout/stderr**，无独立文件 handler。

---

## 5. 运行时文件

服务运行期间存在、重启后可能丢失或需保留的状态。

| 路径 / 资源 | 类型 | 重启影响 |
|-------------|------|----------|
| `chat_run_store`（内存） | 门户对话后台任务 | 重启后进行中任务丢失 |
| `openclaw-state/` | Gateway ADMIN 配对密钥 | **必须保留** |
| `openclaw-portal-state/` | Gateway USER 配对密钥 | **必须保留** |
| `content/reports/` | 报告 JSON 镜像 | 保留；DB 为主、文件为辅 |
| Docker 容器内 `/app/content/reports/` | 同上（镜像内） | 容器 recreate 会丢失 unless 挂载卷 |
| `frontend/dist/` | SPA 静态资源 | 部署必需；`npm run build` 再生 |
| `.env` | 运行配置 | **必须保留** |
| `/tmp/openclaw_news_publisher.uvicorn.pid` | 进程 PID | 运行时有效 |

---

## 6. 建议保留文件

| 类别 | 路径 / 资源 | 原因 |
|------|-------------|------|
| 版本控制 | `.git/` | 源码历史 |
| 配置 | `.env`、`.env.example` | 密钥与 DSN（`.env` 不入库） |
| 数据库 | PostgreSQL 三库 + Docker `pgdata` 卷 | 业务主数据 |
| Gateway 凭证 | `openclaw-state/`、`openclaw-portal-state/` | 门户聊天配对，删后需重新配对 |
| 用户/运维备份 | `backups/` 内快照 | 灾难恢复 |
| 报告镜像 | `content/reports/` | 与 DB 同步的 JSON 副本 |
| Skill 配置 | `skills/*/config/`、`SKILL.md`、`scripts/` | Agent 运行时权威定义 |
| 前端源码 | `frontend/src/`、`package-lock.json` | 构建输入 |
| 后端源码 | `app/`、`pyproject.toml` | 运行输入 |
| 文档 | `docs/human/`、`docs/openclaw/`、`skills/` | 运维与 Agent 规范 |
| 迁移脚本 | `scripts/migrations/` | DDL 参考；启动时亦自动迁移 |
| Docker 初始化 | `scripts/docker/init-databases.sql` | 新库初始化 |

---

## 7. 建议清理文件

按**安全优先级**分组；详见 [scripts/local/cleanup.sh](../../../scripts/local/cleanup.sh) / [cleanup.ps1](../../../scripts/local/cleanup.ps1)（默认 dry-run，需显式 `--apply` / `-Apply` 才删除）。

### 7.1 默认可安全清理（脚本默认包含）

| 目标 | 说明 |
|------|------|
| `**/__pycache__/` | Python 字节码 |
| `.pytest_cache/` | 测试缓存 |
| `.mypy_cache/`、`.ruff_cache/` | 工具缓存 |
| `htmlcov/`、`.coverage` | 覆盖率产物 |
| `skills/*/runs/*` | Skill 任务临时 JSON |
| `skills/*/.openclaw/` | Skill 本地 OpenClaw 缓存（**非**仓库根 `openclaw-state/`） |
| `skills/*/report_payload.json` | 爬虫默认输出 |
| `skills/*/*_price_report.json` | Skill 示例 payload |
| 根目录 `tmp_*.json` | 测试临时 JSON |
| 过期本地服务日志 | `/tmp/openclaw_news_publisher.server.log` 等，默认 >30 天 |

### 7.2 可选清理（需 `--aggressive` 或单独 flag）

| 目标 | 风险 | 说明 |
|------|------|------|
| `frontend/node_modules/` | 低 | 需重新 `npm ci` |
| `frontend/dist/` | 中 | 需重新 `npm run build` 才能对外服务 |
| `.venv/` | 中 | 需重新 `pip install -e .` |
| `*.egg-info/` | 低 | 重装再生 |
| `.env.bak.*` | 低 | Docker 部署旧 env 备份 |
| `frontend/android/build/`、`.gradle/` | 低 | Android 构建缓存 |

### 7.3 禁止清理

| 目标 | 原因 |
|------|------|
| `.git/` | 源码 |
| `.env` | 生产密钥 |
| `openclaw-state/`、`openclaw-portal-state/` | Gateway 配对凭证 |
| `backups/` 内业务备份 | 灾难恢复 |
| `content/reports/` | 业务报告镜像 |
| PostgreSQL / `pgdata` | 主数据库 |
| `docs/` 内已归档报告 | 合规与历史审计追溯 |

---

## 附录 A：按目录扫描摘要

### `app/`（后端）

- 13 处 `__pycache__`（~776 KB 源码 + 缓存）
- 运行时写入：`content/reports/`（配置见 `app/core/config.py`）
- 无独立日志文件

### `frontend/`

- `node_modules/` ~241 MB、`dist/` ~612 KB
- `.gitignore` 忽略：`logs/`、`dist/`、`node_modules/`
- Android：`frontend/android/build/`、`.gradle/` 为构建缓存（开发机构建 APK 时产生）

### `docs/`

- 纯 Markdown，体量小（~340 KB）
- `docs/reports/` — 历史快照报告（**保留**）
- `docs/archive/` — 已归档治理/迁移文档（**保留**）
- 不产生运行时缓存

### `skills/`

- 9 个 Skill 包 + `_shared/` 共享规范
-  ephemeral 模式：`runs/`、`.openclaw/`、`report_payload.json`（见 `tools/skill_cleanup.py`）
- 保留：`config/whitelist.json`（历史列表可 `--prune-whitelist-history` 可选修剪）

### `logs/`

- **项目根不存在** `logs/` 目录
- 日志主要落在系统 `/tmp` 或 journald / Docker

### `scripts/`

- 部署：`scripts/deploy/one-click-{docker,linux,windows}.sh`
- 本地：`scripts/local/{start,stop,restart}-server.sh`
- 迁移：`scripts/migrations/001_multi_user.sql`（应用启动时 `run_multi_user_migrations()` 亦会执行）

---

## 附录 B：与 `.gitignore` 对照

已忽略且适合清理的条目：

```
__pycache__/  .pytest_cache/  .mypy_cache/  .ruff_cache/  htmlcov/  .coverage
frontend/node_modules/  frontend/dist/
tmp_*.json  content/reports/raw/*.json  content/reports/rendered/*.json
openclaw-state/  openclaw-portal-state/  backups/*  .env
```

---

## 附录 C：推荐运维节奏

| 频率 | 动作 |
|------|------|
| 每周 | `bash scripts/local/cleanup.sh` 审查；开发机可 `--apply` |
| 每次部署前 | `bash deploy.sh`（含 pull、build、健康检查） |
| 每月 | 检查 `/tmp` 服务日志体积；Docker `docker system df` |
| 按需 | Skill 任务后 `python skills/.../tools/skill_cleanup.py` |

---

*本报告仅做分析，未删除任何文件。执行清理请使用 [scripts/local/cleanup.sh](../../../scripts/local/cleanup.sh) 并先 dry-run。*
