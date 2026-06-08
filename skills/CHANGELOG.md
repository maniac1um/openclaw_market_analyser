# OpenClaw Skills CHANGELOG

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。  
Skill 包版本与 `VERSIONS.md` 同步。

---

## [2.0.1] - 2026-06-06

### Changed

- **目录迁移**：Skill 包由 `.cursor/skills/` 迁至仓库根目录 **`skills/`**（权威路径）
- **Cursor 兼容**：`.cursor/skills` 改为指向 `skills/` 的符号链接
- 全部文档与 Skill 内 `docs/` 相对路径已对齐新结构

---

## [2.0.0] - 2026-06-06

### Added

- **部署文档**：`docs/human/deployment/openclaw-skills-gateway.md`（Gateway 挂载、API Key、更新与验证）

- **架构**：`SKILL_REFACTOR_PLAN.md` 多用户 SaaS Skill 重构计划
- **_shared**：`report-schema.md`、`ownership-policy.md`、`report-security.md`
- **_shared**：`agent-safety-baseline.md`、`portal-chat-routing.md`、`public-deploy-security.md`
- **_shared**：`quota-policy.md`、`workspace-api-roadmap.md`、`ci-skill-regression.md`
- **Skills**：`openclaw-user-workspace`、`openclaw-report-security`、`openclaw-audit-events`
- **conversational-assistant**：§10 Intent Routing、§11 默认调度流水线

### Changed

- 各业务 Skill §0 鉴权收敛至 `_shared/multi-user-auth.md`
- 报告 schema 收敛至 `_shared/report-schema.md`
- 发布流程统一经 `openclaw-report-security` 安全门
- `news-publisher-enhanced` §8.6 监测 API 改为交叉引用
- 安全准则收敛至 `agent-safety-baseline.md`
- `conversational-assistant` §5 API 速查精简，完整表见 `api-quickref.md`

### Deprecated

- 各 Skill 内重复的长篇鉴权表、报告字段表（请用 `_shared`）
- 包内共享 `whitelist.json` 作为多租户长期方案（见 `workspace-api-roadmap.md`）

---

## [1.0.0] - 2026-06 前

- 初始 Skill 集：conversational-assistant、news-publisher-enhanced、price-ingest-external、price-analysis-reporting、public-news-library
- `_shared/multi-user-auth.md` 多用户鉴权约定
