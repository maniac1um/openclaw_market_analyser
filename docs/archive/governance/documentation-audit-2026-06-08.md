# 文档体系审计报告

> **归档快照（2026-06-08）** — 迁移前审计记录。活跃入口：[PROJECT_DOCUMENT_INDEX.md](../../PROJECT_DOCUMENT_INDEX.md)

**审计日期**：2026-06-08  
**迁移执行**：2026-06-08（见 [documentation-migration-plan-2026-06-08.md](documentation-migration-plan-2026-06-08.md)）  
**审计范围**：`docs/`、`skills/`、根目录 `README.md`、`.github/`、关联 README（`frontend/`、`backups/`）

---

## 1. 文档清单与分类

### 1.1 Human Documentation（人类工程师文档）

面向运维、后端/前端开发、测试与架构阅读；描述系统如何部署、如何开发、如何联调。

| 路径 | 主题 | 状态 |
|------|------|------|
| `README.md` | 项目入口、快速启动、环境变量、文档地图 | 活跃 |
| `docs/human/architecture/overview.md` | 系统架构、三库、数据流 | 活跃 |
| `docs/human/deployment/local.md` | 本地开发与快速验证 | 活跃 |
| `docs/human/deployment/production.md` | 生产 / Docker / Nginx / systemd | 活跃 |
| `docs/human/deployment/openclaw-skills-gateway.md` | Gateway 挂载 `skills/`、API Key | 活跃 |
| `docs/human/development/developer-guide.md` | 模块说明、开发规范、常见任务 | 活跃 |
| `docs/human/development/cross-platform.md` | Win/Ubuntu 协作约定 | 活跃 |
| `docs/human/features/portal-chat.md` | 门户对话、WS、轮询 API | 活跃 |
| `docs/human/mobile/android-app.md` | Capacitor Android 内测 APK | 活跃（`apk-test` 分支） |
| `docs/human/api/openclaw-intake.md` | OpenClaw 入站 API 契约 | 活跃（权威契约） |
| `docs/human/security/gateway-isolation.md` | Gateway 网络与权限隔离（P0 运维） | 活跃 |
| `docs/human/testing/multi-user-test-plan.md` | 多用户测试用例清单 | 活跃 |
| `docs/api/openclaw-intake.md` | API 契约重定向 stub | 兼容 |
| `docs/security/GATEWAY_ISOLATION.md` | Gateway 隔离重定向 stub | 兼容 |
| `backups/README.md` | 本地备份目录安全规则 | 活跃（运维附注） |
| `.github/workflows/ci.yml` | CI 流水线（pytest、bandit、前端构建） | 活跃（无独立说明文档） |

### 1.2 OpenClaw Agent Documentation（OpenClaw Gateway 运行时文档）

面向 **OpenClaw Gateway 运行时 Agent**（cron、门户对话、外采 Agent 等）；`SKILL.md` 与 `_shared` 为执行指令。

**不是 Cursor Agent 文档。** Cursor IDE 内辅助开发的 AI 应读 `docs/` 与根目录治理文件（见 §1.7），不得以 `skills/` 作为自身操作手册。

| 路径 | 主题 | 状态 |
|------|------|------|
| `skills/README.md` | Skill 包入口、路径约定 | 活跃 |
| `skills/VERSIONS.md` | Skill 版本表 | 活跃 |
| `skills/CHANGELOG.md` | Skill 变更记录 | 活跃 |
| `skills/openclaw-conversational-assistant/SKILL.md` | 对话入口、意图路由 | 活跃 |
| `skills/openclaw-conversational-assistant/references/api-quickref.md` | API 速查表 | 活跃 |
| `skills/openclaw-user-workspace/SKILL.md` | 用户工作区只读聚合 | 活跃 |
| `skills/openclaw-report-security/SKILL.md` | 报告发布安全门 | 活跃 |
| `skills/openclaw-audit-events/SKILL.md` | 审计事件 | 活跃 |
| `skills/openclaw-news-publisher-enhanced/SKILL.md` | 新闻爬虫 + 报告入站 | 活跃 |
| `skills/openclaw-price-ingest-external/SKILL.md` | 外采价格 ingest | 活跃 |
| `skills/openclaw-price-ingest-external/README.md` | 外采 Skill 简短说明 | 活跃 |
| `skills/openclaw-price-analysis-reporting/SKILL.md` | 联合分析 + 报告 | 活跃 |
| `skills/openclaw-public-news-library/SKILL.md` | 新闻库 CRUD | 活跃 |
| `skills/_shared/agent-safety-baseline.md` | Agent 最低安全行为 | 活跃 |
| `skills/_shared/multi-user-auth.md` | 鉴权与数据隔离 | 活跃 |
| `skills/_shared/report-schema.md` | 报告 JSON 结构 | 活跃 |
| `skills/_shared/report-security.md` | 报告内容安全策略 | 活跃 |
| `skills/_shared/ownership-policy.md` | 资源归属策略 | 活跃 |
| `skills/_shared/portal-chat-routing.md` | 门户聊天 vs OpenClaw 外采/编排路由 | 活跃 |
| `skills/_shared/public-deploy-security.md` | 公网部署 Agent 检查 | 活跃 |
| `skills/_shared/quota-policy.md` | 配额与回执 | 活跃（部分 API 预埋） |
| `skills/_shared/workspace-api-roadmap.md` | 工作区 API 路线图 | 活跃（部分 API 预埋） |
| `skills/_shared/ci-skill-regression.md` | Skill 回归与 pytest 映射 | 活跃 |

### 1.3 Generated Reports（生成型报告 / 审计快照）

由安全审计、迁移项目或验证 Agent 产出；记录某一时间点的结论与评分，不宜作为「当前操作手册」唯一依据。

| 路径 | 主题 | 状态 |
|------|------|------|
| `docs/reports/security/hardening-plan-2026-06-05.md` | 安全加固计划 v1.8（Phase 1–4 闭环） | 快照（2026-06-05） |
| `docs/reports/security/verification-report-v5-2026-06-05.md` | 安全验证报告 v5（评分 86/100） | 快照（2026-06-05） |

### 1.4 Temporary Files（临时 / 进行中计划）

尚未归档、但主要工作已完成的规划类文档；Agent 可能误当作待办清单。

| 路径 | 主题 | 风险 |
|------|------|------|
| `skills/SKILL_REFACTOR_PLAN.md` | 归档重定向 stub → `docs/archive/skills/` | 低 |

### 1.5 Legacy Documents（历史 / 已实施方案）

描述已落地变更；保留作溯源，不应覆盖活跃运维文档。

| 路径 | 主题 | 说明 |
|------|------|------|
| `docs/archive/multi-user/migration-plan-2026-06-05.md` | 多用户 SaaS 迁移方案 v1.1 | **已实施**（Step 1–9，2026-06-05） |
| `docs/archive/skills/skill-refactor-plan-2026-06-06.md` | Skill 架构重构计划 | **已完成** |
| `frontend/README.md` | 指向 developer-guide 的简短说明 | 活跃 |
| `docs/archive/frontend/vite-template-readme.md` | Vite 官方模板 | 归档 |

### 1.6 Cursor Agent Documentation（Cursor IDE 开发辅助）

面向在本仓库内**改代码、改文档、做治理**的 Cursor Agent；**不包含** `skills/`。

| 路径 | 主题 | 状态 |
|------|------|------|
| `AGENT_DOCUMENTATION_RULES.md` | Cursor 读取范围、优先级、禁止项 | 活跃 |
| `PROJECT_DOCUMENT_INDEX.md` | 全项目文档入口 | 活跃 |
| `DOCUMENTATION_AUDIT.md` | 文档审计 | 活跃 |
| `DOCUMENTATION_MIGRATION_PLAN.md` | 迁移计划（未执行） | 活跃 |

Cursor 开发任务还应读 §1.1 中的 `docs/developer-guide.md`、`docs/architecture.md` 等工程文档。

### 1.7 统计摘要

| 分类 | 文件数（.md） | 备注 |
|------|---------------|------|
| Human Documentation | 14 | 含根 README、`backups/README.md` |
| OpenClaw Agent Documentation | 22 | `skills/`；Gateway 运行时 |
| Cursor Agent Documentation | 4 | 根目录治理元文档 |
| Generated Reports | 2 | 均在 `docs/security/` |
| Temporary Files | 1 | `SKILL_REFACTOR_PLAN.md` |
| Legacy Documents | 2 | 迁移计划 + Vite 模板 README |
| 非文档 | 1 | `.github/workflows/ci.yml` |
| **合计（项目 .md）** | **41** | 不含 `.pytest_cache/README.md`；Cursor 治理 4 与 Human 有交叉引用 |

---

## 2. 发现的问题

### 2.1 重复与内容重叠

| 问题 | 涉及文件 | 严重度 | 说明 |
|------|----------|--------|------|
| **鉴权三重叙述** | `docs/api/openclaw-intake.md`、`skills/_shared/multi-user-auth.md`、`docs/multi-user/MULTI_USER_MIGRATION_PLAN.md` | 中 | 三处均描述 per-user API Key / JWT；Agent 可能读迁移计划而非精简策略 |
| **报告安全双重叙述** | `skills/_shared/report-schema.md`、`skills/_shared/report-security.md`、`skills/openclaw-report-security/SKILL.md` | 低 | 分层合理，但字段长度限制需以 `report-schema` + `openclaw-intake` 为权威 |
| **门户聊天双重叙述** | `docs/portal-chat.md`、`skills/_shared/portal-chat-routing.md` | 低 | 前者偏 FastAPI 实现（人类/Cursor），后者偏 OpenClaw 运行时路由 |
| **部署文档分叉** | `docs/deployment.md`、`docs/server-deployment.md` | 低（有意） | 本地 vs 生产，互补；需在索引中明确「先读哪份」 |
| **安全运维 vs 审计报告** | `docs/security/GATEWAY_ISOLATION.md`、`SECURITY_HARDENING_PLAN.md` | 中 | G-01 在加固计划中引用隔离文档；Agent 读计划可能忽略活跃运维文档 |
| **项目结构重复** | `README.md`、`docs/developer-guide.md`、`docs/architecture.md` | 低 | 目录树与模块表多处出现 |
| **文档地图重复** | `README.md` §文档地图、`docs/cross-platform-development.md` §推荐阅读 | 低 | 缺少单一权威索引（本次将补 `PROJECT_DOCUMENT_INDEX.md`） |

### 2.2 失效 / 过时内容

| 问题 | 证据 | 严重度 |
|------|------|--------|
| **pytest 数量过时** | `SECURITY_HARDENING_PLAN.md` / `SECURITY_VERIFICATION_REPORT.md` 记载 **45/45**；当前仓库 `pytest --collect-only` 为 **102** 项 | 高 |
| **Skill 重构计划状态未归档** | `SKILL_REFACTOR_PLAN.md` 文首架构树仍含「（规划新增）」字样，但正文阶段 0–5 均已 ✅ | 中 |
| **skills 受众表述混淆** | `README.md`、`skills/README.md` 将 `skills/` 与「Cursor Agent」并列 | 高 | `skills/` 属 **OpenClaw 运行时**；Cursor 开发应读 `docs/` + 治理文件，而非把 Skill 当 Cursor 指令 |
| **Android 文档硬编码 IP** | `docs/android-app.md` 含 `https://115.120.202.223` | 低（环境相关，需标注可替换） |
| **多用户迁移「待定」项** | `MULTI_USER_MIGRATION_PLAN.md` 仍列 public 读方案 A、E2E 为「可选」 | 低 |

### 2.3 误读风险

#### Cursor Agent 误读

| 风险场景 | 后果 | 建议优先级 |
|----------|------|------------|
| Cursor 将 **`skills/SKILL.md` 当作自身操作手册** | 在 IDE 内模拟「发报告」「爬新闻」等业务流程 | P0 — `AGENT_DOCUMENTATION_RULES.md` 已区分 |
| Cursor 读取 **已实施** 的 `MULTI_USER_MIGRATION_PLAN.md` | 重复 DDL/配置建议 | P0 — 归档 |
| Cursor 读 **`frontend/README.md`** | 以为是项目前端指南 | P2 |
| Cursor 未读 **`docs/developer-guide.md`** 直接改代码 | 与模块边界/Dev 规范不一致 | P1 |

#### OpenClaw 运行时误读（`skills/` 受众）

| 风险场景 | 后果 | 建议优先级 |
|----------|------|------------|
| OpenClaw 未读 **`agent-safety-baseline.md`** 执行业务 | 跳过写操作确认、重试上限 | P0 |
| 读取 **SKILL_REFACTOR_PLAN** | 误判 Skill 重构待办 | P1 — 归档 |
| **`skills/` 与 `docs/api/` 双源权威** | 字段/鉴权不一致 | P1 — OpenClaw 以 `_shared` + `SKILL.md` 为准；工程契约以 `openclaw-intake` 为准 |

#### 通用（两类 Agent）

| 风险场景 | 后果 | 建议优先级 |
|----------|------|------------|
| 读取 **SECURITY_HARDENING_PLAN** 未修复项表 | 计划已闭环，易漏读摘要 | P1 — 移入 reports |

### 2.4 文档冲突

| 冲突点 | 文档 A | 文档 B | 当前事实（以代码为准） |
|--------|--------|--------|------------------------|
| Public 读权限过渡 | `MULTI_USER_MIGRATION_PLAN` §方案 B | `multi-user-auth.md` | 方案 B 已实施；迁移计划仍含方案 A 讨论 |
| Legacy API Key | `README` 默认 false | 部分 Skill 仍提 Legacy 场景 | `OPENCLAW_LEGACY_API_KEY_ENABLED` 默认 false |
| Gateway 绑定方式 | `GATEWAY_ISOLATION` 推荐 `lan` + ufw | `server-deployment` Docker 示例 | 需同时满足容器可达 + 防火墙 |
| 测试基线 | 安全报告 45 tests | 当前 102 tests | 报告数字仅作历史快照 |

### 2.5 结构性缺口

| 缺口 | 说明 |
|------|------|
| **无统一文档入口** | 依赖 `README.md` 内嵌表格 |
| **Cursor 与 OpenClaw 文档未显式分层** | `skills/` 被表述为 Cursor 可用，导致受众混淆 |
| **无 `AGENTS.md` / `.cursor/rules`** | Cursor 开发指引仅靠治理元文档 |
| **`.github` 无文档** | CI 行为仅能从 `ci.yml` 推断 |
| **`skills/` 不可迁入 `docs/`** | OpenClaw Gateway `extraDirs` 指向仓库根 `skills/`；重构时须保持路径稳定 |
| **治理元文档缺失** | 本次审计前无 `DOCUMENTATION_*`、`PROJECT_DOCUMENT_INDEX` |

---

## 3. 审计结论

1. **文档总量适中（41 个 .md）**，但 **人类文档 / Agent 文档 / 历史报告混放在 `docs/` 根与子目录**，缺少分层入口。
2. **`skills/` 体系较成熟**，是 **OpenClaw Gateway 运行时**权威层；**不应整体搬迁**，仅归档已完成计划类文件。
3. **最紧迫问题**：`skills/` 与 Cursor 受众混淆、安全报告 pytest 数字过时、已实施迁移计划仍位于活跃 `docs/` 路径。
4. **迁移已完成**（2026-06-08）：`docs/human|openclaw|reports|archive` 已落地；`PROJECT_DOCUMENT_INDEX.md` 为统一入口；`AGENT_DOCUMENTATION_RULES.md` **仅约束 Cursor**；`skills/` 保持 Gateway 根路径。

---

## 4. 扫描方法

```bash
# 枚举项目 markdown（排除 node_modules）
find . -maxdepth 4 -name "*.md" -not -path "./frontend/node_modules/*" -not -path "./.git/*"

# 测试数量核对
pytest --collect-only -q

# 核对 skills 受众表述
rg "Cursor" skills/README.md README.md
```

---

*本文件为治理交付物；迁移执行前请勿据此直接删除或移动源文件。*
