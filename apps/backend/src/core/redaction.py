import os
import re
from collections.abc import Mapping, Sequence
from typing import Any

_REDACTION = "[REDACTED]"
_SENSITIVE_KEY_RE = re.compile(
    r"(token|secret|password|api[_-]?key|access[_-]?key|database_url|redis_url|fernet|jwt)",
    re.I,
)
_GENERIC_SECRET_PATTERNS = (
    (re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"), _REDACTION),
    (re.compile(r"sk-[A-Za-z0-9_-]{20,}"), _REDACTION),
    (re.compile(r"(Bearer\s+)[A-Za-z0-9._~+/=-]{20,}", re.I), r"\1" + _REDACTION),
    (re.compile(r"(https://)[^/\s:@]+:[^@\s]+@"), r"\1" + _REDACTION + "@"),
    (
        re.compile(r"(postgresql(?:\+\w+)?://[^:\s/@]+:)[^@\s]+@", re.I),
        r"\1" + _REDACTION + "@",
    ),
    (re.compile(r"(redis://(?::)?)[^@\s]+@", re.I), r"\1" + _REDACTION + "@"),
)


def _secret_values() -> tuple[str, ...]:
    values: set[str] = set()
    for key, value in os.environ.items():
        if not value or len(value) < 4:
            continue
        if _SENSITIVE_KEY_RE.search(key):
            values.add(value)
    return tuple(sorted(values, key=len, reverse=True))


def redact_text(value: str) -> str:
    redacted = value
    for secret in _secret_values():
        redacted = redacted.replace(secret, _REDACTION)
    for pattern, replacement in _GENERIC_SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, Mapping):
        result: dict[Any, Any] = {}
        for key, item in value.items():
            if isinstance(key, str) and _SENSITIVE_KEY_RE.search(key):
                result[key] = _REDACTION if item else item
            else:
                result[key] = redact_value(item)
        return result
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return [redact_value(item) for item in value]
    return value
