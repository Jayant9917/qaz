"""Redis-backed rate limiting helpers."""

from __future__ import annotations

import logging

from fastapi import HTTPException, status

from novo.infrastructure.cache import get_redis

logger = logging.getLogger(__name__)


async def enforce_rate_limit(scope: str, *, limit: int, window_seconds: int) -> None:
    key = f"novo:rate-limit:{scope}"
    try:
        redis = get_redis()
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, window_seconds)
        if count > limit:
            ttl = await redis.ttl(key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(max(ttl, 1) if ttl and ttl > 0 else window_seconds)},
            )
    except HTTPException:
        raise
    except Exception:  # pragma: no cover - fail open if cache is unavailable
        logger.warning("rate_limit_unavailable scope=%s", scope, exc_info=True)
