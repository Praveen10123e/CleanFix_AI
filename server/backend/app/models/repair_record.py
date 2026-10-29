from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, generate_uuid, utc_now


class RepairRecord(Base):
    __tablename__ = "repair_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    complaint_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    technician_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    confirmed_cause: Mapped[str] = mapped_column(Text, nullable=False)
    repair_action: Mapped[str] = mapped_column(Text, nullable=False)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parts_replaced: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verified_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    complaint: Mapped["Complaint"] = relationship(
        "Complaint",
        back_populates="repair_record",
    )
    technician: Mapped["User"] = relationship(
        "User",
        foreign_keys=[technician_id],
        back_populates="repair_records",
    )
    verifier: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[verified_by],
        back_populates="verified_repairs",
    )

    def __repr__(self) -> str:
        return f"<RepairRecord(id={self.id}, complaint_id={self.complaint_id}, technician_id={self.technician_id})>"
