# 架构决策（ADR）

> 重大设计选择的简短记录；新增决策在表末追加一行。

## 做什么

记录「为什么这样设计」，避免重复讨论已定论的架构选择。

## 关键组件

| ID | 决策 | 状态 |
|----|------|------|
| ADR-001 | 后端目录 `app/`，不用 `backend/` | 已接受 |
| ADR-002 | PostgreSQL 三库分离 | 已接受 |
| ADR-003 | Skill 权威路径 `skills/` + Gateway `extraDirs` | 已接受 |
| ADR-004 | 文档分层 `00-overview`…`_agent` | 已接受 |
| ADR-005 | Legacy 全局 API Key 默认关闭 | 已接受 |
| ADR-006 | `00-overview/` 为 onboarding 入口 | 已接受 |
| ADR-008 | Token 统一经 `TokenService` 计费 | 已接受 |

## 数据流（ADR 生命周期）

```
讨论 → 表内追加 ADR-NNN → 关联 roadmap/known-issues → 代码落地
```

## 示例

**ADR-001 后果**：口头说「后端」= `app/`，文档与 import 均用 `app`。

**ADR-004 后果**：人类读 `docs/00-overview`…`05-dev`；Cursor 读 `_agent/`；Skill 正文在 `skills/`。

新增 ADR 模板：

```markdown
| ADR-009 | <一句话决策> | 待定 |
```

背景 / 决策 / 后果各写 1–2 句即可。
