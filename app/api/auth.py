from datetime import timedelta

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.db.session import get_db
from app.models.role import Role
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, LoginResponse, RefreshTokenRequest, RegisterUser
from app.schemas.common import Message
from app.schemas.user import UserRead
from app.services.audit import write_audit_log

router = APIRouter(prefix="/auth", tags=["Authentication"])


def build_tokens(user: User) -> LoginResponse:
    settings = get_settings()
    access_token = create_token(
        subject=str(user.id),
        token_type="access",
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    refresh_token = create_token(
        subject=str(user.id),
        token_type="refresh",
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )
    return LoginResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/register", response_model=UserRead, status_code=201)
def register(payload: RegisterUser, db: Session = Depends(get_db)) -> User:
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise ConflictError("A user with this email already exists")

    role = db.scalar(select(Role).where(func.lower(Role.name) == payload.role_name.lower()))
    if role is None:
        raise NotFoundError("Role not found")
    if role.name == "Admin":
        raise PermissionDeniedError("Admin role cannot be selected during registration")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        roles=[role],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=LoginResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> LoginResponse:
    user = db.scalar(select(User).where(User.email == form_data.username))
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise PermissionDeniedError("Invalid email or password")
    if not user.is_active:
        raise PermissionDeniedError("User account is disabled")

    write_audit_log(db, action="USER_LOGIN", user=user, entity_type="User", entity_id=user.id)
    db.commit()
    return build_tokens(user)


@router.post("/refresh", response_model=LoginResponse)
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)) -> LoginResponse:
    token_data = decode_token(payload.refresh_token)
    if not token_data or token_data.get("type") != "refresh":
        raise PermissionDeniedError("Invalid or expired refresh token")

    user = db.scalar(select(User).where(User.id == int(token_data["sub"]), User.is_active.is_(True)))
    if user is None:
        raise PermissionDeniedError("User is not active or no longer exists")
    return build_tokens(user)


@router.post("/change-password", response_model=Message)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Message:
    if not verify_password(payload.old_password, current_user.hashed_password):
        raise PermissionDeniedError("Old password is incorrect")

    current_user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return Message(message="Password changed successfully")


@router.get("/me", response_model=UserRead)
def read_profile(current_user: User = Depends(get_current_user)) -> User:
    return current_user
