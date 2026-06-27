"""Authentication routes."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from novo.api.dependencies import (
    RequestIdentity,
    get_request_identity,
    require_csrf_protection,
    require_permission,
)
from novo.core.config import Settings, get_settings
from novo.governance.service import get_system_control_state
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
from novo.infrastructure.rate_limit import enforce_rate_limit

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


class UserSettingsResponse(BaseModel):
    id: UUID
    email: EmailStr
    display_name: str
    timezone: str
    locale: str
    status: str
    security_mode: str
    is_active: bool
    last_login_at: datetime | None
    deleted_at: datetime | None
    version: int
    created_at: datetime
    updated_at: datetime


class UserSettingsUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    locale: str | None = Field(default=None, min_length=1, max_length=16)
    security_mode: str | None = Field(default=None, min_length=1, max_length=24)


class SessionResponse(BaseModel):
    id: UUID
    expires_at: datetime
    created_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None


class AuthResponse(BaseModel):
    access_token: str
    csrf_token: str
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


async def _as_user_settings_response(user: User) -> UserSettingsResponse:
    return UserSettingsResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        timezone=user.timezone,
        locale=user.locale,
        status=user.status,
        security_mode=user.security_mode,
        is_active=user.is_active,
        last_login_at=user.last_login_at,
        deleted_at=user.deleted_at,
        version=user.version,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


async def _as_session_response(session: Session) -> SessionResponse:
    return SessionResponse(
        id=session.id,
        expires_at=session.expires_at,
        created_at=session.created_at,
        last_used_at=session.last_used_at,
        revoked_at=session.revoked_at,
    )


SESSION_COOKIE_NAME = "novo_session"
CSRF_COOKIE_NAME = "novo_csrf_token"


def _apply_session_cookies(
    response: Response, *, raw_token: str, csrf_token: str, settings: Settings
) -> None:
    cookie_secure = settings.is_production
    same_site = "lax"
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=raw_token,
        httponly=True,
        secure=cookie_secure,
        samesite=same_site,
        path="/",
        max_age=settings.session_ttl_hours * 60 * 60,
    )
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        secure=cookie_secure,
        samesite=same_site,
        path="/",
        max_age=settings.session_ttl_hours * 60 * 60,
    )


def _clear_session_cookies(response: Response, *, settings: Settings) -> None:
    cookie_secure = settings.is_production
    response.delete_cookie(SESSION_COOKIE_NAME, path="/", secure=cookie_secure, samesite="lax")
    response.delete_cookie(CSRF_COOKIE_NAME, path="/", secure=cookie_secure, samesite="lax")


@router.post("/bootstrap", response_model=AuthResponse)
async def bootstrap(
    request: Request,
    response: Response,
    payload: BootstrapRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthResponse:
    await enforce_rate_limit(
        f"auth:bootstrap:ip:{request.client.host if request.client else 'unknown'}",
        limit=settings.login_rate_limit,
        window_seconds=settings.login_rate_limit_window_seconds,
    )
    if payload.email is not None:
        await enforce_rate_limit(
            f"auth:bootstrap:email:{normalize_email(payload.email)}",
            limit=settings.login_rate_limit,
            window_seconds=settings.login_rate_limit_window_seconds,
        )

    await ensure_security_seed(db, settings)

    owner_email = normalize_email(payload.email or settings.bootstrap_owner_email)
    owner_password = payload.password or settings.bootstrap_owner_password
    display_name = payload.display_name or settings.bootstrap_owner_display_name

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

    session, raw_token, csrf_token = await create_session(
        db,
        user=user,
        session_ttl_hours=settings.session_ttl_hours,
        user_agent=None,
        ip_address=request.client.host if request.client else None,
    )
    user.last_login_at = datetime.now(UTC)
    await get_system_control_state(db, user.id)
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
    _apply_session_cookies(response, raw_token=raw_token, csrf_token=csrf_token, settings=settings)

    permissions = [permission.key for permission in await list_permissions(db)]
    return AuthResponse(
        access_token=raw_token,
        csrf_token=csrf_token,
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
    response: Response,
    db: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthResponse:
    await enforce_rate_limit(
        f"auth:login:ip:{request.client.host if request.client else 'unknown'}",
        limit=settings.login_rate_limit,
        window_seconds=settings.login_rate_limit_window_seconds,
    )
    await enforce_rate_limit(
        f"auth:login:email:{normalize_email(payload.email)}",
        limit=settings.login_rate_limit,
        window_seconds=settings.login_rate_limit_window_seconds,
    )

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

    session, raw_token, csrf_token = await create_session(
        db,
        user=user,
        session_ttl_hours=settings.session_ttl_hours,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    user.last_login_at = datetime.now(UTC)
    await get_system_control_state(db, user.id)
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
    _apply_session_cookies(response, raw_token=raw_token, csrf_token=csrf_token, settings=settings)

    return AuthResponse(
        access_token=raw_token,
        csrf_token=csrf_token,
        expires_at=session.expires_at,
        user=await _as_user_response(user),
        roles=[role.key for role in user.roles],
        permissions=[permission.key for permission in await list_permissions(db)],
        session=await _as_session_response(session),
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    identity: Annotated[RequestIdentity, Depends(require_csrf_protection)],
    response: Response,
    db: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LogoutResponse:
    await enforce_rate_limit(
        f"auth:logout:user:{identity.user.id}",
        limit=settings.mutation_rate_limit,
        window_seconds=settings.mutation_rate_limit_window_seconds,
    )
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
    _clear_session_cookies(response, settings=settings)
    return LogoutResponse(revoked=True)


@router.get("/me", response_model=MeResponse)
async def me(
    identity: Annotated[RequestIdentity, Depends(get_request_identity)],
) -> MeResponse:
    return MeResponse(
        user=await _as_user_response(identity.user),
        roles=identity.roles,
        permissions=identity.permissions,
        session=await _as_session_response(identity.session),
    )


@router.get("/me/settings", response_model=UserSettingsResponse)
async def get_me_settings(
    identity: Annotated[RequestIdentity, Depends(require_permission("auth.read"))],
) -> UserSettingsResponse:
    return await _as_user_settings_response(identity.user)


@router.patch("/me/settings", response_model=UserSettingsResponse)
async def update_me_settings(
    payload: UserSettingsUpdateRequest,
    identity: Annotated[RequestIdentity, Depends(require_permission("auth.write"))],
    _: Annotated[RequestIdentity, Depends(require_csrf_protection)],
    db: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserSettingsResponse:
    await enforce_rate_limit(
        f"auth:settings:user:{identity.user.id}",
        limit=settings.mutation_rate_limit,
        window_seconds=settings.mutation_rate_limit_window_seconds,
    )
    if payload.display_name is not None:
        identity.user.display_name = payload.display_name
    if payload.timezone is not None:
        identity.user.timezone = payload.timezone
    if payload.locale is not None:
        identity.user.locale = payload.locale
    if payload.security_mode is not None:
        identity.user.security_mode = payload.security_mode.strip().casefold()

    identity.user.version += 1
    await log_event(
        db,
        actor_user_id=str(identity.user.id),
        session_id=str(identity.session.id),
        action="auth.settings.update",
        resource_type="user",
        resource_id=str(identity.user.id),
        outcome="success",
        details={
            "display_name": identity.user.display_name,
            "timezone": identity.user.timezone,
            "locale": identity.user.locale,
            "security_mode": identity.user.security_mode,
        },
    )
    await db.commit()
    await db.refresh(identity.user)
    return await _as_user_settings_response(identity.user)
