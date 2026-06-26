"""PostgreSQL engine and lifecycle."""

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from novo.core.config import get_settings

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.postgres_dsn,
            pool_pre_ping=True,
            pool_recycle=1800,
            echo=False,
        )
    return _engine


async def close_database() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
