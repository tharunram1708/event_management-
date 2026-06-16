from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from app.db.session import get_db
from app.models.registration import Registration, RegistrationStatus
from app.models.ticket import Ticket, TicketStatus
from app.models.user import User
from app.schemas.common import Message
from app.schemas.ticket import TicketCreate, TicketDetail, TicketRead, TicketValidation
from app.services.audit import write_audit_log
from app.services.email import send_ticket_email
from app.services.tickets import generate_ticket_number, make_qr_code_base64

router = APIRouter(prefix="/tickets", tags=["Tickets"])


def find_unique_ticket_number(db: Session) -> str:
    for _ in range(10):
        ticket_number = generate_ticket_number()
        if not db.scalar(select(Ticket).where(Ticket.ticket_number == ticket_number)):
            return ticket_number
    raise ConflictError("Could not generate a unique ticket number")


@router.post("", response_model=TicketRead, status_code=201)
def generate_ticket(
    payload: TicketCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Ticket:
    registration = db.get(Registration, payload.registration_id)
    if registration is None:
        raise NotFoundError("Registration not found")
    if registration.participant_id != current_user.id and not current_user.has_role("Admin"):
        raise PermissionDeniedError()
    if registration.status != RegistrationStatus.active.value:
        raise ConflictError("Cannot generate a ticket for a cancelled registration")
    if registration.ticket:
        return registration.ticket

    ticket_number = find_unique_ticket_number(db)
    ticket = Ticket(
        registration_id=registration.id,
        ticket_number=ticket_number,
        qr_code=make_qr_code_base64(ticket_number),
    )
    db.add(ticket)
    db.flush()
    write_audit_log(db, "TICKET_GENERATED", current_user, "Ticket", ticket.id, ticket.ticket_number)
    db.commit()
    db.refresh(ticket)
    background_tasks.add_task(send_ticket_email, registration.participant.email, ticket.ticket_number)
    return ticket


@router.get("/{ticket_number}", response_model=TicketDetail)
def view_ticket(
    ticket_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Ticket:
    ticket = db.scalar(select(Ticket).where(Ticket.ticket_number == ticket_number))
    if ticket is None:
        raise NotFoundError("Ticket not found")
    registration = ticket.registration
    event = registration.event
    can_view = (
        registration.participant_id == current_user.id
        or current_user.has_role("Admin")
        or event.organizer_id == current_user.id
    )
    if not can_view:
        raise PermissionDeniedError()
    return ticket


@router.post("/{ticket_number}/validate", response_model=TicketValidation)
def validate_ticket(
    ticket_number: str,
    _: User = Depends(require_roles("Organizer")),
    db: Session = Depends(get_db),
) -> TicketValidation:
    ticket = db.scalar(select(Ticket).where(Ticket.ticket_number == ticket_number))
    if ticket is None:
        return TicketValidation(ticket_number=ticket_number, is_valid=False)

    is_valid = (
        ticket.status == TicketStatus.valid.value
        and ticket.registration.status == RegistrationStatus.active.value
    )
    return TicketValidation(ticket_number=ticket_number, is_valid=is_valid, status=ticket.status)


@router.post("/{ticket_number}/cancel", response_model=Message)
def cancel_ticket(
    ticket_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Message:
    ticket = db.scalar(select(Ticket).where(Ticket.ticket_number == ticket_number))
    if ticket is None:
        raise NotFoundError("Ticket not found")
    registration = ticket.registration
    can_cancel = registration.participant_id == current_user.id or current_user.has_role("Admin")
    if not can_cancel:
        raise PermissionDeniedError()
    ticket.status = TicketStatus.cancelled.value
    db.commit()
    return Message(message="Ticket cancelled")
