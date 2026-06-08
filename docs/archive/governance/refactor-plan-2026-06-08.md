# OpenClaw News Publisher — 项目治理重构方案

> **状态**：**ABCDE 已于 2026-06-08 执行完成。** 本文档为归档方案记录。

**角色**：Project Governance Agent  
**日期**：2026-06-08  
**依据**：[PROJECT_GOVERNANCE_REPORT.md](../reports/governance/audit-2026-06-08.md)（已迁入 `docs/reports/governance/`）

---

## 目标

| 指标 | 当前 | 目标 |
|------|------|------|
| 新开发者理解项目 | ~45 分钟（根目录干扰） | **≤30 分钟** |
| 新开发者完成部署 | Docker ~45 min；裸机 >90 min | **≤60 分钟**（Docker 主路径） |
| Agent / 人类文档分离 | 基本分离 | **彻底分离**（根目录零 Agent 产物） |
| Skill 职责 | 清晰 | **分区 + 版本表单一来源** |
| docs 结构 | human/openclaw/reports/archive | **+ project-brain + governance** |
| 可维护性 | 1 处逆依赖、文档漂移 | **Project Brain 作单一真相源** |

---

## 执行原则（Phase 4）

1. **先方案、后执行** — 本文件确认后再动手。
2. **禁止直接删除** — 一律先 ARCHIVE，保留 Git 历史可追溯。
3. **兼容 stub 保留 1 个发布周期** — `docs/api/`、`docs/security/` 重定向暂不删。
4. **不修改业务代码** — 本方案范围仅限文档、目录、脚本说明；Service 逆依赖另开 refactor PR。
5. **每步可回滚** — 单次 PR 只做一类变更（归档 / 索引 / project-brain）。

---

# Docs Structure

## 建议最终结构

```text
docs/
├── README.md                          # 文档根入口（保留，更新链接）
├── PROJECT_DOCUMENT_INDEX.md          # 全项目文档地图（人类 + Agent 导航）
├── AGENT_DOCUMENTATION_RULES.md       # Cursor Agent 读取规则
│
├── project-brain/                     # 【新建】项目单一真相源（30 分钟 onboarding）
│   ├── README.md                      # Project Brain 使用说明
│   ├── PROJECT_MAP.md                 # 目录、模块、受众、5 分钟速览
│   ├── ARCHITECTURE.md                # 架构、三库、数据流、API 分层
│   ├── ROADMAP.md                     # 演进路线（chat 持久化、Alembic 等）
│   ├── DECISIONS.md                   # ADR 式关键决策记录
│   ├── KNOWN_ISSUES.md                # 已知问题与技术债索引
│   └── SKILL_MAP.md                   # Skill 职责矩阵 + 阅读顺序摘要
│
├── human/                             # 人类工程师活跃文档（保留现有分区）
│   ├── README.md
│   ├── architecture/
│   │   └── overview.md                # 保留；与 project-brain/ARCHITECTURE 交叉引用
│   ├── deployment/
│   │   ├── local.md
│   │   ├── production.md
│   │   ├── openclaw-skills-gateway.md
│   │   └── getting-started.md         # 【新建】从 DEPLOYMENT_GUIDE 迁入精简版（1 小时路径）
│   ├── development/
│   │   ├── developer-guide.md
│   │   └── cross-platform.md
│   ├── api/
│   │   └── openclaw-intake.md         # API 契约权威
│   ├── security/
│   │   └── gateway-isolation.md       # P0 运维
│   ├── features/
│   │   └── portal-chat.md
│   ├── mobile/
│   │   └── android-app.md
│   └── testing/
│       └── multi-user-test-plan.md
│
├── openclaw/                          # OpenClaw Gateway 运行时索引（保留）
│   ├── README.md
│   ├── reading-order.md
│   └── crosswalk.md
│
├── reports/                           # 生成型报告 / 审计快照（扩展）
│   ├── README.md
│   ├── security/
│   │   ├── hardening-plan-2026-06-05.md
│   │   ├── verification-report-v5-2026-06-05.md
│   │   ├── audit-2026-06-08.md        # 【迁入】SECURITY_AUDIT_REPORT.md
│   │   └── patch-2026-06-08.md        # 【迁入】SECURITY_PATCH_REPORT.md
│   ├── operations/
│   │   └── storage-audit-2026-06-08.md # 【迁入】STORAGE_AUDIT.md
│   └── governance/
│       └── audit-2026-06-08.md        # 【迁入】PROJECT_GOVERNANCE_REPORT.md
│
├── archive/                           # 历史 / 已完成方案（扩展）
│   ├── README.md
│   ├── governance/                    # 保留
│   ├── multi-user/                    # 保留
│   ├── skills/                        # 保留
│   ├── frontend/
│   │   ├── vite-template-readme.md
│   │   └── visualization-plan-2026-06-08.md  # 【迁入】FRONTEND_VISUALIZATION_PLAN.md
│   ├── product/
│   │   └── ux-improvement-plan-2026-06-08.md # 【迁入】UX_IMPROVEMENT_PLAN.md
│   └── stubs/                         # 【新建】过期兼容 stub 最终归宿
│       └── README.md
│
├── api/                               # 兼容 stub（1 周期后 → archive/stubs/）
│   └── openclaw-intake.md
└── security/                          # 兼容 stub（1 周期后 → archive/stubs/）
    ├── GATEWAY_ISOLATION.md
    ├── SECURITY_HARDENING_PLAN.md
    └── SECURITY_VERIFICATION_REPORT.md
```

## 根目录文档收敛

| 当前位置 | 目标位置 | 根目录留存 |
|----------|----------|------------|
| `DEPLOYMENT_GUIDE.md` | `docs/human/deployment/getting-started.md` | 保留 **3 行 stub** 重定向 |
| `PROJECT_GOVERNANCE_REPORT.md` | `docs/reports/governance/audit-2026-06-08.md` | 保留 stub 或仅 Git 历史 |
| `SECURITY_AUDIT_REPORT.md` | `docs/reports/security/audit-2026-06-08.md` | 删除根副本（归档后） |
| `SECURITY_PATCH_REPORT.md` | `docs/reports/security/patch-2026-06-08.md` | 同上 |
| `STORAGE_AUDIT.md` | `docs/reports/operations/storage-audit-2026-06-08.md` | 同上 |
| `UX_IMPROVEMENT_PLAN.md` | `docs/archive/product/ux-improvement-plan-2026-06-08.md` | 同上 |
| `FRONTEND_VISUALIZATION_PLAN.md` | `docs/archive/frontend/visualization-plan-2026-06-08.md` | 同上 |

## README 收敛（目标）

根目录 `README.md` 仅保留：

1. 一句话 + 架构 Mermaid（5 行内）
2. **30 分钟快速启动**（5–6 步，不重复 DEPLOYMENT 全文）
3. 环境变量表（精简，完整列表链到 `.env.example`）
4. **文档入口表** — 指向 `docs/project-brain/PROJECT_MAP.md` 为首要链接

---

# Skill Structure

## 建议最终结构

```text
skills/
├── README.md                          # Gateway extraDirs 入口（保留）
├── VERSIONS.md                        # 版本单一来源（保留）
├── CHANGELOG.md                       # 变更记录（保留）
│
├── production/                        # 【新建】生产 Skill（Gateway 默认加载）
│   ├── openclaw-conversational-assistant/
│   ├── openclaw-user-workspace/
│   ├── openclaw-report-security/
│   ├── openclaw-audit-events/
│   ├── openclaw-news-publisher-enhanced/
│   ├── openclaw-price-ingest-external/
│   ├── openclaw-price-analysis-reporting/
│   └── openclaw-public-news-library/
│
├── shared/                            # 【重命名】_shared → shared（或保留 _shared  symlink）
│   ├── agent-safety-baseline.md
│   ├── multi-user-auth.md
│   ├── report-schema.md
│   ├── report-security.md
│   ├── ownership-policy.md
│   ├── portal-chat-routing.md
│   ├── public-deploy-security.md
│   ├── quota-policy.md
│   ├── workspace-api-roadmap.md
│   └── ci-skill-regression.md
│
├── experimental/                      # 【新建】试验 Skill（默认不挂载 Gateway）
│   └── README.md                      # 准入标准：须标注 skill_version + 过期日
│
└── deprecated/                        # 【新建】弃用 Skill（只读，不加载）
    └── README.md
```

## 迁移策略（两阶段，降低 Gateway 风险）

### 阶段 A — 软分区（推荐先做）

- **不移动** Skill 目录，仅在 `skills/README.md` 与 `SKILL_MAP.md` 中用表格标注 `production | experimental | deprecated`。
- Gateway `extraDirs` 仍指向 `skills/`（现状不变）。
- 删除 `skills/SKILL_REFACTOR_PLAN.md` stub，链接改指 `docs/archive/skills/`。

### 阶段 B — 物理分区（确认 Gateway 路径后）

- 将 8 个 `openclaw-*` 移入 `skills/production/`。
- Gateway 配置改为 `extraDirs: ["/path/to/repo/skills/production", "/path/to/repo/skills/shared"]`。
- 各 Skill 内 `../_shared/` 相对路径批量更新为 `../shared/`（或保留 `_shared` 目录名 + symlink `shared -> _shared` **避免大规模链接修复**）。

**推荐**：阶段 B 采用 **`shared/` 为别名目录，保留 `_shared/` 实体**，双路径只读同一内容，6 个月后再删 `_shared`。

## Skill 文档更新清单

| 文件 | 变更 |
|------|------|
| `docs/openclaw/reading-order.md` | 若路径变更，更新 Skill 相对路径 |
| `docs/openclaw/crosswalk.md` | 不变 |
| `docs/human/deployment/openclaw-skills-gateway.md` | 补充 production/ 挂载示例 |
| `skills/VERSIONS.md` | 增加「分区」列 |

## 不合并的 Skill（确认）

| Skill 对 | 理由 |
|----------|------|
| `conversational-assistant` + 专项 Skill | 路由 vs 执行，委派模式正确 |
| `price-ingest` + `price-analysis` | cron 高频 vs 报告低频 |
| `user-workspace` + `audit-events` | audit API 预埋后独立演进 |

---

# Archive Structure

## 建议最终结构

```text
archive/                               # 仓库根【可选】与 docs/archive/ 二选一
```

**决策**：**不创建仓库根 `archive/`**，统一使用 **`docs/archive/`**，避免双 archive 混淆。

```text
docs/archive/
├── README.md                          # 归档索引 + 「勿当待办」声明
├── governance/
│   ├── README.md
│   ├── documentation-audit-2026-06-08.md
│   ├── documentation-migration-plan-2026-06-08.md
│   └── refactor-plan-2026-06-08.md    # 【迁入】本文件执行完成后
├── multi-user/
│   └── migration-plan-2026-06-05.md
├── skills/
│   └── skill-refactor-plan-2026-06-06.md
├── frontend/
│   ├── vite-template-readme.md
│   └── visualization-plan-2026-06-08.md
├── product/
│   └── ux-improvement-plan-2026-06-08.md
└── stubs/                             # 兼容重定向最终归宿
    ├── README.md
    ├── openclaw-intake-redirect.md    # 自 docs/api/ 迁入
    └── gateway-isolation-redirect.md  # 自 docs/security/ 迁入
```

## 若未来需要仓库根 `archive/`

仅当运维脚本/Skill 产物需要与文档分离时创建：

```text
archive/                               # 仓库根（非 docs/）
├── deprecated-skills/                   # 整包 Skill 快照
├── deprecated-docs/                     # 不推荐；优先 docs/archive/
└── legacy-scripts/                    # 已废弃脚本（如旧 deploy 路径）
```

**当前结论**：`legacy-scripts/` 暂无候选；`scripts/` 全部活跃，**不创建根 archive/**。

---

# Project Brain

建立 `docs/project-brain/` 作为 **30 分钟 onboarding 单一入口**。各文件职责与内容纲要如下。

## `docs/project-brain/README.md`

- Project Brain 是什么、谁该读、与 `PROJECT_DOCUMENT_INDEX` 的关系。
- 阅读顺序：`PROJECT_MAP` → `ARCHITECTURE` → 按角色跳 deployment / openclaw。

## `docs/project-brain/PROJECT_MAP.md`

**目标**：5 分钟建立心智模型。

| 章节 | 内容 |
|------|------|
| 一句话 | OpenClaw 新闻分析 SaaS：Agent 入站 → 三库 → React 门户 |
| 仓库地图 | `app/`（后端）、`frontend/`、`skills/`、`docs/`、`scripts/` — **明确无 backend/** |
| 三受众 | 人类 → `docs/human/`；OpenClaw → `skills/`；Cursor → `AGENT_DOCUMENTATION_RULES.md` |
| 外部依赖 | PostgreSQL ×3、OpenClaw Gateway（可选，对话用） |
| 10 分钟路径 | clone → Docker 一键 → login → account 生成 Key |
| 链接表 | 部署 / API / 安全 P0 / Skill 索引 |

## `docs/project-brain/ARCHITECTURE.md`

**目标**：15 分钟理解系统设计。

- 系统 Mermaid（与 `human/architecture/overview.md` 同源，更精简）
- 三库表 + 自动建表规则
- API 四层：`openclaw` / `public` / `auth` / `chat`
- 报告流水线：Intake → JobRunner → Publish
- 多用户：`QueryContext`、JWT、per-user API Key
- Gateway 双 Agent 隔离（摘要 + 链到 gateway-isolation.md）
- **分层约定**：API → Service → DB；标注已知逆依赖 TD-H1

## `docs/project-brain/ROADMAP.md`

**目标**：演进预期，非承诺排期。

| 项 | 优先级 | 来源 |
|----|--------|------|
| Chat run PostgreSQL 持久化 | P1 | architecture/overview §演进 |
| Alembic 迁移 | P1 | TD-M5 |
| 裸机 DB bootstrap 脚本 | P1 | TD-H4 |
| OpenClaw API IDOR 修复 | P0 安全 | SECURITY_AUDIT |
| Service 层逆依赖修复 | P2 | TD-H1 |
| Skill experimental 分区 | P3 | 本方案 |
| 兼容 stub 清理 | P3 | docs/api、docs/security |

## `docs/project-brain/DECISIONS.md`

ADR 格式，初始条目：

| ID | 决策 | 日期 | 状态 |
|----|------|------|------|
| ADR-001 | 后端目录命名为 `app/` 非 `backend/` | — | 接受 |
| ADR-002 | PostgreSQL 三库分离 | — | 接受 |
| ADR-003 | Skill 权威路径 `skills/` via Gateway extraDirs | 2026-06 | 接受 |
| ADR-004 | 文档三分：human / openclaw / reports+archive | 2026-06-08 | 接受 |
| ADR-005 | Legacy 全局 API Key 默认关闭 | 2026-06 | 接受 |
| ADR-006 | Project Brain 为 onboarding SSOT | 2026-06-08 | 提议中 |

## `docs/project-brain/KNOWN_ISSUES.md`

| ID | 问题 | 严重度 | 跟踪 |
|----|------|--------|------|
| KI-001 | `news_analysis_service` → API 逆依赖 | 中 | TD-H1 |
| KI-002 | pytest 数量文档漂移 | 低 | 115 tests |
| KI-003 | 根目录 Agent 报告未归档 | 中 | 本方案 PR-1 |
| KI-004 | OpenClaw monitoring/news IDOR | 高 | SECURITY_AUDIT |
| KI-005 | audit-events API 预埋未全实现 | 低 | workspace-api-roadmap |
| KI-006 | chat_run_store 内存态 | 中 | ROADMAP |

## `docs/project-brain/SKILL_MAP.md`

| Skill | 一句话职责 | 委派关系 | 必读 _shared |
|-------|------------|----------|--------------|
| conversational-assistant | 对话入口 + 路由 | → 各专项 | agent-safety, multi-user-auth |
| user-workspace | 我的资源只读 | ← conversational | ownership-policy |
| report-security | 发布前五项校验 | ← news/analysis | report-schema, report-security |
| news-publisher-enhanced | 爬虫 + 报告入站 | → report-security | public-deploy-security |
| price-ingest-external | 外采价格入库 | — | quota-policy |
| price-analysis-reporting | 联合分析 + 报告 | → report-security | report-schema |
| public-news-library | 新闻库 | — | report-security (URL) |
| audit-events | 审计追溯 | → user-workspace | workspace-api-roadmap |

附：阅读顺序摘要（链到 `docs/openclaw/reading-order.md`）。

---

# Cleanup Candidates

## 必须保留（MUST KEEP）

| 路径 | 理由 |
|------|------|
| `README.md` | 项目主入口 |
| `app/` | 后端全部代码 |
| `frontend/src/`、`frontend/package.json` | 前端源码 |
| `skills/openclaw-*/SKILL.md` | Gateway 运行时 |
| `skills/_shared/**` | 策略权威 |
| `skills/README.md`、`VERSIONS.md`、`CHANGELOG.md` | Skill 元数据 |
| `docs/human/**`（活跃文档） | 人类工程师 |
| `docs/openclaw/**` | OpenClaw 索引 |
| `docs/PROJECT_DOCUMENT_INDEX.md` | 文档地图 |
| `docs/AGENT_DOCUMENTATION_RULES.md` | Cursor 规则 |
| `scripts/**` | 部署与本地脚本 |
| `tests/**` | pytest |
| `deploy.sh` | 裸机部署编排 |
| `docker-compose.yml`、`Dockerfile` | 容器部署 |
| `.env.example` | 环境模板 |
| `pyproject.toml` | Python 包 |
| `cleanup.sh`、`cleanup.ps1` | 磁盘治理 |
| `.github/workflows/ci.yml` | CI |

## 可以归档（ARCHIVE — 移动，不删除）

| 源路径 | 目标路径 | PR |
|--------|----------|-----|
| `SECURITY_AUDIT_REPORT.md` | `docs/reports/security/audit-2026-06-08.md` | PR-1 |
| `SECURITY_PATCH_REPORT.md` | `docs/reports/security/patch-2026-06-08.md` | PR-1 |
| `STORAGE_AUDIT.md` | `docs/reports/operations/storage-audit-2026-06-08.md` | PR-1 |
| `PROJECT_GOVERNANCE_REPORT.md` | `docs/reports/governance/audit-2026-06-08.md` | PR-1 |
| `UX_IMPROVEMENT_PLAN.md` | `docs/archive/product/ux-improvement-plan-2026-06-08.md` | PR-1 |
| `FRONTEND_VISUALIZATION_PLAN.md` | `docs/archive/frontend/visualization-plan-2026-06-08.md` | PR-1 |
| `skills/SKILL_REFACTOR_PLAN.md` | 删除 stub（全文已在 archive） | PR-1 |
| `DEPLOYMENT_GUIDE.md` | `docs/human/deployment/getting-started.md` + 根 stub | PR-2 |

## 可以删除（DELETE — 仅本地可再生或纯 stub）

| 路径 | 条件 | 方式 |
|------|------|------|
| `frontend/dist/**` | 本地构建产物 | `cleanup.sh --aggressive` 或 `.gitignore` 已忽略 |
| `frontend/node_modules/**` | 本地依赖 | `npm ci` 再生 |
| `.venv/**` | 本地 venv | `pip install -e .` 再生 |
| `.pytest_cache/**` | 测试缓存 | `cleanup.sh` |
| `skills/*/runs/**` | Skill 中间文件 | `cleanup.sh` |
| 根目录归档后原文件 | PR-1 merge 后 | `git rm` 根副本（内容已在 docs/） |
| `docs/api/`、`docs/security/` stub | **1 个发布周期后** | 移入 `docs/archive/stubs/` 或删 |

## 暂不处理（DEFER）

| 项 | 理由 |
|----|------|
| `app/services/news_analysis_service.py` 逆依赖 | 代码 refactor，非文档治理 |
| Skill 物理移入 `production/` | 需 Gateway 配置变更 + 回归 |
| 创建根 `archive/` | 与 `docs/archive/` 重复 |
| 创建 `backend/`  symlink | 可选便利，非必须 |

---

# 执行计划（确认后分 PR）

## PR-1：根目录 Agent 产物归档

1. 创建 `docs/reports/security/`、`operations/`、`governance/` 子目录（若不存在）。
2. 创建 `docs/archive/product/`、`frontend/` 子目录。
3. `git mv` 六份根目录报告/plan 至目标路径。
4. 各原路径留 3–5 行 stub 重定向（可选，推荐 DEPLOYMENT 留 stub）。
5. 更新 `docs/PROJECT_DOCUMENT_INDEX.md`、`docs/reports/README.md`。
6. 更新 `docs/archive/README.md` 索引。

**验收**：根目录仅剩 `README.md`、`DEPLOYMENT_GUIDE.md`（stub）、`deploy.sh`、`docker-compose.yml`、`pyproject.toml`、治理方案两份。

## PR-2：Project Brain 建立

1. 创建 `docs/project-brain/` 七文件（按上文纲要写入）。
2. `README.md` 文档入口首链改为 `docs/project-brain/PROJECT_MAP.md`。
3. `PROJECT_DOCUMENT_INDEX.md` 增加 §Project Brain；pytest 更新为 **115**。
4. `.env.example` L21 链接改为 `docs/human/security/gateway-isolation.md`。

**验收**：新工程师按 PROJECT_MAP → getting-started 可在 30 min 内理解 + Docker 部署。

## PR-3：部署文档收敛

1. 将 `DEPLOYMENT_GUIDE.md` 全文迁入 `docs/human/deployment/getting-started.md`。
2. 根目录 `DEPLOYMENT_GUIDE.md` 改为 stub。
3. `local.md` 顶部增加「零基础请先读 getting-started.md」。
4. 文档化 `scripts/local/bootstrap-postgres.sh`（**可先写文档，脚本后补**）。

**验收**：部署叙述单一权威路径 + 2 份细分（local / production）。

## PR-4：Skill 软分区（可选）

1. 更新 `skills/README.md` 增加 production 表。
2. 写入 `docs/project-brain/SKILL_MAP.md`。
3. 删除 `skills/SKILL_REFACTOR_PLAN.md`（若 PR-1 未做）。

**验收**：Gateway 配置无变更；Skill 职责可查表。

## PR-5：兼容 stub 清理（1 个发布周期后）

1. `docs/api/`、`docs/security/` → `docs/archive/stubs/`。
2. 全仓库 grep 更新外链。
3. `docs/archive/stubs/README.md` 说明过期日期。

---

# 成功标准复验

| 标准 | PR 完成后验证方式 |
|------|-------------------|
| 30 分钟理解 | 新同事仅读 `project-brain/PROJECT_MAP` + `ARCHITECTURE` + README，能画出三库与 API 分层 |
| 1 小时部署 | 按 `getting-started.md` Docker 路径计时 ≤60 min |
| Agent/人类分离 | 根目录无 `*_REPORT.md` / `*_PLAN.md`；Cursor 读 `AGENT_DOCUMENTATION_RULES` |
| Skill 职责明确 | `SKILL_MAP.md` 覆盖 8 Skill + 委派关系 |
| docs 结构清晰 | `PROJECT_DOCUMENT_INDEX` 与目录树一致 |
| 可维护性 | `KNOWN_ISSUES` + `ROADMAP` 有主责条目；逆依赖已登记 |

---

## 确认清单

- [x] **A.** 根目录报告归档至 `docs/reports/` 与 `docs/archive/`（2026-06-08）
- [x] **B.** 建立 `docs/project-brain/` 七文件（2026-06-08）
- [x] **C.** `DEPLOYMENT_GUIDE.md` 迁入 `getting-started.md` + 根 stub（2026-06-08）
- [x] **D.** Skill 软分区（`skills/README.md` + `SKILL_MAP.md`）（2026-06-08）
- [x] **E.** 兼容 stub 保留；`docs/archive/stubs/README.md` 记录保留策略（2026-06-08）

---

*本方案已于 2026-06-08 执行完成。*
