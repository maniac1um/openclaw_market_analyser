# 已知问题

> 技术债跟踪；backlog 优先级见 [roadmap.md](../00-overview/roadmap.md)。

## 做什么

列出当前代码/架构已知缺陷，避免重复踩坑或误把历史当待办。

## 关键组件

| ID | 问题 | 严重度 |
|----|------|--------|
| KI-001 | `news_analysis_service` 逆依赖 `intake_service` | 中 |
| KI-003 | monitoring/news API IDOR 风险 | **高** |
| KI-004 | `chat_run_store` 纯内存，重启丢 run | 中 |
| KI-005 | 无 Alembic，靠 `scripts/migrations/` | 中 |
| KI-006 | audit-events API 预埋未全实现 | 低 |
| KI-007 | 裸机 DB 初始化步骤分散 | 中 |

## 数据流（问题 → 修复）

```
发现 bug → 记入本表 → roadmap 排优先级 → PR 修复 → 移入「已关闭」
```

## 示例

| 我要改 chat 持久化 | |
|--------------------|--|
| 读 | KI-004 + [system-design](../02-backend/system-design.md) |
| 勿依赖 | 纯 localStorage 作唯一真相 |

| 我要动 monitoring API | 先确认 KI-003 归属校验 |

**已关闭**：docs 结构混乱 KI-DOC-004（2026-06-17）

```bash
pytest -q   # 获取当前测试数量，勿信文档硬编码数字
```
