"""NOVO FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from novo.api.v1.router import router as v1_router
from novo.core.config import get_settings
from novo.core.logging import configure_logging
from novo.core.middleware import RequestContextMiddleware
from novo.core.version import __version__
from novo.identity.service import ensure_security_seed
from novo.infrastructure.cache import close_redis
from novo.infrastructure.database import close_database, get_session_factory


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    async with get_session_factory()() as session:
        await ensure_security_seed(session, settings)
    yield
    await close_redis()
    await close_database()


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    application = FastAPI(
        title=settings.app_name,
        version=__version__,
        docs_url="/api/docs" if not settings.is_production else None,
        redoc_url="/api/redoc" if not settings.is_production else None,
        openapi_url="/api/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )
    application.add_middleware(RequestContextMiddleware)
    frontend_origin = settings.frontend_origin.rstrip("/")
    loopback_origin = frontend_origin.replace("localhost", "127.0.0.1")
    allow_origins = list(dict.fromkeys([frontend_origin, loopback_origin]))

    application.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "X-CSRF-Token",
            "X-Request-ID",
            "Idempotency-Key",
            "Authorization",
        ],
    )
    application.include_router(v1_router, prefix=settings.api_prefix)
    return application


app = create_app()
