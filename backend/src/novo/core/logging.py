"""Privacy-safe structured logging foundation."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from novo.core.request_context import get_request_id

_STANDARD_LOG_RECORD_KEYS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "message",
}


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        return value[:2000]
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            key_str = str(key)
            if any(marker in key_str.lower() for marker in ("secret", "password", "token", "key")):
                sanitized[key_str] = "[redacted]"
            else:
                sanitized[key_str] = _sanitize_value(item)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value[:50]]
    if isinstance(value, tuple):
        return [_sanitize_value(item) for item in value[:50]]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return str(value)[:2000]


class JsonFormatter(logging.Formatter):
    """Emit bounded structured logs without application payloads."""

    def format(self, record: logging.LogRecord) -> str:
        details: dict[str, Any] = {}
        for key, value in record.__dict__.items():
            if key in _STANDARD_LOG_RECORD_KEYS or key.startswith("_"):
                continue
            details[key] = _sanitize_value(value)

        event: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "severity": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
            "request_id": get_request_id(),
        }
        if details:
            event["details"] = details
        if record.exc_info:
            event["exception_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None
        return json.dumps(event, ensure_ascii=True, separators=(",", ":"))


def configure_logging(level: str) -> None:
    """Configure the root logger once."""

    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(level.upper())
