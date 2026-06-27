"""Version 1 route composition."""

from fastapi import APIRouter

from novo.api.health import router as health_router
from novo.api.v1.audit import router as audit_router
from novo.api.v1.auth import router as auth_router
from novo.api.v1.control import router as control_router
from novo.api.v1.conversations import router as conversations_router
from novo.api.v1.models import router as models_router
from novo.api.v1.permissions import router as permissions_router
from novo.api.v1.prompts import router as prompts_router

router = APIRouter()
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(permissions_router)
router.include_router(control_router)
router.include_router(audit_router)
router.include_router(models_router)
router.include_router(prompts_router)
router.include_router(conversations_router)
