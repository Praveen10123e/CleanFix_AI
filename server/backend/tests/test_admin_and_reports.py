import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.classroom import Classroom
from backend.app.models.complaint import Complaint
from backend.app.models.device import Device
from backend.app.models.enums import ComplaintStatus, DeviceStatus, DeviceType, UserRole
from backend.app.models.repair_record import RepairRecord
from backend.app.models.user import User


def test_admin_user_provisioning_and_management(
    client: TestClient,
    admin_token: str,
    faculty_token: str,
    db_session: Session,
):
    # 1. Non-admin cannot provision users (403 Forbidden)
    res_forbidden = client.post(
        "/api/v1/admin/users",
        json={"email": "new.tech@bitsathy.ac.in", "name": "New Tech", "role": "TECHNICIAN"},
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert res_forbidden.status_code == 403

    # 2. Admin provisions user
    res_create = client.post(
        "/api/v1/admin/users",
        json={"email": "new.tech@bitsathy.ac.in", "name": "New Tech", "role": "TECHNICIAN"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_create.status_code == 201
    user_data = res_create.json()["data"]
    assert user_data["email"] == "new.tech@bitsathy.ac.in"
    assert user_data["role"] == "TECHNICIAN"
    user_id = user_data["id"]

    # 3. Duplicate email returns 409 Conflict
    res_dup = client.post(
        "/api/v1/admin/users",
        json={"email": "new.tech@bitsathy.ac.in", "name": "New Tech Dup", "role": "FACULTY"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_dup.status_code == 409

    # 4. List users
    res_list = client.get(
        "/api/v1/admin/users",
        params={"role": "TECHNICIAN"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_list.status_code == 200
    assert any(u["email"] == "new.tech@bitsathy.ac.in" for u in res_list.json()["data"])

    # 5. Patch user (deactivation)
    res_patch = client.patch(
        f"/api/v1/admin/users/{user_id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["data"]["is_active"] is False


def test_admin_reports_summary(
    client: TestClient,
    admin_token: str,
    faculty_token: str,
    db_session: Session,
):
    # 1. Non-admin cannot access reports
    res_fac = client.get(
        "/api/v1/admin/reports/summary",
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert res_fac.status_code == 403

    # 2. Setup mock data
    cr = Classroom(building="Demo Tower", room_number="DT-101", description="Lab", is_active=True)
    db_session.add(cr)
    db_session.flush()

    dev1 = Device(classroom_id=cr.id, device_type=DeviceType.PROJECTOR.value, brand="Epson", model="L615U", status=DeviceStatus.OPERATIONAL)
    dev2 = Device(classroom_id=cr.id, device_type=DeviceType.MICROPHONE.value, brand="Shure", model="SM58", status=DeviceStatus.FAULTY)
    db_session.add_all([dev1, dev2])
    db_session.flush()

    user = User(email="reporter@test.edu", name="Reporter", role=UserRole.FACULTY, is_active=True)
    tech = User(email="technician@test.edu", name="Tech", role=UserRole.TECHNICIAN, is_active=True)
    db_session.add_all([user, tech])
    db_session.flush()

    complaint = Complaint(
        device_id=dev2.id,
        classroom_id=cr.id,
        reported_by=user.id,
        assigned_technician_id=tech.id,
        description="Mic buzzing",
        priority="HIGH",
        status=ComplaintStatus.RESOLVED,
    )
    db_session.add(complaint)
    db_session.flush()

    repair = RepairRecord(
        complaint_id=complaint.id,
        technician_id=tech.id,
        confirmed_cause="Blown capacitor",
        repair_action="Replaced capacitor",
    )
    db_session.add(repair)
    db_session.commit()

    # 3. Query report summary
    res_rep = client.get(
        "/api/v1/admin/reports/summary",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_rep.status_code == 200
    data = res_rep.json()["data"]

    assert data["total_active_classrooms"] >= 1
    assert data["total_active_devices"] >= 2
    assert "PROJECTOR" in data["device_counts_by_category"]
    assert "Epson" in data["device_counts_by_brand"]
    assert data["total_complaints"] >= 1
    assert data["completed_repairs"] >= 1
    assert data["assigned_complaints"] >= 1
    assert data["complaints_by_priority"].get("HIGH", 0) >= 1

