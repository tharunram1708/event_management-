from enum import Enum

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class RegistrationStatus(str, Enum):
    active = "active"
    cancelled = "cancelled"


class Registration(TimestampMixin, Base):
    __tablename__ = "registrations"
    __table_args__ = (UniqueConstraint("event_id", "participant_id", name="uq_event_participant"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    participant_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default=RegistrationStatus.active.value, nullable=False)

    event = relationship("Event", back_populates="registrations")
    participant = relationship("User", back_populates="registrations")
    ticket = relationship("Ticket", back_populates="registration", uselist=False, cascade="all, delete-orphan")
    attendance = relationship("Attendance", back_populates="registration", uselist=False, cascade="all, delete-orphan")
