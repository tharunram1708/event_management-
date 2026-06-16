from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from app.models.event import Event
from app.models.registration import Registration
from app.models.user import User
from app.schemas.dashboard import DashboardStats, EventRegistrationCount

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def event_scope(stmt, user: User):
    if user.has_role("Admin"):
        return stmt
    return stmt.where(Event.organizer_id == user.id)


@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(
    current_user: User = Depends(require_roles("Organizer")),
    db: Session = Depends(get_db),
) -> DashboardStats:
    now = datetime.now(timezone.utc)
    total_events = db.scalar(event_scope(select(func.count(Event.id)), current_user)) or 0
    total_participants = db.scalar(
        event_scope(
            select(func.count(distinct(Registration.participant_id))).join(Event),
            current_user,
        )
    ) or 0
    upcoming_events = db.scalar(
        event_scope(select(func.count(Event.id)).where(Event.start_date > now), current_user)
    ) or 0
    completed_events = db.scalar(
        event_scope(select(func.count(Event.id)).where(Event.end_date < now), current_user)
    ) or 0

    return DashboardStats(
        total_events=total_events,
        total_participants=total_participants,
        upcoming_events=upcoming_events,
        completed_events=completed_events,
    )


@router.get("/event-registration-counts", response_model=list[EventRegistrationCount])
def event_registration_counts(
    current_user: User = Depends(require_roles("Organizer")),
    db: Session = Depends(get_db),
) -> list[EventRegistrationCount]:
    stmt = (
        select(Event.id, Event.name, func.count(Registration.id))
        .outerjoin(Registration)
        .group_by(Event.id, Event.name)
        .order_by(Event.start_date.desc())
    )
    stmt = event_scope(stmt, current_user)
    return [
        EventRegistrationCount(event_id=row[0], event_name=row[1], registration_count=row[2])
        for row in db.execute(stmt)
    ]
