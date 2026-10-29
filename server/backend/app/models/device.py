from datetime import datetime
from typing import List, Optional
from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, generate_uuid, utc_now
from backend.app.models.enums import DeviceStatus, DeviceType


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    classroom_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    device_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    brand: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    serial_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
    )
    status: Mapped[DeviceStatus] = mapped_column(
        SQLEnum(DeviceStatus, native_enum=False, length=50),
        nullable=False,
        default=DeviceStatus.OPERATIONAL,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    # Indexes
    __table_args__ = (
        Index("ix_devices_classroom_type", "classroom_id", "device_type"),
        Index("ix_devices_brand_model", "brand", "model"),
    )

    # Relationships
    classroom: Mapped["Classroom"] = relationship(
        "Classroom",
        back_populates="devices",
    )
    history: Mapped[List["DeviceHistory"]] = relationship(
        "DeviceHistory",
        back_populates="device",
        cascade="all, delete-orphan",
        order_by="desc(DeviceHistory.created_at)",
    )
    troubleshooting_sessions: Mapped[List["TroubleshootingSession"]] = relationship(
        "TroubleshootingSession",
        back_populates="device",
    )
    complaints: Mapped[List["Complaint"]] = relationship(
        "Complaint",
        back_populates="device",
    )

    def __repr__(self) -> str:
        return f"<Device(id={self.id}, type={self.device_type}, brand={self.brand}, model={self.model}, status={self.status})>"
