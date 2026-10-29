from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, generate_uuid, utc_now
from backend.app.models.enums import StepResult, TroubleshootingStatus


class TroubleshootingSession(Base):
    __tablename__ = "troubleshooting_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    faculty_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    device_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("devices.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    symptom_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[TroubleshootingStatus] = mapped_column(
        SQLEnum(TroubleshootingStatus, native_enum=False, length=50),
        nullable=False,
        default=TroubleshootingStatus.IN_PROGRESS,
        index=True,
    )
    current_step: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    faculty: Mapped["User"] = relationship(
        "User",
        back_populates="troubleshooting_sessions",
    )
    device: Mapped["Device"] = relationship(
        "Device",
        back_populates="troubleshooting_sessions",
    )
    steps: Mapped[List["TroubleshootingStep"]] = relationship(
        "TroubleshootingStep",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="TroubleshootingStep.step_number",
    )
    complaint: Mapped[Optional["Complaint"]] = relationship(
        "Complaint",
        back_populates="session",
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"<TroubleshootingSession(id={self.id}, device_id={self.device_id}, status={self.status})>"


class TroubleshootingStep(Base):
    __tablename__ = "troubleshooting_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("troubleshooting_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    instruction: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_refs: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    result: Mapped[Optional[StepResult]] = mapped_column(
        SQLEnum(StepResult, native_enum=False, length=50),
        nullable=True,
    )
    result_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("session_id", "step_number", name="uq_session_step_number"),
    )

    # Relationships
    session: Mapped["TroubleshootingSession"] = relationship(
        "TroubleshootingSession",
        back_populates="steps",
    )

    def __repr__(self) -> str:
        return f"<TroubleshootingStep(id={self.id}, session_id={self.session_id}, step={self.step_number}, result={self.result})>"
