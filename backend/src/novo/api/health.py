"""Health and readiness endpoints."""

from typing import Literal

from fastapi import APIRouter, Response, status
from pydantic import BaseModel

from novo.core.config import Settings, get_settings
from novo.core.version import __version__
from novo.infrastructure.health import DependencyState, check_dependencies

router = APIRouter(prefix="/health", tags=["health"])


class LiveResponse(BaseModel):
    status: Literal["alive"]
    service: str
    version: str


class ReadyResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    dependencies: dict[str, DependencyState]


@router.get("/live", response_model=LiveResponse)
async def live(settings: Settings = get_settings()) -> LiveResponse:
    return LiveResponse(status="alive", service=settings.app_name, version=__version__)


@router.get("/ready", response_model=ReadyResponse)
async def ready(response: Response, settings: Settings = get_settings()) -> ReadyResponse:
    dependencies = await check_dependencies(settings)
    required_states = [item for item in dependencies.values() if item.required]
    is_ready = all(item.status == "available" for item in required_states)
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadyResponse(status="ready" if is_ready else "not_ready", dependencies=dependencies)
