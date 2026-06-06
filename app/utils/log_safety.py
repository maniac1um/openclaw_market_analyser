"""Redact secrets and connection details from log messages."""

from __future__ import annotations

import re

_DSN_PASSWORD = re.compile(r"(postgresql(?:\+\w+)?://[^:]+:)([^@]+)(@)", re.IGNORECASE)
_API_KEY = re.compile(r"(api[_-]?key|x-api-key|authorization)\s*[:=]\s*\S+", re.IGNORECASE)
_BEARER = re.compile(r"Bearer\s+\S+", re.IGNORECASE)


def sanitize_for_log(message: str) -> str:
    text = str(message)
    text = _DSN_PASSWORD.sub(r"\1***\3", text)
    text = _API_KEY.sub(lambda m: f"{m.group(0).split('=')[0].split(':')[0]}=***", text)
    text = _BEARER.sub("Bearer ***", text)
    return text
