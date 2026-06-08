# 文档迁移计划

> **归档快照（2026-06-08）** — 迁移已执行。活跃入口：[PROJECT_DOCUMENT_INDEX.md](../../PROJECT_DOCUMENT_INDEX.md)

**版本**：1.0  
**日期**：2026-06-08  
**状态**：**已执行**（2026-06-08）

---

## 1. 设计原则

1. **`skills/` 保留在仓库根目录** — OpenClaw Gateway `skills.load.extraDirs` 依赖此路径；仅迁移「已完成计划」类元文档。`skills/` 面向 **OpenClaw 运行时**，与 Cursor Agent 无关。
2. **不删除源路径** — 首次迁移采用「复制 + 原路径留 stub 重定向」或「git mv + stub」；本计划仅列出目标路径，执行阶段再定 stub 策略。
3. **人类文档与 Agent 文档分离索引** — 内容可交叉引用，但目录层级清晰。
4. **报告与归档带日期/版本后缀** — 避免 Agent 将快照当作最新运维手册。

---

## 2. 目标目录结构（第二阶段设计）

### 2.1 目录树

```
docs/
├── human/                          # 人类工程师：部署、开发、运维、测试
│   ├── getting-started/            # 快速上手（可选：从 README 拆出）
│   ├── architecture/
│   ├── deployment/
│   ├── development/
│   ├── features/
│   ├── mobile/
│   ├── security/                   # 活跃安全运维（非审计快照）
│   ├── api/
│   └── testing/
├── openclaw/                       # OpenClaw 运行时文档索引（非 Skill 正文）
│   ├── README.md                   # 指向 skills/ 的权威说明
│   ├── reading-order.md            # OpenClaw 运行时阅读顺序
│   └── crosswalk.md                # docs/human/api ↔ skills/_shared 对照表
├── reports/                        # 生成型审计 / 验证报告（只读快照）
│   ├── security/
│   └── multi-user/
└── archive/                        # 已实施方案、已完成计划
    ├── multi-user/
    └── skills/

skills/                             # 【不搬迁】Gateway 权威 Skill 根
├── ...                             # SKILL.md、_shared 保持原位
└── (仅 SKILL_REFACTOR_PLAN 迁出至 archive)

# 仓库根（治理元文档）
PROJECT_DOCUMENT_INDEX.md           # 全项目文档入口
AGENT_DOCUMENTATION_RULES.md        # Cursor Agent 读取规则（非 OpenClaw）
DOCUMENTATION_AUDIT.md
DOCUMENTATION_MIGRATION_PLAN.md
```

### 2.2 各目录职责与存放规则

| 目录 | 职责 | 允许存放 | 禁止存放 |
|------|------|----------|----------|
| **`docs/human/`** | 人类工程师操作与开发指南 | 部署手册、架构说明、API 契约、活跃测试计划、功能设计 | 已完成迁移方案全文、审计评分明细、`SKILL.md` 正文、密钥/`.env` 示例 |
| **`docs/openclaw/`** | OpenClaw 运行时文档导航（非 Skill 正文） | 阅读顺序、权威对照表、指向 `skills/` 的索引 | 完整 Skill 副本、Cursor 开发规则 |
| **`docs/reports/`** | 时间点快照与审计产出 | 安全验证报告、加固计划终稿、带版本/日期的评估 | 未标注日期的「当前状态」表述、运维 checklist（应放 human） |
| **`docs/archive/`** | 已实施 / 已完成的历史文档 | 迁移计划、重构计划、废弃模板 README | 仍需每周更新的运维文档 |
| **`skills/`**（根目录） | **OpenClaw Gateway 运行时执行层** | `SKILL.md`、`_shared` 策略、Skill CHANGELOG/VERSIONS | Cursor 规则、人类长篇部署指南、审计报告 |
| **仓库根 `*.md` 治理文件** | 全项目入口；**Cursor Agent 规则** | `PROJECT_DOCUMENT_INDEX`、`AGENT_DOCUMENTATION_RULES`、审计/迁移计划 | OpenClaw 业务指令副本 |

### 2.3 权威源优先级（迁移后）

```
API 契约     → docs/human/api/openclaw-intake.md
报告 JSON    → skills/_shared/report-schema.md
鉴权/隔离    → skills/_shared/multi-user-auth.md（OpenClaw）+ docs/human/security/*（人类运维）
OpenClaw 执行 → skills/*/SKILL.md（不可由 docs 副本替代）
Cursor 开发  → docs/human/* + AGENT_DOCUMENTATION_RULES.md
安全快照     → docs/reports/security/*（只读，非操作依据）
```

---

## 3. 迁移映射表

### 3.1 `docs/` → `docs/human/`（人类活跃文档）

| 原路径 | ↓ | 目标路径 | 备注 |
|--------|---|----------|------|
| `docs/architecture.md` | ↓ | `docs/human/architecture/overview.md` | 系统架构权威 |
| `docs/deployment.md` | ↓ | `docs/human/deployment/local.md` | 本地开发 |
| `docs/server-deployment.md` | ↓ | `docs/human/deployment/production.md` | 生产部署 |
| `docs/openclaw-skills-deploy.md` | ↓ | `docs/human/deployment/openclaw-skills-gateway.md` | Gateway 挂载 |
| `docs/developer-guide.md` | ↓ | `docs/human/development/developer-guide.md` | 开发规范 |
| `docs/cross-platform-development.md` | ↓ | `docs/human/development/cross-platform.md` | Win/Ubuntu |
| `docs/portal-chat.md` | ↓ | `docs/human/features/portal-chat.md` | 门户对话实现 |
| `docs/android-app.md` | ↓ | `docs/human/mobile/android-app.md` | Capacitor APK |
| `docs/api/openclaw-intake.md` | ↓ | `docs/human/api/openclaw-intake.md` | API 契约权威 |
| `docs/security/GATEWAY_ISOLATION.md` | ↓ | `docs/human/security/gateway-isolation.md` | P0 运维必读 |
| `docs/multi-user/MULTI_USER_TEST_PLAN.md` | ↓ | `docs/human/testing/multi-user-test-plan.md` | 活跃测试清单 |

### 3.2 `docs/` → `docs/reports/`（生成型报告）

| 原路径 | ↓ | 目标路径 | 备注 |
|--------|---|----------|------|
| `docs/security/SECURITY_HARDENING_PLAN.md` | ↓ | `docs/reports/security/hardening-plan-2026-06-05.md` | 顶部加「快照」横幅 |
| `docs/security/SECURITY_VERIFICATION_REPORT.md` | ↓ | `docs/reports/security/verification-report-v5-2026-06-05.md` | pytest 45→102 已过时 |

### 3.3 `docs/` → `docs/archive/`（历史 / 已实施）

| 原路径 | ↓ | 目标路径 | 备注 |
|--------|---|----------|------|
| `docs/multi-user/MULTI_USER_MIGRATION_PLAN.md` | ↓ | `docs/archive/multi-user/migration-plan-2026-06-05.md` | 已实施；禁止 Agent 当待办 |

### 3.4 `skills/` → `docs/archive/`（已完成计划）

| 原路径 | ↓ | 目标路径 | 备注 |
|--------|---|----------|------|
| `skills/SKILL_REFACTOR_PLAN.md` | ↓ | `docs/archive/skills/skill-refactor-plan-2026-06-06.md` | 阶段 0–5 已完成 |

### 3.5 `skills/` — **保持原位**（仅登记，不迁移）

| 路径 | 处理 |
|------|------|
| `skills/README.md` | 保持 |
| `skills/VERSIONS.md` | 保持 |
| `skills/CHANGELOG.md` | 保持 |
| `skills/openclaw-*/SKILL.md`（8 个） | 保持 |
| `skills/_shared/*.md`（10 个） | 保持 |
| `skills/openclaw-conversational-assistant/references/api-quickref.md` | 保持 |
| `skills/openclaw-price-ingest-external/README.md` | 保持 |

### 3.6 仓库根与其他

| 原路径 | ↓ | 目标路径 | 备注 |
|--------|---|----------|------|
| `README.md` | ↓ | `README.md`（精简） | 保留根 README；文档地图改为链接 `PROJECT_DOCUMENT_INDEX.md` |
| — | ↓ | `docs/human/getting-started/quickstart.md` | **可选**：从 README 拆出「30 分钟快速启动」 |
| `PROJECT_DOCUMENT_INDEX.md` | ↓ | `PROJECT_DOCUMENT_INDEX.md` | 保持根目录（或 `docs/README.md` 二选一，建议根目录） |
| `AGENT_DOCUMENTATION_RULES.md` | ↓ | `AGENT_DOCUMENTATION_RULES.md` | 保持根目录（仅 Cursor）；`docs/openclaw/README.md` 为 OpenClaw 索引 |
| `frontend/README.md` | ↓ | `docs/archive/frontend/vite-template-readme.md` | Vite 官方模板，非项目文档 |
| `backups/README.md` | ↓ | `backups/README.md` | 保持（运维目录内说明） |
| `.github/workflows/ci.yml` | ↓ | — | 不迁移；在索引中登记 |

### 3.7 新建文件（迁移执行时创建）

| 目标路径 | 用途 |
|----------|------|
| `docs/openclaw/README.md` | OpenClaw 运行时文档入口，指向 `skills/` |
| `docs/openclaw/crosswalk.md` | `docs/human/api` ↔ `skills/_shared` 权威对照 |
| `docs/openclaw/reading-order.md` | OpenClaw 运行时阅读顺序（非 Cursor 规则） |
| `docs/human/README.md` | 人类文档分区索引 |
| `docs/reports/README.md` | 说明报告为快照、勿当运维手册 |
| `docs/archive/README.md` | 说明归档策略 |

---

## 4. 迁移后需更新的交叉引用（抽样）

执行 `git mv` 后须批量更新链接。高引用文件优先：

| 文件 | 需更新的链接模式 |
|------|------------------|
| `README.md` | 全部 `docs/*.md` 路径 |
| `skills/_shared/multi-user-auth.md` | `../../docs/multi-user/...` |
| `skills/_shared/ci-skill-regression.md` | `../../docs/multi-user/MULTI_USER_TEST_PLAN.md` |
| `skills/openclaw-conversational-assistant/SKILL.md` | `../../docs/...` |
| `docs/human/deployment/production.md` | 互链 `local.md`、`gateway-isolation.md` |
| 各 `SKILL.md` 内 `docs/api/openclaw-intake.md` | → `docs/human/api/openclaw-intake.md` |

**建议工具**：`rg 'docs/' --glob '*.md'` 全仓扫描后统一替换。

---

## 5. 原路径 Stub 策略（执行阶段二选一）

| 策略 | 做法 | 优点 |
|------|------|------|
| **A. 重定向 stub** | 原路径保留 10 行以内文件，仅含「已迁至 …」链接 | 外部书签、旧 Skill 链接不断裂 |
| **B. 纯移动** | 仅更新仓内链接，不保留 stub | 目录最干净 |

**推荐**：对 `docs/api/openclaw-intake.md`、`docs/security/GATEWAY_ISOLATION.md` 使用 **策略 A**（外部引用多）；对其余内部文档使用 **策略 B** 或短期 stub（1 个发布周期后删除）。

---

## 6. 执行检查清单（确认后执行）

- [x] 人工评审本计划并批准目标结构
- [x] 创建 `docs/human|`openclaw|`reports|`archive` 子目录
- [x] 按 §3 执行 `git mv` + 关键路径 stub（`docs/api/`、`docs/security/`、`skills/SKILL_REFACTOR_PLAN.md`）
- [x] 修复全仓 markdown 相对链接
- [x] 更新 `README.md` 指向 `PROJECT_DOCUMENT_INDEX.md`
- [x] 在归档/报告文件顶部添加状态横幅
- [x] 新建 `docs/human|openclaw|reports|archive` 索引 README
- [x] 运行 `pytest -q` 确认无回归
- [ ] 提交 PR（由维护者执行）

---

## 7. 明确不迁移项

| 路径 | 原因 |
|------|------|
| `skills/**/SKILL.md` | Gateway `extraDirs` 硬依赖 |
| `skills/_shared/**` | Skill 运行时相对路径引用 |
| `.env.example` | 非文档治理范围 |
| `scripts/**` | 脚本非文档（仅在索引中登记） |
| `tests/**` | 测试代码非文档 |

---

*迁移已于 2026-06-08 执行。旧路径 stub：`docs/api/openclaw-intake.md`、`docs/security/GATEWAY_ISOLATION.md`。*
