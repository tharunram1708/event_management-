from collections.abc import Callable

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import PermissionDeniedError
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise PermissionDeniedError("Invalid or expired access token")

    user_id = payload.get("sub")
    user = db.scalar(select(User).where(User.id == int(user_id), User.is_active.is_(True)))
    if user is None:
        raise PermissionDeniedError("User is not active or no longer exists")
    return user


def require_roles(*role_names: str) -> Callable[[User], User]:
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        user_roles = {role.name for role in current_user.roles}
        if "Admin" in user_roles or user_roles.intersection(role_names):
            return current_user
        raise PermissionDeniedError()

    return dependency


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.has_role("Admin"):
        return current_user
    raise PermissionDeniedError("Admin access is required")
