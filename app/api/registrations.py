from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from app.db.session import get_db
from app.models.event import Event
from app.models.registration import Registration, RegistrationStatus
from app.models.user import User
from app.schemas.common import Message
from app.schemas.registration import RegistrationCreate, RegistrationDetail, RegistrationRead
from app.services.audit import write_audit_log

router = APIRouter(prefix="/registrations", tags=["Registrations"])


def active_registration_count(db: Session, event_id: int) -> int:
    return db.scalar(
        select(func.count(Registration.id)).where(
            Registration.event_id == event_id,
            Registration.status == RegistrationStatus.active.value,
        )
    ) or 0


@router.post("", response_model=RegistrationRead, status_code=201)
def register_for_event(
    payload: RegistrationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Registration:
    event = db.get(Event, payload.event_id)
    if event is None:
        raise NotFoundError("Event not found")

    registration = db.scalar(
        select(Registration).where(
            Registration.event_id == payload.event_id,
            Registration.participant_id == current_user.id,
        )
    )
    if registration and registration.status == RegistrationStatus.active.value:
        raise ConflictError("You are already registered for this event")

    if active_registration_count(db, event.id) >= event.capacity:
        raise ConflictError("Event capacity is full")

    if registration:
        registration.status = RegistrationStatus.active.value
    else:
        registration = Registration(event_id=event.id, participant_id=current_user.id)
        db.add(registration)

    db.flush()
    write_audit_log(db, "REGISTRATION_CREATED", current_user, "Registration", registration.id)
    db.commit()
    db.refresh(registration)
    return registration


@router.post("/{registration_id}/cancel", response_model=Message)
def cancel_registration(
    registration_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Message:
    registration = db.get(Registration, registration_id)
    if registration is None:
        raise NotFoundError("Registration not found")
    if registration.participant_id != current_user.id and not current_user.has_role("Admin"):
        raise PermissionDeniedError()

    registration.status = RegistrationStatus.cancelled.value
    if registration.ticket:
        registration.ticket.status = "cancelled"
    db.commit()
    return Message(message="Registration cancelled")


@router.get("", response_model=list[RegistrationDetail])
def view_registrations(
    event_id: int | None = None,
    current_user: User = Depends(require_roles("Organizer")),
    db: Session = Depends(get_db),
) -> list[Registration]:
    stmt = select(Registration).join(Event)
    if event_id:
        stmt = stmt.where(Registration.event_id == event_id)
    if not current_user.has_role("Admin"):
        stmt = stmt.where(Event.organizer_id == current_user.id)
    return list(db.scalars(stmt.order_by(Registration.created_at.desc())))


@router.get("/history", response_model=list[RegistrationDetail])
def registration_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Registration]:
    return list(
        db.scalars(
            select(Registration)
            .where(Registration.participant_id == current_user.id)
            .order_by(Registration.created_at.desc())
        )
    )
