import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.classroom import Classroom
from backend.app.models.device import Device
from backend.app.models.device_history import DeviceHistory
from backend.app.models.enums import ChangeType, DeviceStatus, DeviceType


def test_classroom_crud_and_permissions(
    client: TestClient,
    admin_token: str,
    faculty_token: str,
    technician_token: str,
    db_session: Session,
):
    # 1. Faculty cannot create classroom
    res = client.post(
        "/api/v1/classrooms",
        json={"room_number": "901", "building": "Science Tower", "description": "Demo room"},
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert res.status_code == 403

    # 2. Admin creates classroom
    res = client.post(
        "/api/v1/classrooms",
        json={"room_number": "901", "building": "Science Tower", "description": "Demo room"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 201
    created = res.json()["data"]
    assert created["room_number"] == "901"
    assert created["building"] == "Science Tower"
    room_id = created["id"]

    # 3. Duplicate creation rejected with 409 Conflict
    res_dup = client.post(
        "/api/v1/classrooms",
        json={"room_number": "901", "building": "Science Tower"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_dup.status_code == 409
    assert res_dup.json()["error"]["code"] == "CONFLICT"

    # 4. Faculty can list classrooms
    res_list = client.get(
        "/api/v1/classrooms",
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert len(list_data["data"]) >= 1
    assert list_data["meta"]["total"] >= 1

    # 5. Get classroom by ID
    res_get = client.get(
        f"/api/v1/classrooms/{room_id}",
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert res_get.status_code == 200
    assert res_get.json()["data"]["id"] == room_id

    # 6. Non-existent classroom returns 404
    non_existent = str(uuid.uuid4())
    res_404 = client.get(
        f"/api/v1/classrooms/{non_existent}",
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert res_404.status_code == 404

    # 7. Admin patches classroom
    res_patch = client.patch(
        f"/api/v1/classrooms/{room_id}",
        json={"description": "Updated room description", "is_active": True},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["data"]["description"] == "Updated room description"


def test_device_crud_history_and_classroom_devices(
    client: TestClient,
    admin_token: str,
    faculty_token: str,
    technician_token: str,
    db_session: Session,
):
    # Setup test classroom
    room = Classroom(building="Tech Block", room_number="TB-100", description="Lab", is_active=True)
    db_session.add(room)
    db_session.commit()
    db_session.refresh(room)

    # 1. Faculty cannot register a device
    res_fac = client.post(
        "/api/v1/devices",
        json={
            "classroom_id": room.id,
            "device_type": DeviceType.PROJECTOR.value,
            "brand": "Epson",
            "model": "PowerLite L615U",
            "serial_number": "TEST-SN-1001",
            "status": "OPERATIONAL",
        },
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert res_fac.status_code == 403

    # 2. Cannot reference nonexistent classroom
    fake_room_id = str(uuid.uuid4())
    res_fake_room = client.post(
        "/api/v1/devices",
        json={
            "classroom_id": fake_room_id,
            "device_type": DeviceType.PROJECTOR.value,
            "brand": "Epson",
            "model": "PowerLite L615U",
            "serial_number": "TEST-SN-1001",
            "status": "OPERATIONAL",
        },
        headers={"Authorization": f"Bearer {technician_token}"},
    )
    assert res_fake_room.status_code == 404

    # 3. Technician creates device successfully
    res_dev = client.post(
        "/api/v1/devices",
        json={
            "classroom_id": room.id,
            "device_type": DeviceType.PROJECTOR.value,
            "brand": "Epson",
            "model": "PowerLite L615U",
            "serial_number": "TEST-SN-1001",
            "status": "OPERATIONAL",
        },
        headers={"Authorization": f"Bearer {technician_token}"},
    )
    assert res_dev.status_code == 201
    dev_data = res_dev.json()["data"]
    device_id = dev_data["id"]
    assert dev_data["model"] == "PowerLite L615U"

    # Verify device history record was created
    history_records = db_session.execute(
        select(DeviceHistory).where(DeviceHistory.device_id == device_id)
    ).scalars().all()
    assert len(history_records) >= 1
    assert history_records[0].change_type == ChangeType.CREATED.value

    # 4. Duplicate serial number returns 409
    res_dup_sn = client.post(
        "/api/v1/devices",
        json={
            "classroom_id": room.id,
            "device_type": DeviceType.PROJECTOR.value,
            "brand": "Sony",
            "model": "VPL-PHZ60",
            "serial_number": "TEST-SN-1001",
            "status": "OPERATIONAL",
        },
        headers={"Authorization": f"Bearer {technician_token}"},
    )
    assert res_dup_sn.status_code == 409

    # 5. List devices in classroom
    res_cr_devs = client.get(
        f"/api/v1/classrooms/{room.id}/devices",
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert res_cr_devs.status_code == 200
    assert len(res_cr_devs.json()["data"]) == 1
    assert res_cr_devs.json()["data"][0]["id"] == device_id

    # 6. Technician updates device status (records STATUS_CHANGE in history)
    res_patch = client.patch(
        f"/api/v1/devices/{device_id}",
        json={"status": DeviceStatus.FAULTY.value},
        headers={"Authorization": f"Bearer {technician_token}"},
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["data"]["status"] == DeviceStatus.FAULTY.value

    history_after_status = db_session.execute(
        select(DeviceHistory).where(DeviceHistory.device_id == device_id).order_by(DeviceHistory.created_at.desc())
    ).scalars().all()
    assert any(h.change_type == ChangeType.STATUS_CHANGE.value for h in history_after_status)

