from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.category import CategoryRead
from app.schemas.common import Page
from app.schemas.user import UserRead


class EventBase(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    description: str | None = None
    start_date: datetime
    end_date: datetime
    venue: str = Field(min_length=2, max_length=200)
    capacity: int = Field(gt=0)
    category_id: int | None = None

    @model_validator(mode="after")
    def dates_must_be_ordered(self) -> "EventBase":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class EventCreate(EventBase):
    organizer_id: int | None = None


class EventUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    venue: str | None = Field(default=None, min_length=2, max_length=200)
    capacity: int | None = Field(default=None, gt=0)
    category_id: int | None = None


class EventRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    start_date: datetime
    end_date: datetime
    venue: str
    capacity: int
    organizer: UserRead
    category: CategoryRead | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventList(BaseModel):
    items: list[EventRead]
    page: Page
