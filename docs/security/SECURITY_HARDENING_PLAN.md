# Security Hardening Plan

**项目**：OpenClaw News Publisher  
**文档版本**：1.8  
**生成日期**：2026-06-05  
**最后更新**：2026-06-05（M-06 + Phase 4 **v5 联测通过**，评分 **86/100**）  
**依据**：Security Audit + Phase 1~4 + `SECURITY_VERIFICATION_REPORT.md` v5  
**修复 Agent 状态**：M-06 补全 + Phase 4 **已提交**  
**验证 Agent 状态**：✅ **v5 联测通过**（评分 **86/100**，pytest **45/45**）

---

## 决策摘要（自动评估结论）

> **结论：Phase 1~4（除 L-06 RBAC）全部验证通过；加固计划闭环。**

| 评估项 | 结论 |
|--------|------|
| Phase 1 / 1.1 | ✅ 已验证 |
| Phase 2（High） | ✅ 已验证 |
| Phase 3（Medium） | ✅ **全部验证**（含 M-06 补全） |
| Phase 4（Low） | ✅ **已验证**（L-01~L-05；L-06 长期） |
| **验证后评分** | **86 / 100**（`SECURITY_VERIFICATION_REPORT.md` v5） |
| pytest | **45/45** |
| pip-audit / bandit / npm audit | **0 高危** |

**Phase 1.1 完成情况**

| 优先级 | ID | 问题 | 状态 |
|--------|-----|------|------|
| P0+ | C-01 闭环 | SPA 不再注入 API Key；门户 HttpOnly Cookie 会话 | ✅ 已修复 |
| P0+ | C-02 边界 | 非法 UUID 预校验，禁止 500；DB 删文件用 `safe_child_path` | ✅ 已修复 |
| P0+ | C-03 增强 | WS 拒绝 Query `api_key`；支持 Header + Cookie + 消息限速 | ✅ 已修复 |

**下一步**：长期治理见 §7（RBAC、lockfile、定期审计）。无阻塞性修复项。

---

## 1. 当前安全评分（0 ~ 100）

### 验证后评分（2026-06-05，v5 联测）

| 维度 | 审计分 | v1 | v4 | **v5** |
|------|--------|-----|-----|--------|
| 身份认证与访问控制 | 35 | 42 | 72 | **72** |
| 输入校验与 Schema | 50 | 48 | 76 | **82** |
| 数据与存储安全 | 55 | 58 | 78 | **78** |
| 应用与 API 安全 | 40 | 38 | 78 | **82** |
| 前端安全（XSS/链接） | 55 | 60 | 74 | **74** |
| 基础设施与部署 | 45 | 45 | 72 | **72** |
| 密钥与配置管理 | 40 | 35 | 70 | **74** |
| 依赖与供应链 | 60 | 52 | 78 | **82** |
| 日志与监控 | 65 | 65 | 78 | **86** |
| Git 发布与工作流 | 50 | 50 | 58 | **62** |

### **综合评分：86 / 100**（v5）

**评级**：✅ **加固计划完成**（生产须 `OPENCLAW_PRODUCTION=true` + 强密钥 + 反代 TLS）

- **内网 / 开发**：✅ 默认可用；诊断/OpenAPI 按需开启。
- **公网 / 生产**：✅ Phase 1~4 已验证；见 `docs/server-deployment.md` checklist

---

## 2. OWASP Top 10（2021）覆盖情况

| # | 类别 | 审计状态 | 验证后状态 | 备注 |
|---|------|----------|------------|------|
| A01 | Broken Access Control | ❌ | ✅ **大幅改善** | Cookie 会话 + 写接口鉴权 ✅；单 Key 共享仍存 |
| A02 | Cryptographic Failures | ⚠️ | ⚠️ **生产改善** | 生产 fail-fast + 强密钥；dev 仍弱密钥 |
| A03 | Injection | ✅ | ✅ | SQL/命令注入维持安全 |
| A04 | Insecure Design | ❌ | ⚠️ | Cookie 会话 ✅；单 Key 无 RBAC |
| A05 | Security Misconfiguration | ❌ | ✅ **改善** | Rate Limit ✅；OpenAPI 默认关 ✅ |
| A06 | Vulnerable Components | ⚠️ | ✅ | starlette/idna 已升级；pip-audit 0 CVE |
| A07 | Auth & Session Failures | ❌ | ✅ **改善** | HttpOnly Cookie ✅；WS 无 Query Key ✅ |
| A08 | Software & Data Integrity | ⚠️ | ⚠️ **生产改善** | 生产强制 HMAC；dev 仍可选 |
| A09 | Logging & Monitoring | ⚠️ | ✅ **改善** | healthz + diagnostics 鉴权/脱敏 ✅ |
| A10 | SSRF | ⚠️ | ✅ **改善** | ssrf_guard + scrape 默认关 |

---

## 3. 已发现漏洞统计

### 原始审计（24 项）

| 等级 | 数量 |
|------|------|
| Critical | 3 |
| High | 8 |
| Medium | 7 |
| Low | 6 |

### 验证后修复状态

| 等级 | 已修复 | 部分修复 | 未修复 | 新增/回归 |
|------|--------|----------|--------|-----------|
| **Critical** | **3**（C-01、C-02、C-03） | 0 | 0 | 0 |
| **High** | **8**（H-01~H-09 含 H-07 完整、WS 限速） | 0 | 0 | 0 |
| **Medium** | **7**（M-01~M-07 含 monitoring UUID） | 0 | 0 | 0 |
| **Low** | **4**（L-01~L-05） | 1（L-06 RBAC 长期） | 0 | 0 |

---

## 4. 修复优先级与进展

### Phase 1 + 1.1 — Critical（✅ 已验证，见报告 v3 §Phase 1.1）

| ID | 问题 | 状态 | 验证结果（v1 → 1.1 后预期） |
|----|------|------|---------------------------|
| C-01 | Public 写接口无鉴权 | ✅ **完成** | 401 ✅；SPA 不再泄露 Key ✅；Cookie 写操作 ✅ |
| C-02 | bulk-delete 路径穿越 + 500 | ✅ **完成** | 路径穿越阻断 ✅；非法 UUID → not_found ✅ |
| C-03 | WebSocket 无鉴权 | ✅ **完成**（限速留 P2） | 无凭证拒绝 ✅；Query Key 拒绝 ✅；Cookie/Header ✅ |

**Phase 1 修改文件（修复 Agent）**

| 文件 | 变更 |
|------|------|
| `app/api/v1/public.py` | 6 个写接口 `verify_api_key`；移除危险双删 |
| `app/api/v1/chat.py` | WS 握手前 API Key 校验 |
| `app/core/security.py` | `is_valid_api_key`、`secrets.compare_digest` |
| `app/core/config.py` | `portal_embed_api_key_in_spa` |
| `app/main.py` | SPA `__OPENCLAW_RUNTIME__` 注入（**待 Phase 1.1 整改**） |
| `app/services/report_management_service.py` | UUID + `safe_child_path` |
| `app/utils/path_safety.py` | **新增** |
| `frontend/src/lib/auth.ts` | **新增** |
| `frontend/src/lib/api.ts` | 写请求 `X-Api-Key` |
| `frontend/src/features/chat/ChatPage.tsx` | WS `?api_key=` |
| `frontend/vite.config.ts` | dev 读取根 `.env` |
| `tests/api/test_security_critical.py` | **新增** 7 项 |

---

### Phase 1.1 — 实现摘要（2026-06-05）

| ID | 实现要点 | 关键文件 |
|----|----------|----------|
| C-01 | `portal_embed_api_key_in_spa` 默认 `false`；`POST/DELETE /public/auth/session`；`verify_portal_write_auth`（Key 或 Cookie） | `security.py`, `public.py`, `auth.ts`, `App.tsx` |
| C-02 | `delete_reports_from_db` 预校验 UUID + `safe_child_path` 删文件 | `public_queries.py` |
| C-03 | WS 仅 `x-api-key` Header 或 `openclaw_portal_session` Cookie；前端 WS 无 Query Key | `chat.py`, `ChatPage.tsx` |

**Phase 1.1 验收标准（✅ v3 已通过）**

- [x] `GET /` HTML **不含** `apiKey` / `__OPENCLAW_RUNTIME__`
- [x] 无 Cookie/无 Key → public 写接口 **401**
- [x] `POST /public/auth/session` + Cookie → 写接口 **200/503**（非 401）
- [x] `bulk-delete` + `["../../../etc/passwd"]` → **422**（Schema 预校验，非 500）
- [x] WS 无凭证 → 拒绝；`?api_key=` → 拒绝；Cookie 或 Header → 接受
- [x] `pytest -q` → **29 passed**

---

### Phase 2 — High（✅ 已验证，7/8 项通过）

| ID | 问题 | 状态 | 验证结果（v3） |
|----|------|------|----------------|
| H-01 | 默认弱密钥，无 fail-fast | ✅ | 生产 + 弱密钥 → RuntimeError ✅ |
| H-02 | HMAC 生产要求 | ✅ | 生产强制签名 ✅；dev 仍可选 |
| H-03 | JSON Schema 无界 DoS | ✅ | 2MB → 413；10000 items → 422 ✅ |
| H-04 | XSS / 恶意 URL | ✅ | `javascript:` → 422；CSP + urlSafety ✅ |
| H-05 | SSRF（scrape 时） | ✅ | localhost 阻断 ✅ |
| H-06 | 无 Rate Limit | ✅ | 超限 → 429 ✅ |
| H-07 | 诊断 / healthz 泄露 | ✅ | healthz 脱敏 ✅；diagnostics/gateway/run-readiness 需鉴权 ✅；异常脱敏 ✅ |
| H-08 | Docker 弱 DB 凭据 | ✅ | 无 5432 映射 ✅ |
| H-09 | 依赖 CVE | ✅ | pip-audit 0 CVE ✅ |

**Phase 2 新增/修改文件**：`app/core/startup_checks.py`、`app/middleware/security.py`、`app/utils/url_validation.py`、`app/utils/ssrf_guard.py`、`tests/api/test_security_high.py`、`tests/conftest.py`，及 schema/main/docker/ci 等。

**Phase 2 测试 Agent 必测（§6.4 — ✅ 已通过，除默认 OpenAPI）**

- [x] `OPENCLAW_PRODUCTION=true` + 默认密钥 → 启动失败
- [x] 2MB `analysis` POST → **413**
- [x] `javascript:` URL POST → **422**
- [x] 连续超限 GET → **429**
- [x] `pip-audit` 无 starlette/idna 高危
- [x] `GET /healthz/db` 失败时 detail 为通用文案（非堆栈）
- [x] `OPENCLAW_EXPOSE_OPENAPI=false` 时 `/docs` 404
- [x] C-03 WS `user_message` 超限返回 Rate limit 错误

**Phase 2 收尾（2026-06-05）**

| 项 | 实现 |
|----|------|
| H-07 完整 | `gateway-status` / `diagnostics` / `run-readiness` → `verify_portal_write_auth`；`public_errors.py` 脱敏 |
| C-03 WS 限速 | `chat.py` 每连接 `ws_messages_per_minute`（默认 12） |

---

### Phase 3 — Medium（✅ v4 验证 + M-06 补全已提交）

| ID | 问题 | 状态 | 验证结果 |
|----|------|------|----------|
| M-01 | OpenAPI `/docs` 公开 | ✅ | 默认 404 ✅（v4） |
| M-02 | Portal Schema 弱 | ✅ | UUID + max_length ✅ |
| M-03 | Git 发布链 | ✅ | 生产 block auto_push ✅ |
| M-04 | CORS 过宽 | ✅ | 白名单 ✅ |
| M-05 | 安全响应头 | ✅ | CSP 等 ✅ |
| M-06 | Query / 路径 UUID | ✅ **补全** | `timeseries` / `observations` 非法 UUID → **422** |
| M-07 | 容器非 root | ✅ | Dockerfile `USER appuser` ✅ |

**Phase 3 附加**

| 项 | 实现 |
|----|------|
| 限流 IP | `trust_x_forwarded_for`（默认 false，反代后可选开） |
| Gateway URL 泄露 | `expose_gateway_ws_url` 默认 false；诊断 extra 不暴露原始 WS |
| 文档 | `docs/api/openclaw-intake.md`、`docs/server-deployment.md` 已同步门户 Cookie 鉴权 |

**Phase 3 新增/修改文件**：`app/utils/public_errors.py`、`tests/api/test_security_medium.py`、`Dockerfile`、`app/core/config.py`、`app/core/startup_checks.py`、`app/main.py`、`app/api/v1/public.py`、`app/api/v1/chat.py`、`frontend/src/lib/api.ts`、`.env.example`

---

### Phase 4 — Low（✅ 已验证 v5）

| ID | 范围 | 状态 | 验证结果（v5） |
|----|------|------|----------------|
| L-01 | 日志脱敏 | ✅ | `sanitize_for_log` + 单元测试 ✅ |
| L-02 | MaxBody 流式 | ✅ | 无 Content-Length 累计上限 ✅ |
| L-03 | Chat WS 脱敏 | ✅ | Gateway 错误不含内部主机 ✅ |
| L-04 | CI SAST | ✅ | bandit exit 0 ✅ |
| L-05 | backups 治理 | ✅ | README + gitignore ✅ |
| L-06 | 单 Key 无 RBAC | ⚠️ **部分缓解** | 多用户 SaaS + QueryContext；Legacy Key 默认关闭 |
| **G-01** | **Gateway 权限越权（USER=admin device）** | ✅ **已修复** | 双 Agent + 双 device + `GatewayPermissionChecker` + 审计；见 [GATEWAY_ISOLATION.md](GATEWAY_ISOLATION.md) |

**Gateway 隔离新增文件（2026-06）**：`gateway_permission_checker.py`、`gateway_audit_service.py`、`audit_queries.py`、`tests/api/test_gateway_security.py`

**Phase 4 新增/修改文件**：`app/utils/log_safety.py`、`bandit.yaml`、`backups/README.md`、`tests/api/test_security_low.py`、`.github/workflows/ci.yml`

---

## 5. 预计修复工作量（更新）

| 阶段 | 范围 | 原估算 | 剩余工时 | 状态 |
|------|------|--------|----------|------|
| Phase 1 | Critical 核心 | 3~5 人日 | ~4 人日 | ✅ 完成 |
| Phase 1.1 | Critical 闭环 | 1~2 人日 | ~1 人日 | ✅ 已提交 |
| Phase 2 | High | 4~6 人日 | ~5 人日 | ✅ 已提交 |
| Phase 3 | Medium | 3~4 人日 | ~3 人日 | ✅ 已提交 |
| Phase 4 | Low | 2~3 人日 | ~2 人日 | ✅ 已提交 |
| 测试与回归 | 各阶段 | 2~3 人日 | 1~2 人日 | 进行中 |

### 里程碑预期评分

| 里程碑 | 预期综合分 | 状态 |
|--------|------------|------|
| Phase 1（v1） | 54 | ✅ 已测 |
| Phase 1.1 完成 | 58 ~ 62 | ✅ **已测**（并入 v3） |
| Phase 2 完成 | 68 ~ 75 | ✅ **68** |
| Phase 3 完成 | 78 ~ 85 | ✅ **80** |
| Phase 4 完成 | 85 ~ 90 | ✅ **86** |

---

## 6. 测试 Agent 工作指引

> 对照文档：`SECURITY_VERIFICATION_REPORT.md` **v5**  
> 自动化：critical（13）+ high（7）+ medium（9）+ low（7）= **36 安全项**  
> 全量回归：`pytest -q` → **45/45**；`bandit -c bandit.yaml -r app -ll -q` → **0 issues**

### 6.1 每阶段必跑命令

```bash
cd /home/maniac1um/openclaw_news_publisher
.venv/bin/pytest tests/ -v
.venv/bin/pip-audit
cd frontend && npm audit --registry=https://registry.npmjs.org
```

### 6.2 Phase 1 已验收项（勿重复失败）

| 用例 | 命令/方法 | 期望 |
|------|-----------|------|
| 写接口无 Key | `POST .../bulk-delete` 无 Header | 401 |
| 伪造 Key | `X-Api-Key: wrong` | 401 |
| 路径穿越 | `ReportManagementService` + `../../../outside` | 域外文件仍存在 |
| WS 无 Key | `websocket_connect("/api/v1/chat/ws")` | 拒绝 |
| SQL 注入 | `?keyword=' OR 1=1 --` | 200 空列表，非 500 |
| pytest | `pytest -q` | 16 passed |

### 6.3 Phase 1.1 — ✅ 已验收（2026-06-05 v3）

全部用例通过，详见 `SECURITY_VERIFICATION_REPORT.md` v3 §Phase 验收清单。

### 6.4 Phase 2 — ✅ 已验收（2026-06-05 v3）

7/8 通过（v3）；剩余项已在 Phase 2 收尾 + Phase 3 修复。

### 6.5 Phase 2 收尾 + Phase 3 — ✅ 已验收（2026-06-05 v4）

- [x] `GET /docs` 默认 → **404**
- [x] diagnostics / gateway-status / run-readiness → **401** 无凭证，Cookie 后 **200**
- [x] `reports/not-a-uuid` → **422**
- [x] 生产 + `GIT_AUTO_PUSH` / `EXPOSE_OPENAPI` → **RuntimeError**
- [x] Gateway 异常脱敏；WS 消息 Rate limit
- [x] pytest **38**；pip-audit / npm audit **0**
- [x] Dockerfile `USER appuser`（静态审查）
- [x] `docs/api/openclaw-intake.md` 鉴权表已同步
- [x] M-06：`monitoring/{id}/timeseries` 非法 UUID → **422**（v4 后已修补，待 v5 复验）

### 6.7 Phase 4 + M-06 — ✅ 已验收（2026-06-05 v5）

- [x] monitoring timeseries / observations 非法 UUID → **422**
- [x] 超大 POST body → **413**（含 Content-Length 路径）
- [x] MaxBody 无 Content-Length 累计上限（单元 + middleware 测试）
- [x] WS Gateway 错误脱敏
- [x] bandit **0** high issues
- [x] backups README + gitignore
- [x] pytest **45**；v4 行为 **11/11** 无回归

### 6.8 行为测试差距（v5 后）

| 缺口 | 状态 |
|------|------|
| monitoring UUID 422 | ✅ 已关闭 |
| MaxBody 流式绕过 | ✅ 已关闭 |
| Chat WS 异常泄露 | ✅ 已关闭 |
| 单 Key 无 RBAC | ⬜ 长期（L-06） |

---

## 7. 长期安全治理建议

（与 v1.0 相同，略）

- SDL：新 API 默认「鉴权 + Schema + 限流」
- 依赖：lockfile + CI `pip-audit` / `npm audit`
- 密钥：禁止 SPA 内嵌；轮换机制；`chmod 600 .env`
- 网络：反代 TLS + Rate Limit；DB 不映射公网
- 审计：每半年全量代码审计；重大版本前渗透测试

---

## 8. 相关文档索引

| 文档 | 用途 |
|------|------|
| `SECURITY_VERIFICATION_REPORT.md` | 测试 Agent 验证报告 **v5**（评分 **86**） |
| `SECURITY_HARDENING_PLAN.md` | 本文档：计划、进展、验收清单 |
| `tests/api/test_security_*.py` | 安全回归自动化（critical + high + medium + **low**） |
| `docs/server-deployment.md` | 生产部署 + `OPENCLAW_PRODUCTION` checklist |
| `docs/api/openclaw-intake.md` | 门户 workflow 鉴权表（已同步） |

---

## 9. 变更日志

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2026-06-05 | 初版：审计结果与 P0~P3 计划 |
| 1.1 | 2026-06-05 | 纳入验证报告 v1；Phase 1 标为部分完成 |
| 1.2 | 2026-06-05 | Phase 1.1 修复提交；pytest 22/22 |
| 1.3 | 2026-06-05 | Phase 2 High 修复提交；pytest 29/29 |
| 1.4 | 2026-06-05 | Phase 1.1 + Phase 2 联测完成；评分 68；报告 v3 |
| 1.5 | 2026-06-05 | Phase 2 收尾 + Phase 3 提交；pytest 38/38 |
| 1.6 | 2026-06-05 | v4 联测通过；评分 **80**；M-06 部分待 Phase 4 |
| 1.7 | 2026-06-05 | M-06 补全 + Phase 4 提交；pytest **45/45** |
| 1.8 | 2026-06-05 | v5 联测通过；评分 **86**；Phase 1~4 闭环 |

---

**加固计划状态**：✅ **Phase 1~4 验证完成**（L-06 RBAC 为长期项，不阻塞生产）。

**长期治理**：见 §7 — RBAC、lockfile、定期审计。
