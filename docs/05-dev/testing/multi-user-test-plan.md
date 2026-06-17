# 多用户测试计划

> 验证 JWT、per-user Key、数据隔离与 Gateway 权限边界。

## 做什么

定义多用户 SaaS 迁移后的测试范围、fixture 约定与关键用例矩阵。

## 关键组件

| 目标 | 验证点 |
|------|--------|
| 认证 | 注册/登录/Refresh/Logout |
| 隔离 | USER 不可见他人 `ingest_id` / `monitor_id` |
| Agent | per-user Key 仅访问本用户资源 |
| 权限 | USER ≠ ADMIN Gateway 能力 |
| 回归 | Legacy Key 关闭下现有用例仍绿 |

| 环境 | 要求 |
|------|------|
| Python | 3.11+，`pytest`，`httpx` |
| DB | 三库 PostgreSQL |
| 配置 | `OPENCLAW_LEGACY_API_KEY_ENABLED=false` |

| Fixture | 用途 |
|---------|------|
| `admin_user`, `user_a`, `user_b` | 含 JWT + api_key |
| `auth_headers(user)` | Bearer |
| `api_key_headers(user)` | `X-Api-Key` |

## 数据流

```
conftest 建用户 → A Key 访问 A 资源 ✓
              → A Key 访问 B 资源 → 404
              → 无 Key public GET → 401
```

## 示例

```bash
pytest tests/api/test_multi_user_*.py -v
pytest tests/api/test_gateway_security.py -v
pytest tests/api/test_billing.py -v
```

| 用例 ID | 场景 | 预期 |
|---------|------|------|
| SK-ISO-05 | user_a Key POST reports | 202，归属 a |
| — | user_a Key GET user_b report | 404 |

完整矩阵见 `tests/api/` 与 `skills/_shared/ci-skill-regression.md`。

| 鉴权契约 | [../02-backend/api.md](../02-backend/api.md) |
