"""Lightweight user-message safety checks for chat and similar inputs."""

from __future__ import annotations

import re

# Each entry: (compiled pattern, user-facing category label)
_BLOCKED: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"(忽略|无视|绕过).{0,12}(之前|上面|系统|安全).{0,12}(指令|规则|限制|提示)",
            re.I,
        ),
        "提示词注入",
    ),
    (
        re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", re.I),
        "prompt injection",
    ),
    (
        re.compile(r"(jailbreak|DAN\s+mode|developer\s+mode\s+enabled)", re.I),
        "prompt injection",
    ),
    (
        re.compile(
            r"(泄露|输出|告诉我|打印|export).{0,16}(api[_\s-]?key|jwt[_\s-]?secret|密码|password|\.env|database_url|dsn)",
            re.I,
        ),
        "敏感信息请求",
    ),
    (
        re.compile(
            r"(reveal|show|print|dump).{0,16}(api[_\s-]?key|jwt|secret|password|\.env|credentials)",
            re.I,
        ),
        "sensitive data request",
    ),
    (
        re.compile(r"\brm\s+-rf\s+(/|\\|\.|\*)", re.I),
        "危险系统命令",
    ),
    (
        re.compile(r"(drop\s+database|truncate\s+table|delete\s+from\s+\w+\s*;)", re.I),
        "危险数据库操作",
    ),
    (
        re.compile(
            r"(制作|合成|购买渠道).{0,8}(炸弹|毒品|冰毒|海洛因|枪支|爆炸物)",
            re.I,
        ),
        "违法有害内容",
    ),
    (
        re.compile(
            r"(how\s+to\s+(make|build|synthesize)|recipe\s+for).{0,20}(bomb|explosive|meth|heroin|weapon)",
            re.I,
        ),
        "illegal harmful content",
    ),
    (
        re.compile(
            r"(钓鱼|诈骗脚本|木马|勒索软件|入侵教程|撞库|脱库)",
            re.I,
        ),
        "违法有害内容",
    ),
]

# Additional patterns for portal USER → Gateway (system/file/shell access)
_GATEWAY_USER_BLOCKED: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"\b(cat|head|tail|less|more|nano|vim|vi|sed|awk)\s+[/~]", re.I),
        "文件读取命令",
    ),
    (
        re.compile(r"\b(sudo|su\s|chmod|chown|kill\s+-9|systemctl|service\s+\w+\s+(stop|restart))", re.I),
        "系统管理命令",
    ),
    (
        re.compile(r"(/etc/|/root/|~/.openclaw|\.openclaw/|/var/log/)", re.I),
        "敏感路径访问",
    ),
    (
        re.compile(r"\b(curl|wget|fetch)\s+https?://", re.I),
        "任意 HTTP 出站",
    ),
    (
        re.compile(r"(修改|写入|删除|覆盖).{0,8}(文件|配置|服务器|gateway|openclaw)", re.I),
        "文件/配置变更",
    ),
    (
        re.compile(r"\b(write|modify|delete|overwrite)\s+(file|config|server)", re.I),
        "file/config modification",
    ),
]


def check_user_message(text: str) -> str | None:
    """Return a short rejection reason if *text* should be blocked, else None."""
    normalized = (text or "").strip()
    if not normalized:
        return "empty message"
    if len(normalized) > 4000:
        return "message too long"
    for pattern, category in _BLOCKED:
        if pattern.search(normalized):
            return category
    return None


def check_gateway_user_message(text: str) -> str | None:
    """Stricter checks for portal USER role before Gateway forwarding."""
    normalized = (text or "").strip()
    if not normalized:
        return "empty message"
    for pattern, category in _GATEWAY_USER_BLOCKED:
        if pattern.search(normalized):
            return category
    return None
