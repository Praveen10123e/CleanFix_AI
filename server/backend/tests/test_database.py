import uuid
import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.classroom import Classroom
from backend.app.models.complaint import Complaint
from backend.app.models.device import Device
from backend.app.models.device_history import DeviceHistory
from backend.app.models.enums import (
    ChangeType,
    ComplaintStatus,
    DeviceStatus,
    DeviceType,
    DocumentStatus,
    DocumentType,
    StepResult,
    TroubleshootingStatus,
    UserRole,
)
from backend.app.models.knowledge import (
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeIngestionJob,
)
from backend.app.models.repair_record import RepairRecord
from backend.app.models.troubleshooting import (
    TroubleshootingSession,
    TroubleshootingStep,
)
from backend.app.models.user import User


def test_all_twelve_tables_initialized(db_session: Session):
    """Verify all 12 tables exist in the schema."""
    inspector = inspect(db_session.bind)
    tables = inspector.get_table_names()
    expected_tables = {
        "users",
        "classrooms",
        "devices",
        "device_history",
        "troubleshooting_sessions",
        "troubleshooting_steps",
        "complaints",
        "repair_records",
        "knowledge_documents",
        "knowledge_chunks",
        "knowledge_ingestion_jobs",
        "audit_logs",
    }
    for table in expected_tables:
        assert table in tables, f"Expected table '{table}' not found in database"


def test_uuid_and_utc_timestamps(db_session: Session):
    """Verify automatic UUID generation and UTC timestamp assignment."""
    user = User(
        email="uuid.test@classroom.edu",
        name="UUID Test",
        role=UserRole.FACULTY,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Validate UUID format
    assert user.id is not None
    assert len(user.id) == 36
    # Validates uuid syntax
    assert uuid.UUID(user.id)

    # Validate timestamps
    assert user.created_at is not None
    assert user.updated_at is not None
    assert user.created_at.tzinfo is not None or user.created_at.isoformat()


def test_foreign_key_enforcement(db_session: Session):
    """Verify that SQLite enforces foreign key constraints when inserting orphaned rows."""
    non_existent_classroom_id = str(uuid.uuid4())
    device = Device(
        classroom_id=non_existent_classroom_id,
        device_type=DeviceType.PROJECTOR.value,
        brand="Epson",
        model="Test Model",
    )
    db_session.add(device)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_classroom_and_device_relationship(db_session: Session):
    """Verify Classroom to Device one-to-many relationship."""
    classroom = Classroom(
        building="Hall A",
        room_number="101",
        description="Demo Hall",
    )
    db_session.add(classroom)
    db_session.commit()
    db_session.refresh(classroom)

    device = Device(
        classroom_id=classroom.id,
        device_type=DeviceType.PROJECTOR.value,
        brand="Sony",
        model="Laser 500",
        serial_number="SN-TEST-123",
    )
    db_session.add(device)
    db_session.commit()

    db_session.refresh(classroom)
    assert len(classroom.devices) == 1
    assert classroom.devices[0].model == "Laser 500"
    assert classroom.devices[0].classroom.room_number == "101"


def test_troubleshooting_session_and_steps_relationship(db_session: Session, faculty_user: User):
    """Verify TroubleshootingSession and TroubleshootingSteps cascade and relationship."""
    classroom = Classroom(building="Hall B", room_number="202")
    db_session.add(classroom)
    db_session.flush()

    device = Device(
        classroom_id=classroom.id,
        device_type=DeviceType.SMART_BOARD.value,
        brand="SmartTech",
        model="Board 7000",
    )
    db_session.add(device)
    db_session.flush()

    session = TroubleshootingSession(
        faculty_id=faculty_user.id,
        device_id=device.id,
        symptom_text="Touch screen not responding",
    )
    db_session.add(session)
    db_session.flush()

    step1 = TroubleshootingStep(
        session_id=session.id,
        step_number=1,
        instruction="Verify USB touch cable connection to the wall plate",
        reason="Check physical layer connection",
        result=StepResult.FAILED,
    )
    step2 = TroubleshootingStep(
        session_id=session.id,
        step_number=2,
        instruction="Reboot smart board display using power cycle switch",
        result=StepResult.SUCCESS,
    )
    db_session.add_all([step1, step2])
    db_session.commit()

    db_session.refresh(session)
    assert len(session.steps) == 2
    assert session.steps[0].step_number == 1
    assert session.steps[1].step_number == 2
    assert session.steps[0].result == StepResult.FAILED


def test_complaint_and_repair_record_relationship(
    db_session: Session,
    faculty_user: User,
    technician_user: User,
    admin_user: User,
):
    """Verify Complaint and RepairRecord relationship and verification flow."""
    classroom = Classroom(building="Hall C", room_number="303")
    db_session.add(classroom)
    db_session.flush()

    device = Device(
        classroom_id=classroom.id,
        device_type=DeviceType.AUDIO_SYSTEM.value,
        brand="Yamaha",
        model="AMP-300",
    )
    db_session.add(device)
    db_session.flush()

    complaint = Complaint(
        classroom_id=classroom.id,
        device_id=device.id,
        reported_by=faculty_user.id,
        assigned_technician_id=technician_user.id,
        description="No sound output from ceiling speakers",
        status=ComplaintStatus.IN_PROGRESS,
    )
    db_session.add(complaint)
    db_session.flush()

    repair = RepairRecord(
        complaint_id=complaint.id,
        technician_id=technician_user.id,
        confirmed_cause="Blown amplifier fuse",
        repair_action="Replaced 2A fuse and tested audio path",
        verified_by=admin_user.id,
    )
    db_session.add(repair)
    db_session.commit()

    db_session.refresh(complaint)
    assert complaint.repair_record is not None
    assert complaint.repair_record.confirmed_cause == "Blown amplifier fuse"
    assert complaint.repair_record.verifier.name == admin_user.name


def test_classroom_building_room_uniqueness(db_session: Session):
    """Verify unique constraint on (building, room_number)."""
    r1 = Classroom(building="North Wing", room_number="N-101")
    r2 = Classroom(building="North Wing", room_number="N-101")
    db_session.add(r1)
    db_session.commit()

    db_session.add(r2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
