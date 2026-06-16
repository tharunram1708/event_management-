from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.role import Role

DEFAULT_ROLES = {
    "Admin": "Can manage users, roles, events, reports, and system data.",
    "Organizer": "Can manage assigned events, tickets, attendance, and reports.",
    "Participant": "Can register for events and view own tickets.",
}


def seed_roles(db: Session) -> None:
    for name, description in DEFAULT_ROLES.items():
        role = db.scalar(select(Role).where(Role.name == name))
        if role is None:
            db.add(Role(name=name, description=description))
    db.commit()
