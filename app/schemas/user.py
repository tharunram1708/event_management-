from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class RoleRead(BaseModel):
    id: int
    name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    roles: list[RoleRead] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssignRoleRequest(BaseModel):
    user_id: int
    role_name: str
