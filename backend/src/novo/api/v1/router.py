"""Version 1 route composition."""

from fastapi import APIRouter

from novo.api.health import router as health_router

router = APIRouter()
router.include_router(health_router)
