from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.db.session import get_db
from app.models.event import Event
from app.models.user import User
from app.schemas.common import Message, Page
from app.schemas.event import EventCreate, EventList, EventRead, EventUpdate
from app.services.audit import write_audit_log

router = APIRouter(prefix="/events", tags=["Events"])

SORT_COLUMNS = {
    "name": Event.name,
    "start_date": Event.start_date,
    "created_at": Event.created_at,
}


def can_manage_event(user: User, event: Event) -> bool:
    return user.has_role("Admin") or event.organizer_id == user.id


def apply_event_filters(
    stmt: Select[tuple[Event]],
    search: str | None,
    category_id: int | None,
    date_from: datetime | None,
    date_to: datetime | None,
) -> Select[tuple[Event]]:
    if search:
        stmt = stmt.where(Event.name.ilike(f"%{search}%"))
    if category_id:
        stmt = stmt.where(Event.category_id == category_id)
    if date_from:
        stmt = stmt.where(Event.start_date >= date_from)
    if date_to:
        stmt = stmt.where(Event.start_date <= date_to)
    return stmt


@router.post("", response_model=EventRead, status_code=201)
def create_event(
    payload: EventCreate,
    current_user: User = Depends(require_roles("Organizer")),
    db: Session = Depends(get_db),
) -> Event:
    organizer_id = payload.organizer_id if current_user.has_role("Admin") else current_user.id
    event = Event(**payload.model_dump(exclude={"organizer_id"}), organizer_id=organizer_id)
    db.add(event)
    db.flush()
    write_audit_log(db, "EVENT_CREATED", current_user, "Event", event.id, event.name)
    db.commit()
    db.refresh(event)
    return event


@router.get("", response_model=EventList)
def list_events(
    search: str | None = None,
    category_id: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort_by: Literal["name", "start_date", "created_at"] = "start_date",
    sort_order: Literal["asc", "desc"] = "asc",
    db: Session = Depends(get_db),
) -> EventList:
    base_stmt = apply_event_filters(select(Event), search, category_id, date_from, date_to)
    total = db.scalar(select(func.count()).select_from(base_stmt.subquery())) or 0

    sort_column = SORT_COLUMNS[sort_by]
    order_clause = sort_column.desc() if sort_order == "desc" else sort_column.asc()
    items = list(db.scalars(base_stmt.order_by(order_clause).limit(limit).offset(offset)))
    return EventList(items=items, page=Page(total=total, limit=limit, offset=offset))


@router.get("/{event_id}", response_model=EventRead)
def get_event(event_id: int, db: Session = Depends(get_db)) -> Event:
    event = db.get(Event, event_id)
    if event is None:
        raise NotFoundError("Event not found")
    return event


@router.patch("/{event_id}", response_model=EventRead)
def update_event(
    event_id: int,
    payload: EventUpdate,
    current_user: User = Depends(require_roles("Organizer")),
    db: Session = Depends(get_db),
) -> Event:
    event = db.get(Event, event_id)
    if event is None:
        raise NotFoundError("Event not found")
    if not can_manage_event(current_user, event):
        raise PermissionDeniedError()

    changes = payload.model_dump(exclude_unset=True)
    start_date = changes.get("start_date", event.start_date)
    end_date = changes.get("end_date", event.end_date)
    if end_date <= start_date:
        raise PermissionDeniedError("end_date must be after start_date")

    for field, value in changes.items():
        setattr(event, field, value)
    write_audit_log(db, "EVENT_UPDATED", current_user, "Event", event.id, event.name)
    db.commit()
    db.refresh(event)
    return event


@router.delete("/{event_id}", response_model=Message)
def delete_event(
    event_id: int,
    current_user: User = Depends(require_roles("Organizer")),
    db: Session = Depends(get_db),
) -> Message:
    event = db.get(Event, event_id)
    if event is None:
        raise NotFoundError("Event not found")
    if not can_manage_event(current_user, event):
        raise PermissionDeniedError()
    db.delete(event)
    db.commit()
    return Message(message="Event deleted")
