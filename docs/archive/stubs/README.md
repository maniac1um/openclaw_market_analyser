# 兼容 URL 重定向（保留期）

**策略 ADR-008**：以下 stub 保留 **一个发布周期**（自 2026-06-08 起），供旧书签与外部链接过渡。

| 当前路径 | 权威路径 | 计划 |
|----------|----------|------|
| [docs/api/openclaw-intake.md](../api/openclaw-intake.md) | [human/api/openclaw-intake.md](../human/api/openclaw-intake.md) | 下周期迁入本目录或删除 |
| [docs/security/GATEWAY_ISOLATION.md](../security/GATEWAY_ISOLATION.md) | [human/security/gateway-isolation.md](../human/security/gateway-isolation.md) | 同上 |
| [docs/security/SECURITY_HARDENING_PLAN.md](../security/SECURITY_HARDENING_PLAN.md) | [reports/security/hardening-plan-2026-06-05.md](../reports/security/hardening-plan-2026-06-05.md) | 同上 |
| [docs/security/SECURITY_VERIFICATION_REPORT.md](../security/SECURITY_VERIFICATION_REPORT.md) | [reports/security/verification-report-v5-2026-06-05.md](../reports/security/verification-report-v5-2026-06-05.md) | 同上 |

## 已移除的根目录 stub（2026-06-08）

以下文件已删除，请直接使用权威路径：

| 原根目录路径 | 现权威路径 |
|--------------|------------|
| `DEPLOYMENT_GUIDE.md` | [human/deployment/getting-started.md](../human/deployment/getting-started.md) |
| `cleanup.sh` | [scripts/local/cleanup.sh](../../scripts/local/cleanup.sh) |
| `cleanup.ps1` | [scripts/local/cleanup.ps1](../../scripts/local/cleanup.ps1) |

清理前须全仓库 `grep` 更新引用。
