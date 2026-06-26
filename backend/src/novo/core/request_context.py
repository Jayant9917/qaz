"""Request-scoped correlation context."""

from contextvars import ContextVar, Token
from uuid import uuid4

_request_id: ContextVar[str] = ContextVar("request_id", default="unscoped")


def new_request_id(candidate: str | None = None) -> str:
    """Return a safe request identifier."""

    value = (candidate or "").strip()
    if value and len(value) <= 128 and value.replace("-", "").isalnum():
        return value
    return str(uuid4())


def bind_request_id(request_id: str) -> Token[str]:
    return _request_id.set(request_id)


def reset_request_id(token: Token[str]) -> None:
    _request_id.reset(token)


def get_request_id() -> str:
    return _request_id.get()
