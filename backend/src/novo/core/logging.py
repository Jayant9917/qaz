"""Privacy-safe structured logging foundation."""

import json
import logging
from datetime import UTC, datetime
from typing import Any

from novo.core.request_context import get_request_id


class JsonFormatter(logging.Formatter):
    """Emit bounded structured logs without application payloads."""

    def format(self, record: logging.LogRecord) -> str:
        event: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "severity": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
            "request_id": get_request_id(),
        }
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
