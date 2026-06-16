from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.event import EventRead
from app.schemas.user import UserRead


class RegistrationCreate(BaseModel):
    event_id: int


class RegistrationRead(BaseModel):
    id: int
    event_id: int
    participant_id: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RegistrationDetail(RegistrationRead):
    event: EventRead
    participant: UserRead
