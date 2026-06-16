from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Event(TimestampMixin, Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    start_date: Mapped[datetime] = mapped_column(index=True, nullable=False)
    end_date: Mapped[datetime] = mapped_column(index=True, nullable=False)
    venue: Mapped[str] = mapped_column(String(200), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    organizer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))

    organizer = relationship("User", back_populates="organized_events")
    category = relationship("Category", back_populates="events")
    registrations = relationship("Registration", back_populates="event", cascade="all, delete-orphan")
