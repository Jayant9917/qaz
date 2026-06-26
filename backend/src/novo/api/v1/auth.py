"""Authentication routes."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from novo.api.dependencies import RequestIdentity, get_request_identity
from novo.core.config import Settings, get_settings
from novo.identity.models import Role, Session, User
from novo.identity.security import hash_password, normalize_email
from novo.identity.service import (
    authenticate_user,
    create_session,
    ensure_security_seed,
    list_permissions,
    log_event,
    revoke_session,
)
from novo.infrastructure.database import get_session

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=256)


class BootstrapRequest(BaseModel):
    email: EmailStr | None = None
    display_name: str | None = None
    password: str | None = None


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    display_name: str
    is_active: bool
    created_at: datetime


class SessionResponse(BaseModel):
    id: UUID
    expires_at: datetime
    created_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: UserResponse
    roles: list[str]
    permissions: list[str]
    session: SessionResponse


class LogoutResponse(BaseModel):
    revoked: bool


class MeResponse(BaseModel):
    user: UserResponse
    roles: list[str]
    permissions: list[str]
    session: SessionResponse


async def _as_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        is_active=user.is_active,
        created_at=user.created_at,
    )


async def _as_session_response(session: Session) -> SessionResponse:
    return SessionResponse(
        id=session.id,
        expires_at=session.expires_at,
        created_at=session.created_at,
        last_used_at=session.last_used_at,
        revoked_at=session.revoked_at,
    )


@router.post("/bootstrap", response_model=AuthResponse)
async def bootstrap(
    request: BootstrapRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthResponse:
    await ensure_security_seed(db, settings)

    owner_email = normalize_email(request.email or settings.bootstrap_owner_email)
    owner_password = request.password or settings.bootstrap_owner_password
    display_name = request.display_name or settings.bootstrap_owner_display_name

    user = await db.scalar(select(User).where(User.email == owner_email))
    if user is None:
        user = User(
            email=owner_email,
            display_name=display_name,
            password_hash=hash_password(owner_password),
            is_active=True,
        )
        owner_role = await db.scalar(select(Role).where(Role.key == "owner"))
        if owner_role is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Owner role is missing",
            )
        user.roles.append(owner_role)
        db.add(user)
        await db.flush()

    session, raw_token = await create_session(
        db,
        user=user,
        session_ttl_hours=settings.session_ttl_hours,
        user_agent=None,
        ip_address=None,
    )
    await log_event(
        db,
        actor_user_id=str(user.id),
        session_id=str(session.id),
        action="auth.bootstrap",
        resource_type="auth",
        resource_id=str(user.id),
        outcome="success",
        details={"version": "0.1.0"},
    )
    await db.commit()

    permissions = [permission.key for permission in await list_permissions(db)]
    return AuthResponse(
        access_token=raw_token,
        expires_at=session.expires_at,
        user=await _as_user_response(user),
        roles=[role.key for role in user.roles],
        permissions=permissions,
        session=await _as_session_response(session),
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthResponse:
    user = await authenticate_user(db, payload.email, payload.password)
    if user is None:
        await log_event(
            db,
            actor_user_id=None,
            session_id=None,
            action="auth.login",
            resource_type="auth",
            resource_id=None,
            outcome="denied",
            details={"email": normalize_email(payload.email)},
        )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    session, raw_token = await create_session(
        db,
        user=user,
        session_ttl_hours=settings.session_ttl_hours,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    await log_event(
        db,
        actor_user_id=str(user.id),
        session_id=str(session.id),
        action="auth.login",
        resource_type="auth",
        resource_id=str(user.id),
        outcome="success",
        details={"email": user.email},
    )
    await db.commit()

    return AuthResponse(
        access_token=raw_token,
        expires_at=session.expires_at,
        user=await _as_user_response(user),
        roles=[role.key for role in user.roles],
        permissions=[permission.key for permission in await list_permissions(db)],
        session=await _as_session_response(session),
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    identity: Annotated[RequestIdentity, Depends(get_request_identity)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> LogoutResponse:
    await revoke_session(db, identity.session, "user_logout")
    await log_event(
        db,
        actor_user_id=str(identity.user.id),
        session_id=str(identity.session.id),
        action="auth.logout",
        resource_type="auth",
        resource_id=str(identity.user.id),
        outcome="success",
        details={},
    )
    await db.commit()
    return LogoutResponse(revoked=True)


@router.get("/me", response_model=MeResponse)
async def me(identity: Annotated[RequestIdentity, Depends(get_request_identity)]) -> MeResponse:
    return MeResponse(
        user=await _as_user_response(identity.user),
        roles=identity.roles,
        permissions=identity.permissions,
        session=await _as_session_response(identity.session),
    )
