# Token 计费

> 余额制：操作扣 Token，充值/订阅发放 Token；实现 `app/services/token_service.py`。

## 做什么

统一管控 AI 对话、工作流分析、Agent 分析与报告入站的 Token 消耗与余额。

## 关键组件

| 概念 | 说明 |
|------|------|
| 余额 | `total_grants - total_usage` |
| 固定扣费 | 工作流 / Agent / 报告按操作类型 |
| 动态扣费 | 聊天按输入+输出文本估算 |
| 表 | `token_usage`、`token_grants`、`payments`、`subscriptions` |

| 操作 | 默认 Token | 环境变量 |
|------|-------------|----------|
| 工作流分析 | 500 | `OPENCLAW_TOKEN_WORKFLOW_COST` |
| Agent 分析 | 500 | `OPENCLAW_TOKEN_AGENT_COST` |
| 报告入站 | 300 | `OPENCLAW_TOKEN_REPORT_COST` |
| 聊天 | 动态 | + 预检 reserve 512 |

| 订阅 | 月发放 |
|------|--------|
| free | 5,000 |
| pro | 100,000 |

ADMIN 角色跳过扣费（开发便利）。

## 数据流

```
请求 → TokenService 预检余额 → 执行业务 → 写 token_usage
充值/订阅 → token_grants → 余额增加
低余额 → notification_service → token_low 通知
```

```
POST /payments → pending → simulate-success → completed → balance ↑
SubscriptionGrantScheduler (UTC 0点) → 到期用户 → grant → period +30d
```

## 示例

```bash
# 查余额
curl http://localhost:8000/api/v1/public/users/balance \
  -H "Authorization: Bearer $JWT"

# 模拟充值
curl -X POST http://localhost:8000/api/v1/public/payments \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"tokens": 1000}'
# → POST .../payments/{id}/simulate-success
```

余额不足 → **402**；超速 → **429**（默认 10 次/分，5000 Token/分）。

| API 详情 | [../02-backend/api.md](../02-backend/api.md) |
