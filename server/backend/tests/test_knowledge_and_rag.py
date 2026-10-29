import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.classroom import Classroom
from backend.app.models.complaint import Complaint
from backend.app.models.device import Device
from backend.app.models.enums import ComplaintStatus, DeviceStatus, DeviceType, DocumentType, StepResult, TroubleshootingStatus, UserRole
from backend.app.models.repair_record import RepairRecord
from backend.app.models.troubleshooting import TroubleshootingSession, TroubleshootingStep
from backend.app.models.user import User
from backend.app.services.rag_interface import (
    RAGTroubleshootingContext,
    StubRAGDiagnosticService,
    build_rag_troubleshooting_context,
)


def test_knowledge_metadata_endpoints(
    client: TestClient,
    technician_token: str,
    faculty_token: str,
):
    # 1. Faculty cannot create knowledge metadata (Technician or Admin only)
    res_fac = client.post(
        "/api/v1/knowledge/documents",
        json={
            "document_type": DocumentType.MANUAL.value,
            "title": "Epson PowerLite L615U User Manual",
            "device_type": DeviceType.PROJECTOR.value,
            "brand": "Epson",
            "model": "PowerLite L615U",
            "file_path": "manuals/epson_l615u.pdf",
        },
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert res_fac.status_code == 403

    # 2. Technician creates knowledge document metadata
    res_tech = client.post(
        "/api/v1/knowledge/documents",
        json={
            "document_type": DocumentType.MANUAL.value,
            "title": "Epson PowerLite L615U User Manual",
            "device_type": DeviceType.PROJECTOR.value,
            "brand": "Epson",
            "model": "PowerLite L615U",
            "file_path": "manuals/epson_l615u.pdf",
        },
        headers={"Authorization": f"Bearer {technician_token}"},
    )
    assert res_tech.status_code == 201
    doc_data = res_tech.json()["data"]
    doc_id = doc_data["id"]
    assert doc_data["title"] == "Epson PowerLite L615U User Manual"
    assert doc_data["status"] == "PENDING"

    # 3. Faculty can list and retrieve document metadata
    res_list = client.get(
        "/api/v1/knowledge/documents",
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert res_list.status_code == 200
    assert len(res_list.json()["data"]) >= 1

    res_get = client.get(
        f"/api/v1/knowledge/documents/{doc_id}",
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert res_get.status_code == 200
    assert res_get.json()["data"]["id"] == doc_id


def test_future_rag_interface_context_builder_and_stub(db_session: Session):
    """Verify that build_rag_troubleshooting_context correctly gathers and serializes all required metadata."""
    cr = Classroom(building="Academic Tower", room_number="101", is_active=True)
    db_session.add(cr)
    db_session.flush()

    dev = Device(
        classroom_id=cr.id,
        device_type=DeviceType.PROJECTOR.value,
        brand="Epson",
        model="PowerLite L615U",
        serial_number="RAG-SN-999",
        status=DeviceStatus.FAULTY,
    )
    db_session.add(dev)
    db_session.flush()

    faculty = User(email="prof.test@classroom.edu", name="Prof Test", role=UserRole.FACULTY, is_active=True)
    tech = User(email="tech.test@classroom.edu", name="Tech Test", role=UserRole.TECHNICIAN, is_active=True)
    db_session.add_all([faculty, tech])
    db_session.flush()

    # Create previous repair history
    old_complaint = Complaint(
        device_id=dev.id,
        classroom_id=cr.id,
        reported_by=faculty.id,
        description="Filter clogged",
        status=ComplaintStatus.RESOLVED,
    )
    db_session.add(old_complaint)
    db_session.flush()

    old_repair = RepairRecord(
        complaint_id=old_complaint.id,
        technician_id=tech.id,
        confirmed_cause="Dust buildup on intake filter",
        repair_action="Cleaned electrostatic filter and reset timer",
        parts_replaced="Filter foam pad",
    )
    db_session.add(old_repair)
    db_session.flush()

    # Active troubleshooting session with completed step
    session = TroubleshootingSession(
        faculty_id=faculty.id,
        device_id=dev.id,
        symptom_text="Projector turns off after 5 minutes with amber warning light",
        status=TroubleshootingStatus.IN_PROGRESS,
        current_step=2,
    )
    db_session.add(session)
    db_session.flush()

    step1 = TroubleshootingStep(
        session_id=session.id,
        step_number=1,
        instruction="Verify ventilation clearance around projector vents",
        reason="Prevents thermal shutdown",
        result=StepResult.FAILED,
        result_note="Ventilation is clear but amber light stays on",
    )
    db_session.add(step1)
    db_session.commit()

    # 1. Build RAG context
    rag_context = build_rag_troubleshooting_context(db_session, session.id)

    assert isinstance(rag_context, RAGTroubleshootingContext)
    assert rag_context.session_id == session.id
    assert rag_context.symptom_text == "Projector turns off after 5 minutes with amber warning light"
    assert rag_context.device.brand == "Epson"
    assert rag_context.device.model == "PowerLite L615U"
    assert rag_context.device.classroom_room_number == "101"
    assert len(rag_context.previous_steps) == 1
    assert rag_context.previous_steps[0].result == "FAILED"
    assert len(rag_context.repair_history) == 1
    assert rag_context.repair_history[0].confirmed_cause == "Dust buildup on intake filter"

    # 2. Test Stub Service
    stub_service = StubRAGDiagnosticService()
    diag_result = stub_service.generate_diagnostic_step(rag_context)
    assert diag_result.session_id == session.id
    assert diag_result.recommended_action == "EXECUTE_STEP"
    assert diag_result.confidence_score == 1.0

    evidence = stub_service.retrieve_evidence("amber light", rag_context.device)
    assert evidence["status"] == "RAG_NOT_CONFIGURED"

