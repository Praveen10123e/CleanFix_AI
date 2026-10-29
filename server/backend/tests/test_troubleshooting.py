import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token
from backend.app.models.classroom import Classroom
from backend.app.models.complaint import Complaint
from backend.app.models.device import Device
from backend.app.models.enums import ComplaintStatus, DeviceStatus, DeviceType, StepResult, TroubleshootingStatus, UserRole
from backend.app.models.troubleshooting import TroubleshootingSession, TroubleshootingStep
from backend.app.models.user import User


@pytest.fixture
def sample_device(db_session: Session) -> Device:
    classroom = Classroom(building="Main Academic Block", room_number="001", description="Smart Hall", is_active=True)
    db_session.add(classroom)
    db_session.commit()
    db_session.refresh(classroom)

    device = Device(
        classroom_id=classroom.id,
        device_type=DeviceType.PROJECTOR.value,
        brand="Epson",
        model="PowerLite L615U",
        serial_number="DEMO-PRJ-001",
        status=DeviceStatus.OPERATIONAL,
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device


def test_troubleshooting_flow_successful_resolution(
    client: TestClient,
    faculty_token: str,
    faculty_user: User,
    sample_device: Device,
    db_session: Session,
):
    # 1. Faculty creates troubleshooting session
    res_start = client.post(
        "/api/v1/troubleshooting/sessions",
        json={"device_id": sample_device.id, "symptom_text": "Projector displays no image and power LED is flashing"},
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert res_start.status_code == 201
    session_data = res_start.json()["data"]
    session_id = session_data["id"]
    assert session_data["status"] == "IN_PROGRESS"
    assert session_data["current_step"] == 1
    assert len(session_data["steps"]) == 1
    step_1 = session_data["steps"][0]
    assert step_1["step_number"] == 1
    assert "power" in step_1["instruction"].lower()

    # 2. Record Step 1 result
    res_res1 = client.post(
        f"/api/v1/troubleshooting/sessions/{session_id}/steps/{step_1['id']}/result",
        json={"result": "FAILED", "result_note": "Power LED stopped flashing but screen still dark"},
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert res_res1.status_code == 200
    assert res_res1.json()["data"]["result"] == "FAILED"

    # 3. Advance to Step 2
    res_step2 = client.post(
        f"/api/v1/troubleshooting/sessions/{session_id}/steps/next",
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert res_step2.status_code == 200
    step_2 = res_step2.json()["data"]
    assert step_2["step_number"] == 2
    assert "shutter" in step_2["instruction"].lower() or "mute" in step_2["instruction"].lower()

    # 4. Record Step 2 result as SUCCESS
    res_res2 = client.post(
        f"/api/v1/troubleshooting/sessions/{session_id}/steps/{step_2['id']}/result",
        json={"result": "SUCCESS", "result_note": "Lens shutter was closed. Opened shutter and image appeared!"},
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert res_res2.status_code == 200
    assert res_res2.json()["data"]["result"] == "SUCCESS"

    # 5. Complete session
    res_comp = client.post(
        f"/api/v1/troubleshooting/sessions/{session_id}/complete",
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert res_comp.status_code == 200
    assert res_comp.json()["data"]["status"] == "RESOLVED"
    assert res_comp.json()["data"]["ended_at"] is not None


def test_troubleshooting_unauthorized_access(
    client: TestClient,
    faculty_token: str,
    sample_device: Device,
    db_session: Session,
):
    # Start session as faculty_user
    res_start = client.post(
        "/api/v1/troubleshooting/sessions",
        json={"device_id": sample_device.id, "symptom_text": "Microphone has no sound"},
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    session_id = res_start.json()["data"]["id"]

    # Create another faculty user
    other_faculty = User(
        email="other.faculty@classroom.edu",
        name="Other Faculty",
        role=UserRole.FACULTY,
        is_active=True,
    )
    db_session.add(other_faculty)
    db_session.commit()
    db_session.refresh(other_faculty)

    other_token = create_access_token({"sub": other_faculty.id, "email": other_faculty.email, "role": other_faculty.role.value})

    # Other faculty cannot access this session
    res_other = client.post(
        f"/api/v1/troubleshooting/sessions/{session_id}/steps/next",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert res_other.status_code == 403


def test_troubleshooting_escalate_to_complaint(
    client: TestClient,
    faculty_token: str,
    sample_device: Device,
    db_session: Session,
):
    # 1. Start session
    res_start = client.post(
        "/api/v1/troubleshooting/sessions",
        json={"device_id": sample_device.id, "symptom_text": "Projector lamp failure"},
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    session_id = res_start.json()["data"]["id"]

    # 2. Escalate session to complaint
    res_esc = client.post(
        f"/api/v1/troubleshooting/sessions/{session_id}/complaint",
        json={"description": "Projector lamp exploded with loud pop, needs bulb replacement", "priority": "HIGH"},
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert res_esc.status_code == 201
    complaint_data = res_esc.json()["data"]
    assert complaint_data["session_id"] == session_id
    assert complaint_data["status"] == "PENDING"
    assert complaint_data["priority"] == "HIGH"

    # Verify device status changed to FAULTY
    db_session.refresh(sample_device)
    assert sample_device.status == DeviceStatus.FAULTY

