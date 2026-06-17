# 文档

> 人类文档入口 → [00-overview/README.md](00-overview/README.md) · Cursor Agent → [_agent/documentation-rules.md](_agent/documentation-rules.md)

## 做什么

本目录是 OpenClaw News Publisher 的**人类可读**工程文档。OpenClaw 运行时 Skill 在仓库根 `skills/`。

## 关键组件

| 目录 | 内容 |
|------|------|
| `00-overview/` | 5 分钟懂项目 |
| `01-getting-started/` | 部署 |
| `02-backend/` | API、设计、安全 |
| `03-frontend/` | UI、Android |
| `04-product/` | 对话、计费 |
| `05-dev/` | 开发、测试 |
| `_agent/` | Cursor / OpenClaw Agent 规则 |

## 数据流（5 分钟 onboarding）

```
project-map.md → architecture.md → local-dev.md → developer-guide.md
```

| 角色 | 路径 |
|------|------|
| 新开发者 | [00-overview/project-map.md](00-overview/project-map.md) |
| 运维 | [01-getting-started/getting-started.md](01-getting-started/getting-started.md) |
| 后端 | [02-backend/api.md](02-backend/api.md) |

## 示例

```bash
# 本地跑起来
uvicorn app.main:app --reload --port 8000   # 终端 1
cd frontend && npm run dev                   # 终端 2 → :5173
```
