from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.models.role import Role
from app.models.user import User
from app.schemas.common import Message
from app.schemas.user import AssignRoleRequest, RoleRead

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("", response_model=list[RoleRead])
def list_roles(_: User = Depends(require_admin), db: Session = Depends(get_db)) -> list[Role]:
    return list(db.scalars(select(Role).order_by(Role.name)))


@router.post("/assign", response_model=Message)
def assign_role(
    payload: AssignRoleRequest,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Message:
    user = db.get(User, payload.user_id)
    role = db.scalar(select(Role).where(func.lower(Role.name) == payload.role_name.lower()))
    if user is None:
        raise NotFoundError("User not found")
    if role is None:
        raise NotFoundError("Role not found")
    if role not in user.roles:
        user.roles.append(role)
        db.commit()
    return Message(message=f"{role.name} role assigned to {user.email}")
