from datetime import datetime

from pydantic import BaseModel


class EventReport(BaseModel):
    event_id: int
    event_name: str
    start_date: datetime
    end_date: datetime
    capacity: int
    registrations: int
    tickets: int
    attended: int


class RegistrationReport(BaseModel):
    total_registrations: int
    active_registrations: int
    cancelled_registrations: int


class AttendanceReport(BaseModel):
    event_id: int
    registered_count: int
    attended_count: int
    attendance_rate: float
