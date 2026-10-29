import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.classroom import Classroom
from backend.app.models.device import Device
from backend.app.models.enums import DeviceType, UserRole
from backend.app.models.user import User
from backend.scripts.seed_data import CLASSROOM_CODES, seed_database
from backend.tests.conftest import TestingSessionLocal


def test_seed_database_inventory_and_roles(db_session: Session):
    """Verify seed script populates exactly 10 classrooms, 30 devices, and 3 specific BIT role accounts."""
    # Seed the isolated test database
    seed_database(clean_legacy=True, session=db_session)

    # 1. Verify 10 classrooms
    classrooms = db_session.execute(select(Classroom)).scalars().all()
    room_numbers = [c.room_number for c in classrooms]
    assert len(classrooms) == 10, f"Expected 10 classrooms, found {len(classrooms)}"
    for code in CLASSROOM_CODES:
        assert code in room_numbers, f"Classroom code '{code}' not found in inventory"

    # 2. Verify 30 devices total
    devices = db_session.execute(select(Device)).scalars().all()
    assert len(devices) == 30, f"Expected 30 devices, found {len(devices)}"

    # 3. Verify exactly 10 microphones, 10 projectors, and 10 smartboards
    mics = [d for d in devices if d.device_type == DeviceType.MICROPHONE.value]
    prjs = [d for d in devices if d.device_type == DeviceType.PROJECTOR.value]
    sbds = [d for d in devices if d.device_type == DeviceType.SMART_BOARD.value]

    assert len(mics) == 10, f"Expected 10 microphones, found {len(mics)}"
    assert len(prjs) == 10, f"Expected 10 projectors, found {len(prjs)}"
    assert len(sbds) == 10, f"Expected 10 smartboards, found {len(sbds)}"

    # 4. Verify 3 real manufacturers per category
    mic_brands = {d.brand for d in mics}
    assert mic_brands == {"Shure", "Sennheiser", "Audio-Technica"}

    prj_brands = {d.brand for d in prjs}
    assert prj_brands == {"Epson", "BenQ", "Sony"}

    sbd_brands = {d.brand for d in sbds}
    assert sbd_brands == {"SMART Technologies", "ViewSonic", "BenQ"}

    # 5. Verify every classroom has exactly 1 of each category
    for c in classrooms:
        room_devices = [d for d in devices if d.classroom_id == c.id]
        assert len(room_devices) == 3
        types_in_room = {d.device_type for d in room_devices}
        assert types_in_room == {
            DeviceType.MICROPHONE.value,
            DeviceType.PROJECTOR.value,
            DeviceType.SMART_BOARD.value,
        }

    # 6. Verify the 3 required BIT role accounts
    admin_acc = db_session.execute(
        select(User).where(User.email == "praveenj.cs24@bitsathy.ac.in")
    ).scalar_one_or_none()
    assert admin_acc is not None
    assert admin_acc.role == UserRole.ADMIN
    assert admin_acc.is_active is True

    faculty_acc = db_session.execute(
        select(User).where(User.email == "dhanushm.cs24@bitsathy.ac.in")
    ).scalar_one_or_none()
    assert faculty_acc is not None
    assert faculty_acc.role == UserRole.FACULTY
    assert faculty_acc.is_active is True

    tech_acc = db_session.execute(
        select(User).where(User.email == "thiyaneshd.ad24@bitsathy.ac.in")
    ).scalar_one_or_none()
    assert tech_acc is not None
    assert tech_acc.role == UserRole.TECHNICIAN
    assert tech_acc.is_active is True


def test_seed_idempotency(db_session: Session):
    """Verify running seed script multiple times does not duplicate records or create collisions."""
    seed_database(clean_legacy=True, session=db_session)
    count_rooms_1 = db_session.execute(select(func.count(Classroom.id))).scalar_one()
    count_devs_1 = db_session.execute(select(func.count(Device.id))).scalar_one()

    # Re-run seed
    seed_database(clean_legacy=True, session=db_session)
    count_rooms_2 = db_session.execute(select(func.count(Classroom.id))).scalar_one()
    count_devs_2 = db_session.execute(select(func.count(Device.id))).scalar_one()

    assert count_rooms_1 == count_rooms_2 == 10
    assert count_devs_1 == count_devs_2 == 30
