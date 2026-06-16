from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.models.attendance import Attendance
from app.models.event import Event
from app.models.registration import Registration, RegistrationStatus
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.report import AttendanceReport, EventReport, RegistrationReport

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/events/{event_id}", response_model=EventReport)
def event_report(
    event_id: int,
    _: User = Depends(require_roles("Organizer")),
    db: Session = Depends(get_db),
) -> EventReport:
    event = db.get(Event, event_id)
    if event is None:
        raise NotFoundError("Event not found")

    registrations = db.scalar(select(func.count(Registration.id)).where(Registration.event_id == event_id)) or 0
    tickets = db.scalar(
        select(func.count(Ticket.id)).join(Registration).where(Registration.event_id == event_id)
    ) or 0
    attended = db.scalar(
        select(func.count(Attendance.id)).join(Registration).where(Registration.event_id == event_id)
    ) or 0
    return EventReport(
        event_id=event.id,
        event_name=event.name,
        start_date=event.start_date,
        end_date=event.end_date,
        capacity=event.capacity,
        registrations=registrations,
        tickets=tickets,
        attended=attended,
    )


@router.get("/registrations", response_model=RegistrationReport)
def registration_report(
    event_id: int | None = None,
    _: User = Depends(require_roles("Organizer")),
    db: Session = Depends(get_db),
) -> RegistrationReport:
    stmt = select(Registration)
    if event_id:
        stmt = stmt.where(Registration.event_id == event_id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    active = db.scalar(
        select(func.count()).select_from(
            stmt.where(Registration.status == RegistrationStatus.active.value).subquery()
        )
    ) or 0
    cancelled = db.scalar(
        select(func.count()).select_from(
            stmt.where(Registration.status == RegistrationStatus.cancelled.value).subquery()
        )
    ) or 0
    return RegistrationReport(
        total_registrations=total,
        active_registrations=active,
        cancelled_registrations=cancelled,
    )


@router.get("/attendance/{event_id}", response_model=AttendanceReport)
def attendance_report(
    event_id: int,
    _: User = Depends(require_roles("Organizer")),
    db: Session = Depends(get_db),
) -> AttendanceReport:
    registered = db.scalar(
        select(func.count(Registration.id)).where(
            Registration.event_id == event_id,
            Registration.status == RegistrationStatus.active.value,
        )
    ) or 0
    attended = db.scalar(
        select(func.count(Attendance.id)).join(Registration).where(Registration.event_id == event_id)
    ) or 0
    rate = round((attended / registered) * 100, 2) if registered else 0.0
    return AttendanceReport(event_id=event_id, registered_count=registered, attended_count=attended, attendance_rate=rate)
