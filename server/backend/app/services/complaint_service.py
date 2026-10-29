import logging
from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from backend.app.db.base import utc_now
from backend.app.models.audit_log import AuditLog
from backend.app.models.classroom import Classroom
from backend.app.models.complaint import Complaint
from backend.app.models.device import Device
from backend.app.models.device_history import DeviceHistory
from backend.app.models.enums import (
    ChangeType,
    ComplaintStatus,
    DeviceStatus,
    UserRole,
)
from backend.app.models.repair_record import RepairRecord
from backend.app.models.user import User
from backend.app.schemas.complaint import (
    ComplaintAssignmentUpdate,
    ComplaintCreate,
    ComplaintResolutionCreate,
    ComplaintStatusUpdate,
)

logger = logging.getLogger(__name__)

# Valid state transitions for complaints
VALID_TRANSITIONS = {
    ComplaintStatus.PENDING: {ComplaintStatus.ASSIGNED, ComplaintStatus.IN_PROGRESS, ComplaintStatus.CANCELLED},
    ComplaintStatus.ASSIGNED: {ComplaintStatus.IN_PROGRESS, ComplaintStatus.CANCELLED},
    ComplaintStatus.IN_PROGRESS: {ComplaintStatus.RESOLVED, ComplaintStatus.PENDING, ComplaintStatus.CANCELLED},
    ComplaintStatus.RESOLVED: set(),  # Terminal state
    ComplaintStatus.CANCELLED: set(), # Terminal state
}


class ComplaintService:
    """Service managing the full lifecycle of complaints and repair records."""

    def create_complaint(self, db: Session, user: User, payload: ComplaintCreate) -> Complaint:
        stmt_dev = select(Device).where(Device.id == payload.device_id)
        device = db.execute(stmt_dev).scalar_one_or_none()
        if not device:
            raise NotFoundException(message=f"Device '{payload.device_id}' not found.", details={"device_id": payload.device_id})

        classroom_id = payload.classroom_id or device.classroom_id
        stmt_cr = select(Classroom).where(Classroom.id == classroom_id)
        if not db.execute(stmt_cr).scalar_one_or_none():
            raise NotFoundException(message=f"Classroom '{classroom_id}' not found.", details={"classroom_id": classroom_id})

        complaint = Complaint(
            device_id=device.id,
            classroom_id=classroom_id,
            reported_by=user.id,
            description=payload.description.strip(),
            priority=payload.priority.strip() if payload.priority else "MEDIUM",
            status=ComplaintStatus.PENDING,
            created_at=utc_now(),
        )
        db.add(complaint)
        db.flush()

        # Update device status if operational
        if device.status == DeviceStatus.OPERATIONAL:
            device.status = DeviceStatus.FAULTY
            hist = DeviceHistory(
                device_id=device.id,
                changed_by=user.id,
                change_type=ChangeType.STATUS_CHANGE.value,
                previous_values={"status": DeviceStatus.OPERATIONAL.value},
                new_values={"status": DeviceStatus.FAULTY.value},
            )
            db.add(hist)

        audit = AuditLog(
            actor_id=user.id,
            action="COMPLAINT_CREATED",
            entity_type="COMPLAINT",
            entity_id=complaint.id,
        )
        db.add(audit)
        db.commit()
        db.refresh(complaint)

        logger.info("Complaint created: %s for device %s by %s", complaint.id, device.id, user.email)
        return complaint

    def list_complaints(
        self,
        db: Session,
        user: User,
        status_filter: Optional[ComplaintStatus] = None,
        classroom_id: Optional[str] = None,
        device_id: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to_me: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Complaint], int]:
        stmt = select(Complaint)
        count_stmt = select(func.count(Complaint.id))

        # Role-based visibility
        if user.role == UserRole.FACULTY:
            # Faculty only see their own reported complaints
            stmt = stmt.where(Complaint.reported_by == user.id)
            count_stmt = count_stmt.where(Complaint.reported_by == user.id)
        elif user.role == UserRole.TECHNICIAN:
            if assigned_to_me is True:
                stmt = stmt.where(Complaint.assigned_technician_id == user.id)
                count_stmt = count_stmt.where(Complaint.assigned_technician_id == user.id)

        # Common filters
        if status_filter:
            stmt = stmt.where(Complaint.status == status_filter)
            count_stmt = count_stmt.where(Complaint.status == status_filter)
        if classroom_id:
            stmt = stmt.where(Complaint.classroom_id == classroom_id)
            count_stmt = count_stmt.where(Complaint.classroom_id == classroom_id)
        if device_id:
            stmt = stmt.where(Complaint.device_id == device_id)
            count_stmt = count_stmt.where(Complaint.device_id == device_id)
        if priority:
            stmt = stmt.where(Complaint.priority == priority.strip())
            count_stmt = count_stmt.where(Complaint.priority == priority.strip())

        total = db.execute(count_stmt).scalar_one()
        complaints = db.execute(
            stmt.order_by(Complaint.created_at.desc()).limit(limit).offset(offset)
        ).scalars().all()

        return complaints, total

    def get_complaint(self, db: Session, user: User, complaint_id: str) -> Complaint:
        stmt = select(Complaint).where(Complaint.id == complaint_id)
        complaint = db.execute(stmt).scalar_one_or_none()
        if not complaint:
            raise NotFoundException(message=f"Complaint '{complaint_id}' not found.", details={"complaint_id": complaint_id})

        # Role-based visibility check
        if user.role == UserRole.FACULTY and complaint.reported_by != user.id:
            raise ForbiddenException(
                message="You can only access complaints reported by you.",
                details={"complaint_id": complaint_id},
            )

        return complaint

    def assign_complaint(
        self,
        db: Session,
        admin_user: User,
        complaint_id: str,
        payload: ComplaintAssignmentUpdate,
    ) -> Complaint:
        stmt = select(Complaint).where(Complaint.id == complaint_id)
        complaint = db.execute(stmt).scalar_one_or_none()
        if not complaint:
            raise NotFoundException(message=f"Complaint '{complaint_id}' not found.", details={"complaint_id": complaint_id})

        # Verify technician exists, is technician, and is active
        stmt_tech = select(User).where(User.id == payload.technician_id)
        tech = db.execute(stmt_tech).scalar_one_or_none()
        if not tech or tech.role != UserRole.TECHNICIAN:
            raise BadRequestException(
                message=f"User '{payload.technician_id}' is not an active technician.",
                details={"technician_id": payload.technician_id},
            )
        if not tech.is_active:
            raise BadRequestException(
                message=f"Technician '{tech.name}' is deactivated.",
                details={"technician_id": payload.technician_id},
            )

        complaint.assigned_technician_id = tech.id
        complaint.status = ComplaintStatus.ASSIGNED
        complaint.assigned_at = utc_now()

        audit = AuditLog(
            actor_id=admin_user.id,
            action="COMPLAINT_ASSIGNED",
            entity_type="COMPLAINT",
            entity_id=complaint.id,
        )
        db.add(audit)
        db.commit()
        db.refresh(complaint)

        logger.info("Complaint %s assigned to technician %s by %s", complaint.id, tech.email, admin_user.email)
        return complaint

    def update_complaint_status(
        self,
        db: Session,
        user: User,
        complaint_id: str,
        payload: ComplaintStatusUpdate,
    ) -> Complaint:
        stmt = select(Complaint).where(Complaint.id == complaint_id)
        complaint = db.execute(stmt).scalar_one_or_none()
        if not complaint:
            raise NotFoundException(message=f"Complaint '{complaint_id}' not found.", details={"complaint_id": complaint_id})

        # Technicians can only update complaints assigned to them
        if user.role == UserRole.TECHNICIAN and complaint.assigned_technician_id != user.id:
            raise ForbiddenException(
                message="You can only update complaints assigned to you.",
                details={"complaint_id": complaint_id, "assigned_technician_id": complaint.assigned_technician_id},
            )

        # Validate legal transition
        allowed_next = VALID_TRANSITIONS.get(complaint.status, set())
        if payload.status not in allowed_next and user.role != UserRole.ADMIN:
            raise BadRequestException(
                message=f"Invalid complaint status transition from '{complaint.status.value}' to '{payload.status.value}'.",
                details={
                    "current_status": complaint.status.value,
                    "target_status": payload.status.value,
                    "allowed_transitions": [s.value for s in allowed_next],
                },
            )

        complaint.status = payload.status
        audit = AuditLog(
            actor_id=user.id,
            action="COMPLAINT_STATUS_UPDATED",
            entity_type="COMPLAINT",
            entity_id=complaint.id,
        )
        db.add(audit)
        db.commit()
        db.refresh(complaint)

        logger.info("Complaint %s status updated to %s by %s", complaint.id, payload.status.value, user.email)
        return complaint

    def resolve_complaint(
        self,
        db: Session,
        user: User,
        complaint_id: str,
        payload: ComplaintResolutionCreate,
    ) -> Complaint:
        stmt = select(Complaint).where(Complaint.id == complaint_id)
        complaint = db.execute(stmt).scalar_one_or_none()
        if not complaint:
            raise NotFoundException(message=f"Complaint '{complaint_id}' not found.", details={"complaint_id": complaint_id})

        # Authorization: must be assigned technician or Admin
        if user.role == UserRole.TECHNICIAN and complaint.assigned_technician_id != user.id:
            raise ForbiddenException(
                message="You can only submit resolution for complaints assigned to you.",
                details={"complaint_id": complaint_id},
            )

        # Check if already resolved / repair record exists
        if complaint.repair_record is not None:
            raise ConflictException(
                message="A repair record has already been filed for this complaint.",
                details={"repair_record_id": complaint.repair_record.id},
            )

        # 1. Create RepairRecord
        repair = RepairRecord(
            complaint_id=complaint.id,
            technician_id=user.id,
            confirmed_cause=payload.confirmed_cause.strip(),
            repair_action=payload.repair_action.strip(),
            resolution_notes=payload.resolution_notes.strip() if payload.resolution_notes else None,
            parts_replaced=payload.parts_replaced.strip() if payload.parts_replaced else None,
            verified_by=None,
            created_at=utc_now(),
        )
        db.add(repair)

        # 2. Update Complaint
        complaint.status = ComplaintStatus.RESOLVED
        complaint.resolved_at = utc_now()

        # 3. Restore device status to OPERATIONAL
        stmt_dev = select(Device).where(Device.id == complaint.device_id)
        device = db.execute(stmt_dev).scalar_one_or_none()
        if device:
            prev_status = device.status.value
            device.status = DeviceStatus.OPERATIONAL
            hist = DeviceHistory(
                device_id=device.id,
                changed_by=user.id,
                change_type=ChangeType.REPAIRED.value,
                previous_values={"status": prev_status},
                new_values={
                    "status": DeviceStatus.OPERATIONAL.value,
                    "repair_record_id": repair.id,
                    "cause": payload.confirmed_cause,
                },
            )
            db.add(hist)

        # 4. Audit Log
        audit = AuditLog(
            actor_id=user.id,
            action="COMPLAINT_RESOLVED",
            entity_type="COMPLAINT",
            entity_id=complaint.id,
        )
        db.add(audit)
        db.commit()
        db.refresh(complaint)

        logger.info("Complaint %s resolved by technician %s", complaint.id, user.email)
        return complaint


complaint_service = ComplaintService()

