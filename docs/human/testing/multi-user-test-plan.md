# 多用户 SaaS 测试计划

**项目**：OpenClaw News Publisher  
**文档版本**：1.1  
**生成日期**：2026-06-05  
**关联**：[migration-plan-2026-06-05.md](../../archive/multi-user/migration-plan-2026-06-05.md)（归档，已实施）

---

## 1. 测试目标

验证多用户迁移后：

- 注册、登录、退出、Token 生命周期正确
- USER / ADMIN 权限边界清晰
- 数据按 `user_id` 隔离，无 IDOR
- OpenClaw per-user API Key 与 **public 读方案 B** 兼容
- 现有 security 回归不破坏

---

## 2. 测试环境

| 项 | 要求 |
|----|------|
| Python | 3.11+，`pytest`, `httpx` |
| 数据库 | 三库 PostgreSQL（或 testcontainers） |
| 配置 | `OPENCLAW_LEGACY_API_KEY_ENABLED=false`（默认）；过渡期用例可显式 `monkeypatch` 为 `true` |
| 用户 | 至少 bootstrap ADMIN + 两个 USER 测试账号 |
| OpenClaw | 每用户独立 API Key（测试 fixture 生成） |

**Fixture 建议**（`tests/conftest.py` 扩展）：

- `admin_user`, `user_a`, `user_b` — 含 password、JWT、api_key
- `auth_headers(user)` — Bearer JWT
- `api_key_headers(user)` — `X-Api-Key`
- `client` — FastAPI TestClient

---

## 3. 认证流程测试

### 3.1 注册

| ID | 用例 | 预期 |
|----|------|------|
| REG-01 | 合法 email/username/password | 201；users 表有记录；password 为 argon2 hash |
| REG-02 | 重复 email | 409 |
| REG-03 | 重复 username | 409 |
| REG-04 | 弱密码（<8 或缺复杂度） | 422 |
| REG-05 | 非法 email 格式 | 422 |
| REG-06 | `OPENCLAW_ALLOW_REGISTRATION=false` | 403 |
| REG-07 | 首用户 + `FIRST_USER_IS_ADMIN=true` | role=ADMIN |

### 3.2 登录

| ID | 用例 | 预期 |
|----|------|------|
| LOG-01 | 正确 email/password | 200；`access_token`；Set-Cookie refresh；`last_login_at` 更新 |
| LOG-02 | 错误密码 | 401；统一文案；不泄露用户是否存在 |
| LOG-03 | suspended 用户 | 403 |
| LOG-04 | 5 次失败 | 429 限速 |
| LOG-05 | 限速窗口后恢复 | 200 |

### 3.3 退出与 Token

| ID | 用例 | 预期 |
|----|------|------|
| TOK-01 | logout | refresh cookie 清除；session revoked |
| TOK-02 | access 过期 + 有效 refresh | `/auth/refresh` 200；新 access |
| TOK-03 | refresh 过期 | 401；需重新登录 |
| TOK-04 | `/auth/me` 带有效 JWT | 返回 user 信息（无 password_hash） |
| TOK-05 | 无凭证访问 `/auth/me` | 401 |

---

## 4. 权限控制测试

| ID | 用例 | 角色 | 预期 |
|----|------|------|------|
| RBAC-01 | 读自己的 reports 列表 | USER | 200；仅自己的 |
| RBAC-02 | 读全部 reports 列表 | ADMIN | 200；含所有 user |
| RBAC-03 | USER 访问 admin-only 端点（未来） | USER | 403 |
| RBAC-04 | bulk-delete 他人 ingest_id | USER | 404 或 0 deleted |
| RBAC-05 | ADMIN bulk-delete 任意 ingest_id | ADMIN | 200 |

---

## 5. 数据隔离测试

| ID | 用例 | 预期 |
|----|------|------|
| ISO-01 | user_a JWT 列 reports | 无 user_b 记录 |
| ISO-02 | user_a JWT 列 news_library | 无 user_b 记录 |
| ISO-03 | user_a JWT 列 monitors | 无 user_b monitor_id |
| ISO-04 | user_a Key ingest 报告 | reports.user_id = user_a |
| ISO-05 | user_a Key bootstrap monitor | price_monitors.user_id = user_a |
| ISO-06 | user_a Key POST news/library | news_library.user_id = user_a |
| ISO-07 | 联合分析 monitor 属于 user_b | user_a Key 触发 → 404/403 |
| ISO-08 | 并发：A/B 同时 ingest | 互不串 ingest_id 归属 |

---

## 6. IDOR 测试

| ID | 用例 | 预期 |
|----|------|------|
| IDOR-01 | user_a 读 user_b 的 `ingest_id` detail | 404 |
| IDOR-02 | user_a 删 user_b 的 ingest_id bulk | 不删除 |
| IDOR-03 | user_a 读 user_b 的 monitor timeseries | 404 |
| IDOR-04 | user_a 读 user_b 的 news_library id | 404 |
| IDOR-05 | 猜测随机 UUID | 404（非 403） |
| IDOR-06 | user_a Key ingest 到 user_b 已有 monitor_id | 404 |

---

## 7. OpenClaw API Key 测试

| ID | 用例 | 预期 |
|----|------|------|
| OC-01 | user_a Key POST /openclaw/reports | 202；user_id=user_a |
| OC-02 | user_b Key GET /openclaw/reports/{a_ingest} | 404 |
| OC-03 | 无效 Key | 401 |
| OC-04 | revoked Key | 401 |
| OC-05 | user_a Key POST observations/ingest 到 a_monitor | 200 |
| OC-06 | user_a Key POST observations/ingest 到 b_monitor | 404 |
| OC-07 | 门户 POST /auth/api-keys | 返回 key 一次；DB 存 hash |
| OC-08 | Legacy global Key（enabled） | 映射 ADMIN；全量读写 |

---

## 8. Public 读接口方案 B 测试

| ID | 用例 | 凭证 | 预期 |
|----|------|------|------|
| PUB-01 | GET /public/reports | 无 | 401 |
| PUB-02 | GET /public/reports | user_a JWT | 仅 a 的数据 |
| PUB-03 | GET /public/monitoring/{a_monitor}/timeseries | user_a API Key | 200 |
| PUB-04 | GET /public/monitoring/{b_monitor}/timeseries | user_a API Key | 404 |
| PUB-05 | GET /public/news/library | user_a API Key + keyword | 仅 a 的新闻 |
| PUB-06 | GET /public/reports | Legacy global Key | ADMIN 全量 |
| PUB-07 | Skill 典型 curl（带 Key 读 timeseries + ingest） | user_a Key | 端到端通过 |

---

## 9. WebSocket 测试

| ID | 用例 | 预期 |
|----|------|------|
| WS-01 | 无 JWT/Cookie 连接 | close 1008 Unauthorized |
| WS-02 | 登录用户 Cookie 连接 | accept |
| WS-03 | user_a 会话 | 正常 user_message 流 |

---

## 10. 前端测试（手动 / E2E 清单）

| ID | 用例 | 预期 |
|----|------|------|
| FE-01 | 未登录访问 /reports | redirect /login |
| FE-02 | 注册 → 登录 → 见 nav | 正常 |
| FE-03 | 用户菜单显示 username | 正确 |
| FE-04 | logout | 清 session；redirect login |
| FE-05 | access 过期 silent refresh | 无感或一次 refresh |
| FE-06 | 生成 API Key UI | 展示一次；可复制 |
| FE-07 | 设计风格 | 无廉价 admin 模板；沿用 CSS 变量 |

---

## 11. 回归测试

| 项 | 要求 |
|----|------|
| 现有 security tests | 全绿；改用 `tests/api/conftest.py` 的 per-user Key fixture |
| healthz | 仍公开 |
| Rate limit | 仍生效 |
| SSRF / path safety | 不回归 |

**新测试文件**（已实现）：

```
tests/api/conftest.py                   # admin_user / user_a / user_b / api_headers
tests/api/test_multi_user_auth.py       # REG, LOG, TOK, Legacy 开关
tests/api/test_multi_user_isolation.py  # ISO, RBAC（含 PostgreSQL）
tests/api/test_multi_user_idor.py       # IDOR（含 PostgreSQL）
tests/api/test_multi_user_openclaw_key.py # OC, PUB
tests/test_prompt_safety.py             # 对话违规词过滤
```

**Skill 架构 CI 映射**：见 [`skills/_shared/ci-skill-regression.md`](../../../skills/_shared/ci-skill-regression.md)（SK-ISO-* / SK-SEC-* 与上表用例对应）。

当前：`pytest -q` → **85 passed**（含 security 回归，Legacy Key 默认关闭）。

---

## 12. 并发测试

| ID | 用例 | 预期 |
|----|------|------|
| CON-01 | 10 线程 user_a + 10 线程 user_b 同时 list reports | 无交叉数据 |
| CON-02 | 同时 register 相同 email | 仅一个 201，其余 409 |
| CON-03 | 同时 login 同一用户 | 多个有效 session（或按设计单 session） |

---

## 13. 验收标准

- [x] pytest multi-user suite 全绿（`tests/api/test_multi_user_*.py` + security 回归）
- [x] Legacy Key 默认关闭（`OPENCLAW_LEGACY_API_KEY_ENABLED=false`）
- [x] 安全测试改用 per-user API Key fixture（`tests/api/conftest.py`）
- [ ] Skill curl 示例在部署环境手动验证（带 per-user Key）
- [ ] 前端 E2E 清单（§10）手动验收

---

## 14. 不在本阶段范围

- OAuth / SSO 集成测试
- MODERATOR 角色
- 共享 OpenClaw 多租户 Agent 测试
- 性能压测（可后续补充）
