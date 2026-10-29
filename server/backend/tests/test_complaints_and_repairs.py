import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token
from backend.app.models.classroom import Classroom
from backend.app.models.complaint import Complaint
from backend.app.models.device import Device
from backend.app.models.enums import ComplaintStatus, DeviceStatus, DeviceType, UserRole
from backend.app.models.repair_record import RepairRecord
from backend.app.models.user import User


@pytest.fixture
def test_setup(db_session: Session):
    classroom = Classroom(building="Main Academic Block", room_number="002", description="Room 002", is_active=True)
    db_session.add(classroom)
    db_session.commit()
    db_session.refresh(classroom)

    device = Device(
        classroom_id=classroom.id,
        device_type=DeviceType.MICROPHONE.value,
        brand="Shure",
        model="SM58",
        serial_number="DEMO-MIC-TEST-002",
        status=DeviceStatus.FAULTY,
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)

    return {"classroom": classroom, "device": device}


def test_complaint_lifecycle_and_technician_resolution(
    client: TestClient,
    admin_token: str,
    faculty_token: str,
    technician_token: str,
    technician_user: User,
    test_setup: dict,
    db_session: Session,
):
    device = test_setup["device"]
    classroom = test_setup["classroom"]

    # 1. Faculty creates a complaint
    res_comp = client.post(
        "/api/v1/complaints",
        json={
            "device_id": device.id,
            "classroom_id": classroom.id,
            "description": "Microphone emits loud high pitch squeal and crackling",
            "priority": "HIGH",
        },
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert res_comp.status_code == 201
    comp_data = res_comp.json()["data"]
    complaint_id = comp_data["id"]
    assert comp_data["status"] == "PENDING"
    assert comp_data["priority"] == "HIGH"

    # 2. Admin assigns complaint to technician
    res_assign = client.patch(
        f"/api/v1/complaints/{complaint_id}/assignment",
        json={"technician_id": technician_user.id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_assign.status_code == 200
    assert res_assign.json()["data"]["assigned_technician_id"] == technician_user.id
    assert res_assign.json()["data"]["status"] == "ASSIGNED"

    # 3. Technician updates status to IN_PROGRESS
    res_prog = client.patch(
        f"/api/v1/complaints/{complaint_id}/status",
        json={"status": "IN_PROGRESS"},
        headers={"Authorization": f"Bearer {technician_token}"},
    )
    assert res_prog.status_code == 200
    assert res_prog.json()["data"]["status"] == "IN_PROGRESS"

    # 4. Faculty cannot submit resolution (403 Forbidden)
    res_fac_res = client.post(
        f"/api/v1/complaints/{complaint_id}/resolution",
        json={"confirmed_cause": "Loose wire", "repair_action": "Soldered connection"},
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert res_fac_res.status_code == 403

    # 5. Assigned technician submits resolution
    res_res = client.post(
        f"/api/v1/complaints/{complaint_id}/resolution",
        json={
            "confirmed_cause": "Degraded XLR connector solder joint inside podium receptacle plate",
            "repair_action": "Resoldered ground pin and tightened XLR strain relief collar",
            "parts_replaced": "Neutrik NC3MD-L-1 XLR connector pin insert",
            "resolution_notes": "Tested with tone generator and frequency sweep. 0dB SNR, no feedback or crackling.",
        },
        headers={"Authorization": f"Bearer {technician_token}"},
    )
    assert res_res.status_code == 200
    res_data = res_res.json()["data"]
    assert res_data["status"] == "RESOLVED"
    assert res_data["repair_record"] is not None
    assert res_data["repair_record"]["parts_replaced"] == "Neutrik NC3MD-L-1 XLR connector pin insert"

    # Verify device status restored to OPERATIONAL in DB
    db_session.refresh(device)
    assert device.status == DeviceStatus.OPERATIONAL

    # 6. Attempting duplicate resolution returns 409 Conflict
    res_dup = client.post(
        f"/api/v1/complaints/{complaint_id}/resolution",
        json={"confirmed_cause": "Duplicate attempt", "repair_action": "None"},
        headers={"Authorization": f"Bearer {technician_token}"},
    )
    assert res_dup.status_code == 409


def test_technician_role_and_assignment_restrictions(
    client: TestClient,
    admin_token: str,
    technician_token: str,
    test_setup: dict,
    db_session: Session,
):
    device = test_setup["device"]
    classroom = test_setup["classroom"]

    # Create reporter user
    reporter = User(email="complaint.reporter@classroom.edu", name="Reporter User", role=UserRole.FACULTY, is_active=True)
    db_session.add(reporter)
    db_session.commit()
    db_session.refresh(reporter)

    # Create complaint
    complaint = Complaint(
        device_id=device.id,
        classroom_id=classroom.id,
        reported_by=reporter.id,
        description="Smartboard touch dead",
        priority="LOW",
        status=ComplaintStatus.PENDING,
    )
    db_session.add(complaint)
    db_session.commit()
    db_session.refresh(complaint)

    # Attempt to assign to non-technician user should fail with 400
    non_tech_user = User(email="not.a.tech@classroom.edu", name="Teacher", role=UserRole.FACULTY, is_active=True)
    db_session.add(non_tech_user)
    db_session.commit()
    db_session.refresh(non_tech_user)

    res_bad_assign = client.patch(
        f"/api/v1/complaints/{complaint.id}/assignment",
        json={"technician_id": non_tech_user.id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_bad_assign.status_code == 400

    # Unassigned technician cannot resolve complaint
    res_unassigned_res = client.post(
        f"/api/v1/complaints/{complaint.id}/resolution",
        json={"confirmed_cause": "Cause", "repair_action": "Action"},
        headers={"Authorization": f"Bearer {technician_token}"},
    )
    assert res_unassigned_res.status_code == 403
