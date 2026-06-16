from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.core.exceptions import ConflictError, NotFoundError
from app.db.session import get_db
from app.models.attendance import Attendance
from app.models.event import Event
from app.models.registration import Registration, RegistrationStatus
from app.models.ticket import Ticket, TicketStatus
from app.models.user import User
from app.schemas.attendance import AttendanceCreate, AttendanceRead, AttendanceSummary

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.post("", response_model=AttendanceRead, status_code=201)
def mark_attendance(
    payload: AttendanceCreate,
    current_user: User = Depends(require_roles("Organizer")),
    db: Session = Depends(get_db),
) -> Attendance:
    ticket = db.scalar(select(Ticket).where(Ticket.ticket_number == payload.ticket_number))
    if ticket is None:
        raise NotFoundError("Ticket not found")
    if ticket.status != TicketStatus.valid.value:
        raise ConflictError("Ticket is not valid for attendance")
    if ticket.registration.status != RegistrationStatus.active.value:
        raise ConflictError("Registration is not active")
    if ticket.registration.attendance:
        raise ConflictError("Attendance already marked")

    attendance = Attendance(registration_id=ticket.registration_id, marked_by_id=current_user.id)
    ticket.status = TicketStatus.used.value
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance


@router.get("/{event_id}", response_model=list[AttendanceRead])
def view_attendance(
    event_id: int,
    _: User = Depends(require_roles("Organizer")),
    db: Session = Depends(get_db),
) -> list[Attendance]:
    return list(
        db.scalars(
            select(Attendance)
            .join(Registration)
            .where(Registration.event_id == event_id)
            .order_by(Attendance.created_at.desc())
        )
    )


@router.get("/{event_id}/summary", response_model=AttendanceSummary)
def attendance_summary(
    event_id: int,
    _: User = Depends(require_roles("Organizer")),
    db: Session = Depends(get_db),
) -> AttendanceSummary:
    event = db.get(Event, event_id)
    if event is None:
        raise NotFoundError("Event not found")
    registered = db.scalar(
        select(func.count(Registration.id)).where(
            Registration.event_id == event_id,
            Registration.status == RegistrationStatus.active.value,
        )
    ) or 0
    attended = db.scalar(
        select(func.count(Attendance.id)).join(Registration).where(Registration.event_id == event_id)
    ) or 0
    return AttendanceSummary(
        event_id=event_id,
        registered_count=registered,
        attended_count=attended,
        absent_count=max(registered - attended, 0),
    )
