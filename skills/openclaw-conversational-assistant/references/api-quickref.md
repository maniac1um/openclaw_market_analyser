# API 速查（对话式助手）

前缀：`{BASE_URL}/api/v1`。读接口在 multi-user 模式下须带 `X-Api-Key: ${API_KEY}` 或 Bearer。

## 监测与价格

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/openclaw/monitoring/bootstrap` | 创建监测任务 |
| POST | `/openclaw/monitoring/{id}/observations/ingest` | 外采价格入库 |
| GET | `/openclaw/monitoring/{id}/summary` | 窗口统计 |
| GET | `/public/monitoring/monitors` | 当前用户监测列表 |
| GET | `/public/monitoring/{id}/timeseries` | 日聚合趋势 |
| GET | `/public/monitoring/{id}/observations` | 观测明细 |
| POST | `/openclaw/monitoring/external-heartbeat` | 外采心跳 |

## 报告与分析

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/openclaw/reports` | 提交报告 JSON |
| GET | `/openclaw/reports/{ingest_id}` | 入站状态 |
| GET | `/public/reports` | 报告列表 |
| GET | `/public/reports/{ingest_id}` | 报告详情 |
| POST | `/openclaw/analysis/news-trigger` | 新闻+价格联合分析 |

## 新闻库

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/openclaw/news/library` | 入库 |
| GET | `/openclaw/news/library` | 查询（Key） |
| GET | `/public/news/library` | 查询（scoped） |

## 工作流（门户 / Agent）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/public/workflow/state` | 总览 |
| GET | `/public/workflow/external-configs` | 定时任务列表 |
| POST | `/public/workflow/external-configs` | 保存定时任务 |
| POST | `/public/workflow/external-configs/{job}/toggle` | 启停 |
| POST | `/public/workflow/monitor/bootstrap` | 门户创建监测 |
| POST | `/public/workflow/analysis/run` | 门户触发分析 |

## 账户（仅门户 UI，Agent 不代操作）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/public/auth/api-keys` | 生成 Key（JWT） |
| GET | `/public/auth/api-keys` | 列出 Key 前缀 |
| DELETE | `/public/auth/api-keys/{id}` | 撤销 |

## 健康检查

| 方法 | 路径 | 鉴权 |
|------|------|------|
| GET | `/healthz` | 无 |
| GET | `/healthz/db` | 无 |
