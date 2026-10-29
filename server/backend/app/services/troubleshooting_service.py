import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from backend.app.db.base import utc_now
from backend.app.models.audit_log import AuditLog
from backend.app.models.complaint import Complaint
from backend.app.models.device import Device
from backend.app.models.device_history import DeviceHistory
from backend.app.models.enums import (
    ChangeType,
    ComplaintStatus,
    DeviceStatus,
    StepResult,
    TroubleshootingStatus,
    UserRole,
)
from backend.app.models.troubleshooting import (
    TroubleshootingSession,
    TroubleshootingStep,
)
from backend.app.models.user import User
from backend.app.schemas.troubleshooting import (
    StepResultSubmit,
    TroubleshootingComplaintCreate,
    TroubleshootingSessionCreate,
)
from backend.app.services.troubleshooting_catalogue import get_troubleshooting_steps

logger = logging.getLogger(__name__)


def verify_session_access(session: TroubleshootingSession, user: User) -> None:
    """Ensure user owns the session or has administrator privileges."""
    if user.role != UserRole.ADMIN and session.faculty_id != user.id:
        raise ForbiddenException(
            message="Access forbidden: you can only view or manage your own troubleshooting sessions.",
            details={"session_id": session.id, "user_id": user.id},
        )


class TroubleshootingService:
    """Service handling troubleshooting sessions and guided step workflows."""

    def create_session(
        self,
        db: Session,
        user: User,
        payload: TroubleshootingSessionCreate,
    ) -> TroubleshootingSession:
        # Verify target device exists
        stmt_dev = select(Device).where(Device.id == payload.device_id)
        device = db.execute(stmt_dev).scalar_one_or_none()
        if not device:
            raise NotFoundException(
                message=f"Device with ID '{payload.device_id}' not found.",
                details={"device_id": payload.device_id},
            )

        # 1. Create TroubleshootingSession record
        session = TroubleshootingSession(
            faculty_id=user.id,
            device_id=device.id,
            symptom_text=payload.symptom_text.strip(),
            status=TroubleshootingStatus.IN_PROGRESS,
            current_step=1,
            started_at=utc_now(),
        )
        db.add(session)
        db.flush()

        # 2. Retrieve catalogue steps
        catalogue_steps = get_troubleshooting_steps(device.device_type, payload.symptom_text)

        # 3. Insert Step 1
        first_step_def = catalogue_steps[0] if catalogue_steps else {
            "step_number": 1,
            "instruction": "Verify device power and cable seating.",
            "reason": "Basic diagnostic check.",
            "source_refs": {},
        }

        step1 = TroubleshootingStep(
            session_id=session.id,
            step_number=1,
            instruction=first_step_def["instruction"],
            reason=first_step_def.get("reason"),
            source_refs=first_step_def.get("source_refs"),
            result=None,
            result_note=None,
            created_at=utc_now(),
        )
        db.add(step1)
        db.flush()

        # 4. Audit Log
        audit = AuditLog(
            actor_id=user.id,
            action="TROUBLESHOOTING_SESSION_STARTED",
            entity_type="TROUBLESHOOTING_SESSION",
            entity_id=session.id,
        )
        db.add(audit)
        db.commit()
        db.refresh(session)

        logger.info("Troubleshooting session created: %s for device %s by %s", session.id, device.id, user.email)
        return session

    def get_next_step(
        self,
        db: Session,
        user: User,
        session_id: str,
    ) -> TroubleshootingStep:
        stmt = select(TroubleshootingSession).where(TroubleshootingSession.id == session_id)
        session = db.execute(stmt).scalar_one_or_none()
        if not session:
            raise NotFoundException(message=f"Session '{session_id}' not found.", details={"session_id": session_id})

        verify_session_access(session, user)

        if session.status != TroubleshootingStatus.IN_PROGRESS:
            raise BadRequestException(
                message=f"Cannot advance session: current status is '{session.status.value}'.",
                details={"session_status": session.status.value},
            )

        # Find latest step in DB
        stmt_steps = select(TroubleshootingStep).where(
            TroubleshootingStep.session_id == session.id
        ).order_by(TroubleshootingStep.step_number.desc())
        steps = db.execute(stmt_steps).scalars().all()

        if not steps:
            raise NotFoundException("No steps recorded for this session.")

        latest_step = steps[0]

        # If latest step has not been recorded, return it
        if latest_step.result is None:
            return latest_step

        # If latest step has a result, find next step from catalogue
        target_step_num = latest_step.step_number + 1
        catalogue_steps = get_troubleshooting_steps(session.device.device_type, session.symptom_text)

        matching_def = next((s for s in catalogue_steps if s["step_number"] == target_step_num), None)
        if not matching_def:
            raise BadRequestException(
                message="All available guided troubleshooting steps have been completed. If the issue remains unresolved, please escalate to an AV technician complaint.",
                details={"steps_completed": len(steps)},
            )

        new_step = TroubleshootingStep(
            session_id=session.id,
            step_number=target_step_num,
            instruction=matching_def["instruction"],
            reason=matching_def.get("reason"),
            source_refs=matching_def.get("source_refs"),
            result=None,
            result_note=None,
            created_at=utc_now(),
        )
        db.add(new_step)
        session.current_step = target_step_num
        db.commit()
        db.refresh(new_step)

        return new_step

    def record_step_result(
        self,
        db: Session,
        user: User,
        session_id: str,
        step_id: str,
        payload: StepResultSubmit,
    ) -> TroubleshootingStep:
        stmt_session = select(TroubleshootingSession).where(TroubleshootingSession.id == session_id)
        session = db.execute(stmt_session).scalar_one_or_none()
        if not session:
            raise NotFoundException(message=f"Session '{session_id}' not found.", details={"session_id": session_id})

        verify_session_access(session, user)

        stmt_step = select(TroubleshootingStep).where(
            TroubleshootingStep.id == step_id,
            TroubleshootingStep.session_id == session.id,
        )
        step = db.execute(stmt_step).scalar_one_or_none()
        if not step:
            raise NotFoundException(message=f"Step '{step_id}' not found in session '{session_id}'.", details={"step_id": step_id})

        # Record outcome
        step.result = payload.result
        step.result_note = payload.result_note.strip() if payload.result_note else None
        step.completed_at = utc_now()

        db.commit()
        db.refresh(step)

        logger.info("Step %s result logged: %s for session %s", step.step_number, step.result.value, session.id)
        return step

    def complete_session(
        self,
        db: Session,
        user: User,
        session_id: str,
    ) -> TroubleshootingSession:
        stmt = select(TroubleshootingSession).where(TroubleshootingSession.id == session_id)
        session = db.execute(stmt).scalar_one_or_none()
        if not session:
            raise NotFoundException(message=f"Session '{session_id}' not found.", details={"session_id": session_id})

        verify_session_access(session, user)

        session.status = TroubleshootingStatus.RESOLVED
        session.ended_at = utc_now()

        audit = AuditLog(
            actor_id=user.id,
            action="TROUBLESHOOTING_SESSION_RESOLVED",
            entity_type="TROUBLESHOOTING_SESSION",
            entity_id=session.id,
        )
        db.add(audit)
        db.commit()
        db.refresh(session)

        logger.info("Troubleshooting session %s marked RESOLVED by %s", session.id, user.email)
        return session

    def escalate_to_complaint(
        self,
        db: Session,
        user: User,
        session_id: str,
        payload: TroubleshootingComplaintCreate,
    ) -> Complaint:
        stmt = select(TroubleshootingSession).where(TroubleshootingSession.id == session_id)
        session = db.execute(stmt).scalar_one_or_none()
        if not session:
            raise NotFoundException(message=f"Session '{session_id}' not found.", details={"session_id": session_id})

        verify_session_access(session, user)

        # Check if already escalated
        if session.status == TroubleshootingStatus.ESCALATED_TO_COMPLAINT:
            stmt_comp = select(Complaint).where(Complaint.session_id == session.id)
            existing_complaint = db.execute(stmt_comp).scalar_one_or_none()
            if existing_complaint:
                return existing_complaint

        # End session
        session.status = TroubleshootingStatus.ESCALATED_TO_COMPLAINT
        session.ended_at = utc_now()

        desc_text = payload.description.strip() if payload.description else f"Troubleshooting unresolved: {session.symptom_text}"

        complaint = Complaint(
            session_id=session.id,
            device_id=session.device_id,
            classroom_id=session.device.classroom_id,
            reported_by=user.id,
            description=desc_text,
            priority=payload.priority or "MEDIUM",
            status=ComplaintStatus.PENDING,
            created_at=utc_now(),
        )
        db.add(complaint)
        db.flush()

        # Update device status if operational
        if session.device.status == DeviceStatus.OPERATIONAL:
            session.device.status = DeviceStatus.FAULTY
            hist = DeviceHistory(
                device_id=session.device.id,
                changed_by=user.id,
                change_type=ChangeType.STATUS_CHANGE.value,
                previous_values={"status": DeviceStatus.OPERATIONAL.value},
                new_values={"status": DeviceStatus.FAULTY.value},
            )
            db.add(hist)

        # Audit Log
        audit = AuditLog(
            actor_id=user.id,
            action="COMPLAINT_CREATED_FROM_TROUBLESHOOTING",
            entity_type="COMPLAINT",
            entity_id=complaint.id,
        )
        db.add(audit)
        db.commit()
        db.refresh(complaint)

        logger.info("Session %s escalated to complaint %s by %s", session.id, complaint.id, user.email)
        return complaint


troubleshooting_service = TroubleshootingService()

