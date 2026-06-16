from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_events: int
    total_participants: int
    upcoming_events: int
    completed_events: int


class EventRegistrationCount(BaseModel):
    event_id: int
    event_name: str
    registration_count: int
