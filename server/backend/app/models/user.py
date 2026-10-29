from datetime import datetime
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, generate_uuid, utc_now
from backend.app.models.enums import UserRole


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    google_sub: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, native_enum=False, length=50),
        nullable=False,
        default=UserRole.FACULTY,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    # Relationships
    troubleshooting_sessions: Mapped[List["TroubleshootingSession"]] = relationship(
        "TroubleshootingSession",
        back_populates="faculty",
        cascade="all, delete-orphan",
    )
    reported_complaints: Mapped[List["Complaint"]] = relationship(
        "Complaint",
        foreign_keys="[Complaint.reported_by]",
        back_populates="reporter",
    )
    assigned_complaints: Mapped[List["Complaint"]] = relationship(
        "Complaint",
        foreign_keys="[Complaint.assigned_technician_id]",
        back_populates="technician",
    )
    repair_records: Mapped[List["RepairRecord"]] = relationship(
        "RepairRecord",
        foreign_keys="[RepairRecord.technician_id]",
        back_populates="technician",
    )
    verified_repairs: Mapped[List["RepairRecord"]] = relationship(
        "RepairRecord",
        foreign_keys="[RepairRecord.verified_by]",
        back_populates="verifier",
    )
    uploaded_documents: Mapped[List["KnowledgeDocument"]] = relationship(
        "KnowledgeDocument",
        back_populates="uploader",
    )
    device_changes: Mapped[List["DeviceHistory"]] = relationship(
        "DeviceHistory",
        back_populates="changer",
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="actor",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role}, is_active={self.is_active})>"
