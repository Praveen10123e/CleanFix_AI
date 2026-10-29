from datetime import datetime
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, generate_uuid, utc_now


class Classroom(Base):
    __tablename__ = "classrooms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    room_number: Mapped[str] = mapped_column(String(50), nullable=False)
    building: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("building", "room_number", name="uq_classroom_building_room"),
    )

    # Relationships
    devices: Mapped[List["Device"]] = relationship(
        "Device",
        back_populates="classroom",
        cascade="all, delete-orphan",
    )
    complaints: Mapped[List["Complaint"]] = relationship(
        "Complaint",
        back_populates="classroom",
    )

    def __repr__(self) -> str:
        return f"<Classroom(id={self.id}, building={self.building}, room_number={self.room_number}, is_active={self.is_active})>"
