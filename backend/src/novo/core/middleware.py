"""HTTP middleware."""

import logging
from collections.abc import Awaitable, Callable
from time import perf_counter

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from novo.core.request_context import bind_request_id, new_request_id, reset_request_id

logger = logging.getLogger(__name__)

RequestHandler = Callable[[Request], Awaitable[Response]]


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Bind request correlation and emit a safe completion event."""

    async def dispatch(self, request: Request, call_next: RequestHandler) -> Response:
        request_id = new_request_id(request.headers.get("x-request-id"))
        token = bind_request_id(request_id)
        started = perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((perf_counter() - started) * 1000, 2)
            logger.exception(
                "http.request.failed method=%s path=%s duration_ms=%s",
                request.method,
                request.url.path,
                duration_ms,
            )
            raise
        else:
            response.headers["X-Request-ID"] = request_id
            duration_ms = round((perf_counter() - started) * 1000, 2)
            logger.info(
                "http.request.completed method=%s path=%s status=%s duration_ms=%s",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
            )
            return response
        finally:
            reset_request_id(token)
