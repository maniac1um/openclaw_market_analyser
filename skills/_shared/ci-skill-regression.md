# Skill 架构 CI 回归（OpenClaw Skills 共用）

**目的**：将多用户隔离与 Skill 文档假设纳入 CI / 发布前检查。  
**范围**：引用仓库现有 pytest；**不** 新增业务代码（除非仓库已有测试需文档对齐）。

---

## 1. 必跑命令

```bash
cd /path/to/openclaw_news_publisher
pytest -q tests/api/test_multi_user_auth.py \
          tests/api/test_multi_user_isolation.py \
          tests/api/test_multi_user_idor.py \
          tests/api/test_multi_user_openclaw_key.py \
          tests/api/test_security_high.py \
          tests/api/test_security_critical.py
```

全量：

```bash
pytest -q
```

**门禁**：上述 multi-user + security 用例全绿方可发布 Skill 包 v2.0 到生产。

---

## 2. A/B Key 交叉访问矩阵（Skill 假设）

与 [`docs/human/testing/multi-user-test-plan.md`](../../docs/human/testing/multi-user-test-plan.md) 对齐：

| ID | 场景 | 预期 | 测试文件 |
|----|------|------|----------|
| **SK-ISO-01** | user_a Key → `GET /public/reports` | 仅 a 的数据 | `test_multi_user_isolation.py` |
| **SK-ISO-02** | user_a Key → user_b `ingest_id` 详情 | **404** | `test_multi_user_idor.py` |
| **SK-ISO-03** | user_a Key → user_b `monitor_id` timeseries | **404** | `test_multi_user_idor.py` |
| **SK-ISO-04** | user_a Key ingest → b_monitor | **404** | `test_multi_user_openclaw_key.py` |
| **SK-ISO-05** | user_a Key `POST /openclaw/reports` | 202；归属 a | `test_multi_user_openclaw_key.py` |
| **SK-ISO-06** | 无 Key `GET /public/reports` | **401** | `test_multi_user_openclaw_key.py` |
| **SK-SEC-01** | `javascript:` URL 入站 | schema 拒绝 | `test_security_high.py` |
| **SK-SEC-02** | bulk-delete 非 UUID | **422** | `test_security_high.py` |
| **SK-SEC-03** | Rate limit 超限 | **429** | `test_security_high.py` |

**Skill 文档要求**：Agent 不得假设跨用户 403；须与 **404** 语义一致（`ownership-policy.md`）。

---

## 3. Fixture 约定

见 `tests/api/conftest.py`：

- `admin_user`, `user_a`, `user_b`
- `api_headers` / per-user `X-Api-Key`
- `OPENCLAW_LEGACY_API_KEY_ENABLED=false`（默认）

Skill curl 示例在 CI 手测清单中使用 **user_a** 的 Key，**禁止**硬编码生产 Key。

---

## 4. 发布前 Skill 检查清单（人工）

```text
[ ] CHANGELOG.md 已更新版本
[ ] 各 SKILL.md skill_version 与 CHANGELOG 一致
[ ] conversational-assistant §10/§11 与专项 Skill 委派无矛盾
[ ] report-security 门控在 news-publisher / price-analysis 文档中仍被引用
[ ] pytest multi-user 全绿
[ ] Legacy Key 生产环境关闭
[ ] Skill curl 在 staging 用 per-user Key 抽测（MULTI_USER_TEST_PLAN §13）
```

---

## 5. 与门户 E2E

手动清单见 `MULTI_USER_TEST_PLAN.md` §10（FE-01～FE-07）。Skill 层不替代 E2E，但须与门户只读/写分流一致（`portal-chat-routing.md`）。

---

## 相关文档

- [`../CHANGELOG.md`](../CHANGELOG.md)
- [`../VERSIONS.md`](../VERSIONS.md)
- [`ownership-policy.md`](ownership-policy.md)
- [`public-deploy-security.md`](public-deploy-security.md)
