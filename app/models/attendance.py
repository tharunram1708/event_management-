from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Attendance(TimestampMixin, Base):
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(primary_key=True)
    registration_id: Mapped[int] = mapped_column(
        ForeignKey("registrations.id"),
        unique=True,
        nullable=False,
    )
    marked_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    registration = relationship("Registration", back_populates="attendance")
    marked_by = relationship("User")
