from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote_plus

import pytest
from fastapi.testclient import TestClient
from redis import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from novo.core.config import get_settings
from novo.infrastructure.database import close_database
from novo.main import create_app

BACKEND_ROOT = Path(__file__).resolve().parents[1]
TEST_POSTGRES_DB = "novo_test"
TEST_REDIS_DB = 15
ENV_KEYS = (
    "NOVO_ENVIRONMENT",
    "NOVO_POSTGRES_DB",
    "NOVO_REDIS_DB",
    "NOVO_REQUIRE_INFRASTRUCTURE_FOR_READINESS",
)


async def _recreate_test_database() -> None:
    settings = get_settings()
    admin_dsn = (
        f"postgresql+asyncpg://{settings.postgres_user}:{quote_plus(settings.postgres_password)}"
        f"@{settings.postgres_host}:{settings.postgres_port}/postgres"
    )
    engine = create_async_engine(admin_dsn, isolation_level="AUTOCOMMIT", echo=False)
    try:
        async with engine.connect() as connection:
            await connection.execute(
                text(f'DROP DATABASE IF EXISTS "{TEST_POSTGRES_DB}" WITH (FORCE)')
            )
            await connection.execute(
                text(f'CREATE DATABASE "{TEST_POSTGRES_DB}" OWNER "{settings.postgres_user}"')
            )
    finally:
        await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def isolated_test_environment() -> None:
    original_env = {key: os.environ.get(key) for key in ENV_KEYS}
    os.environ["NOVO_ENVIRONMENT"] = "test"
    os.environ["NOVO_POSTGRES_DB"] = TEST_POSTGRES_DB
    os.environ["NOVO_REDIS_DB"] = str(TEST_REDIS_DB)
    os.environ["NOVO_REQUIRE_INFRASTRUCTURE_FOR_READINESS"] = "false"
    get_settings.cache_clear()

    asyncio.run(_recreate_test_database())
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        check=True,
        env=os.environ.copy(),
    )

    try:
        yield
    finally:
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        get_settings.cache_clear()


@pytest.fixture(autouse=True)
def clear_redis_state() -> None:
    settings = get_settings()
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        client.flushdb()
        yield
        client.flushdb()
    finally:
        client.close()


@pytest.fixture
def client() -> TestClient:
    get_settings.cache_clear()
    with TestClient(create_app()) as test_client:
        yield test_client
    asyncio.run(close_database())
    get_settings.cache_clear()
