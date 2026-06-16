from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.registration import RegistrationRead


class TicketCreate(BaseModel):
    registration_id: int


class TicketRead(BaseModel):
    id: int
    registration_id: int
    ticket_number: str
    status: str
    qr_code: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TicketDetail(TicketRead):
    registration: RegistrationRead


class TicketValidation(BaseModel):
    ticket_number: str
    is_valid: bool
    status: str | None = None
