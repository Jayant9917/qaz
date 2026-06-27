"""Row-level security helpers."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def apply_owner_context(db: AsyncSession, owner_id: UUID) -> None:
    await db.execute(
        text(
            "SELECT set_config('app.owner_id', :owner_id, true), "
            "set_config('app.user_id', :owner_id, true)"
        ),
        {"owner_id": str(owner_id)},
    )


async def apply_runtime_role(db: AsyncSession) -> None:
    try:
        exists = await db.scalar(text("SELECT 1 FROM pg_roles WHERE rolname = 'novo_runtime'"))
        if not exists:
            raise RuntimeError("Runtime role novo_runtime is missing")
        await db.execute(text("SET ROLE novo_runtime"))
    except Exception:
        logger.warning("runtime_role_unavailable", exc_info=True)
        raise RuntimeError("Failed to activate the runtime database role") from None
