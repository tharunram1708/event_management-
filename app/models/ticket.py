from enum import Enum

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class TicketStatus(str, Enum):
    valid = "valid"
    used = "used"
    cancelled = "cancelled"


class Ticket(TimestampMixin, Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    registration_id: Mapped[int] = mapped_column(ForeignKey("registrations.id"), unique=True, nullable=False)
    ticket_number: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default=TicketStatus.valid.value, nullable=False)
    qr_code: Mapped[str | None] = mapped_column(Text)

    registration = relationship("Registration", back_populates="ticket")
