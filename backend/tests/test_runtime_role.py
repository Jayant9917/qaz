from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from sqlalchemy import text

from novo.infrastructure.database import close_database, get_session_factory
from novo.infrastructure.rls import apply_runtime_role


@pytest.mark.asyncio
async def test_runtime_role_is_active_in_normal_sessions() -> None:
    try:
        async with get_session_factory()() as session:
            await session.execute(text("SET row_security = on"))
            await apply_runtime_role(session)
            row = (
                await session.execute(text("SELECT current_user, current_setting('row_security')"))
            ).fetchone()
            assert row is not None
            assert row[0] == "novo_runtime"
            assert row[1] == "on"
    finally:
        await close_database()


@pytest.mark.asyncio
async def test_apply_runtime_role_fails_closed_when_role_missing() -> None:
    db = AsyncMock()
    db.scalar = AsyncMock(return_value=None)
    db.execute = AsyncMock()

    with pytest.raises(RuntimeError, match="Failed to activate the runtime database role"):
        await apply_runtime_role(db)

    db.execute.assert_not_awaited()
