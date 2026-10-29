from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, generate_uuid, utc_now
from backend.app.models.enums import ComplaintStatus


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    session_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("troubleshooting_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    device_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("devices.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    classroom_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("classrooms.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    reported_by: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    assigned_technician_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(50), default="MEDIUM", nullable=False, index=True)
    status: Mapped[ComplaintStatus] = mapped_column(
        SQLEnum(ComplaintStatus, native_enum=False, length=50),
        nullable=False,
        default=ComplaintStatus.PENDING,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    session: Mapped[Optional["TroubleshootingSession"]] = relationship(
        "TroubleshootingSession",
        back_populates="complaint",
    )
    device: Mapped["Device"] = relationship(
        "Device",
        back_populates="complaints",
    )
    classroom: Mapped["Classroom"] = relationship(
        "Classroom",
        back_populates="complaints",
    )
    reporter: Mapped["User"] = relationship(
        "User",
        foreign_keys=[reported_by],
        back_populates="reported_complaints",
    )
    technician: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[assigned_technician_id],
        back_populates="assigned_complaints",
    )
    repair_record: Mapped[Optional["RepairRecord"]] = relationship(
        "RepairRecord",
        back_populates="complaint",
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"<Complaint(id={self.id}, device_id={self.device_id}, status={self.status})>"
