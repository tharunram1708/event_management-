from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AttendanceCreate(BaseModel):
    ticket_number: str


class AttendanceRead(BaseModel):
    id: int
    registration_id: int
    marked_by_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttendanceSummary(BaseModel):
    event_id: int
    registered_count: int
    attended_count: int
    absent_count: int
