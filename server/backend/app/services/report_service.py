import logging
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from backend.app.models.classroom import Classroom
from backend.app.models.complaint import Complaint
from backend.app.models.device import Device
from backend.app.models.enums import ComplaintStatus, DeviceStatus
from backend.app.models.repair_record import RepairRecord
from backend.app.models.troubleshooting import TroubleshootingSession
from backend.app.schemas.report import ReportSummaryData

logger = logging.getLogger(__name__)


def generate_report_summary(db: Session) -> ReportSummaryData:
    """Generate dynamic database-derived metrics across rooms, inventory, complaints, and repairs."""
    # 1. Classrooms
    total_active_classrooms = db.execute(
        select(func.count(Classroom.id)).where(Classroom.is_active.is_(True))
    ).scalar_one()

    # 2. Devices
    total_active_devices = db.execute(
        select(func.count(Device.id)).where(Device.status != DeviceStatus.DECOMMISSIONED)
    ).scalar_one()

    # Device counts by category
    cat_rows = db.execute(
        select(Device.device_type, func.count(Device.id)).group_by(Device.device_type)
    ).all()
    device_counts_by_category = {str(row[0]): int(row[1]) for row in cat_rows}

    # Device counts by brand
    brand_rows = db.execute(
        select(Device.brand, func.count(Device.id)).group_by(Device.brand)
    ).all()
    device_counts_by_brand = {str(row[0]): int(row[1]) for row in brand_rows}

    # Device counts by status
    status_rows = db.execute(
        select(Device.status, func.count(Device.id)).group_by(Device.status)
    ).all()
    device_counts_by_status = {
        (row[0].value if hasattr(row[0], "value") else str(row[0])): int(row[1]) for row in status_rows
    }

    # 3. Complaints
    total_complaints = db.execute(select(func.count(Complaint.id))).scalar_one()

    open_statuses = [ComplaintStatus.PENDING, ComplaintStatus.ASSIGNED, ComplaintStatus.IN_PROGRESS]
    open_complaints = db.execute(
        select(func.count(Complaint.id)).where(Complaint.status.in_(open_statuses))
    ).scalar_one()

    complaint_status_rows = db.execute(
        select(Complaint.status, func.count(Complaint.id)).group_by(Complaint.status)
    ).all()
    complaints_by_status = {
        (row[0].value if hasattr(row[0], "value") else str(row[0])): int(row[1]) for row in complaint_status_rows
    }

    complaint_priority_rows = db.execute(
        select(Complaint.priority, func.count(Complaint.id)).group_by(Complaint.priority)
    ).all()
    complaints_by_priority = {str(row[0]): int(row[1]) for row in complaint_priority_rows}

    assigned_complaints = db.execute(
        select(func.count(Complaint.id)).where(Complaint.assigned_technician_id.isnot(None))
    ).scalar_one()

    unassigned_complaints = db.execute(
        select(func.count(Complaint.id)).where(Complaint.assigned_technician_id.is_(None))
    ).scalar_one()

    # 4. Repairs
    completed_repairs = db.execute(select(func.count(RepairRecord.id))).scalar_one()

    # 5. Common reported symptoms
    symptom_rows = db.execute(
        select(TroubleshootingSession.symptom_text, func.count(TroubleshootingSession.id))
        .group_by(TroubleshootingSession.symptom_text)
        .order_by(desc(func.count(TroubleshootingSession.id)))
        .limit(5)
    ).all()
    common_symptoms = [{"symptom": str(row[0]), "count": int(row[1])} for row in symptom_rows]

    # 6. Recent complaints
    recent_complaint_rows = db.execute(
        select(Complaint).order_by(desc(Complaint.created_at)).limit(5)
    ).scalars().all()

    recent_complaints = [
        {
            "id": c.id,
            "classroom_id": c.classroom_id,
            "device_id": c.device_id,
            "description": c.description,
            "priority": c.priority,
            "status": c.status.value,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in recent_complaint_rows
    ]

    return ReportSummaryData(
        total_active_classrooms=total_active_classrooms,
        total_active_devices=total_active_devices,
        device_counts_by_category=device_counts_by_category,
        device_counts_by_brand=device_counts_by_brand,
        device_counts_by_status=device_counts_by_status,
        total_complaints=total_complaints,
        open_complaints=open_complaints,
        complaints_by_status=complaints_by_status,
        complaints_by_priority=complaints_by_priority,
        assigned_complaints=assigned_complaints,
        unassigned_complaints=unassigned_complaints,
        completed_repairs=completed_repairs,
        common_symptoms=common_symptoms,
        recent_complaints=recent_complaints,
    )

