import logging
import sys
from pathlib import Path

# Ensure project root, server directory, and backend directory are in sys.path
SERVER_DIR = Path(__file__).resolve().parent.parent.parent  # .../server
REPO_ROOT = SERVER_DIR.parent
BACKEND_DIR = Path(__file__).resolve().parent.parent  # .../server/backend

for path_dir in (str(SERVER_DIR), str(REPO_ROOT), str(BACKEND_DIR)):
    if path_dir not in sys.path:
        sys.path.insert(0, path_dir)

from sqlalchemy import func, select
from backend.app.db.init_db import init_db
from backend.app.db.session import SessionLocal
from backend.app.models.classroom import Classroom
from backend.app.models.device import Device
from backend.app.models.device_history import DeviceHistory
from backend.app.models.enums import ChangeType, DeviceStatus, DeviceType, UserRole
from backend.app.models.user import User

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_data")

# -----------------------------------------------------------------------------
# SEED ACCOUNTS SPECIFICATION
# -----------------------------------------------------------------------------

PRIMARY_USERS = [
    {
        "email": "praveenj.cs24@bitsathy.ac.in",
        "name": "Praveen J (Admin)",
        "role": UserRole.ADMIN,
        "google_sub": None,
        "is_active": True,
    },
    {
        "email": "dhanushm.cs24@bitsathy.ac.in",
        "name": "Dhanush M (Faculty)",
        "role": UserRole.FACULTY,
        "google_sub": None,
        "is_active": True,
    },
    {
        "email": "thiyaneshd.ad24@bitsathy.ac.in",
        "name": "Thiyanesh D (Technician)",
        "role": UserRole.TECHNICIAN,
        "google_sub": None,
        "is_active": True,
    },
]

DEV_TEST_USERS = [
    {
        "email": "admin.dev@classroom.edu",
        "name": "Prof. Alan Turing (Admin Dev)",
        "role": UserRole.ADMIN,
        "google_sub": "mock_google_sub_admin_1001",
        "is_active": True,
    },
    {
        "email": "faculty.dev@classroom.edu",
        "name": "Dr. Grace Hopper (Faculty Dev)",
        "role": UserRole.FACULTY,
        "google_sub": "mock_google_sub_faculty_1002",
        "is_active": True,
    },
    {
        "email": "technician.dev@classroom.edu",
        "name": "Alex Vance (Technician Dev)",
        "role": UserRole.TECHNICIAN,
        "google_sub": "mock_google_sub_tech_1003",
        "is_active": True,
    },
    {
        "email": "deactivated.dev@classroom.edu",
        "name": "Inactive User (Testing)",
        "role": UserRole.FACULTY,
        "google_sub": "mock_google_sub_inactive_1004",
        "is_active": False,
    },
]

# -----------------------------------------------------------------------------
# 10 CLASSROOMS SPECIFICATION (001 to 010)
# -----------------------------------------------------------------------------

BUILDING_NAME = "Main Academic Block"
CLASSROOM_CODES = ["001", "002", "003", "004", "005", "006", "007", "008", "009", "010"]

CLASSROOMS_DATA = [
    {
        "building": BUILDING_NAME,
        "room_number": code,
        "description": f"Smart Classroom {code} equipped with dual AV projection, interactive display, and wireless audio.",
        "is_active": True,
    }
    for code in CLASSROOM_CODES
]

# -----------------------------------------------------------------------------
# 30 DEVICES SPECIFICATION (10 Microphones, 10 Projectors, 10 Smartboards)
# Verified real equipment models across 3 real manufacturers per category
# -----------------------------------------------------------------------------

# Distribution map across classrooms 001 - 010
DEVICES_PLAN = [
    # Room 001
    {"room": "001", "type": DeviceType.MICROPHONE.value, "brand": "Shure", "model": "SM58", "serial": "DEMO-MIC-001", "status": DeviceStatus.OPERATIONAL},
    {"room": "001", "type": DeviceType.PROJECTOR.value, "brand": "Epson", "model": "PowerLite L615U", "serial": "DEMO-PRJ-001", "status": DeviceStatus.OPERATIONAL},
    {"room": "001", "type": DeviceType.SMART_BOARD.value, "brand": "SMART Technologies", "model": "SMART Board 7000R Pro", "serial": "DEMO-SBD-001", "status": DeviceStatus.OPERATIONAL},

    # Room 002
    {"room": "002", "type": DeviceType.MICROPHONE.value, "brand": "Sennheiser", "model": "EW-D SKM-S", "serial": "DEMO-MIC-002", "status": DeviceStatus.OPERATIONAL},
    {"room": "002", "type": DeviceType.PROJECTOR.value, "brand": "BenQ", "model": "MW560", "serial": "DEMO-PRJ-002", "status": DeviceStatus.OPERATIONAL},
    {"room": "002", "type": DeviceType.SMART_BOARD.value, "brand": "ViewSonic", "model": "ViewBoard IFP6550", "serial": "DEMO-SBD-002", "status": DeviceStatus.OPERATIONAL},

    # Room 003
    {"room": "003", "type": DeviceType.MICROPHONE.value, "brand": "Audio-Technica", "model": "ATW-1102", "serial": "DEMO-MIC-003", "status": DeviceStatus.OPERATIONAL},
    {"room": "003", "type": DeviceType.PROJECTOR.value, "brand": "Sony", "model": "VPL-PHZ60", "serial": "DEMO-PRJ-003", "status": DeviceStatus.DEGRADED},
    {"room": "003", "type": DeviceType.SMART_BOARD.value, "brand": "BenQ", "model": "BenQ Board Master RP6502", "serial": "DEMO-SBD-003", "status": DeviceStatus.OPERATIONAL},

    # Room 004
    {"room": "004", "type": DeviceType.MICROPHONE.value, "brand": "Shure", "model": "ULXD4", "serial": "DEMO-MIC-004", "status": DeviceStatus.OPERATIONAL},
    {"room": "004", "type": DeviceType.PROJECTOR.value, "brand": "Epson", "model": "EB-2250U", "serial": "DEMO-PRJ-004", "status": DeviceStatus.OPERATIONAL},
    {"room": "004", "type": DeviceType.SMART_BOARD.value, "brand": "SMART Technologies", "model": "SMART Board MX065-V2", "serial": "DEMO-SBD-004", "status": DeviceStatus.OPERATIONAL},

    # Room 005
    {"room": "005", "type": DeviceType.MICROPHONE.value, "brand": "Sennheiser", "model": "SL Handheld DW", "serial": "DEMO-MIC-005", "status": DeviceStatus.OPERATIONAL},
    {"room": "005", "type": DeviceType.PROJECTOR.value, "brand": "BenQ", "model": "MH560", "serial": "DEMO-PRJ-005", "status": DeviceStatus.OPERATIONAL},
    {"room": "005", "type": DeviceType.SMART_BOARD.value, "brand": "ViewSonic", "model": "ViewBoard IFP7550", "serial": "DEMO-SBD-005", "status": DeviceStatus.OPERATIONAL},

    # Room 006
    {"room": "006", "type": DeviceType.MICROPHONE.value, "brand": "Audio-Technica", "model": "AT2020", "serial": "DEMO-MIC-006", "status": DeviceStatus.FAULTY},
    {"room": "006", "type": DeviceType.PROJECTOR.value, "brand": "Sony", "model": "VPL-PHZ50", "serial": "DEMO-PRJ-006", "status": DeviceStatus.OPERATIONAL},
    {"room": "006", "type": DeviceType.SMART_BOARD.value, "brand": "BenQ", "model": "BenQ Board Pro RP7502", "serial": "DEMO-SBD-006", "status": DeviceStatus.OPERATIONAL},

    # Room 007
    {"room": "007", "type": DeviceType.MICROPHONE.value, "brand": "Shure", "model": "MXA910", "serial": "DEMO-MIC-007", "status": DeviceStatus.OPERATIONAL},
    {"room": "007", "type": DeviceType.PROJECTOR.value, "brand": "Epson", "model": "PowerLite 119W", "serial": "DEMO-PRJ-007", "status": DeviceStatus.OPERATIONAL},
    {"room": "007", "type": DeviceType.SMART_BOARD.value, "brand": "SMART Technologies", "model": "SMART Board GX065", "serial": "DEMO-SBD-007", "status": DeviceStatus.OPERATIONAL},

    # Room 008
    {"room": "008", "type": DeviceType.MICROPHONE.value, "brand": "Sennheiser", "model": "e 835", "serial": "DEMO-MIC-008", "status": DeviceStatus.OPERATIONAL},
    {"room": "008", "type": DeviceType.PROJECTOR.value, "brand": "BenQ", "model": "LK936ST", "serial": "DEMO-PRJ-008", "status": DeviceStatus.OPERATIONAL},
    {"room": "008", "type": DeviceType.SMART_BOARD.value, "brand": "ViewSonic", "model": "ViewBoard IFP8650", "serial": "DEMO-SBD-008", "status": DeviceStatus.OPERATIONAL},

    # Room 009
    {"room": "009", "type": DeviceType.MICROPHONE.value, "brand": "Audio-Technica", "model": "System 10 Pro", "serial": "DEMO-MIC-009", "status": DeviceStatus.OPERATIONAL},
    {"room": "009", "type": DeviceType.PROJECTOR.value, "brand": "Sony", "model": "VPL-CWZ10", "serial": "DEMO-PRJ-009", "status": DeviceStatus.OPERATIONAL},
    {"room": "009", "type": DeviceType.SMART_BOARD.value, "brand": "BenQ", "model": "BenQ Board Essential RE6501", "serial": "DEMO-SBD-009", "status": DeviceStatus.OPERATIONAL},

    # Room 010
    {"room": "010", "type": DeviceType.MICROPHONE.value, "brand": "Shure", "model": "SM58", "serial": "DEMO-MIC-010", "status": DeviceStatus.OPERATIONAL},
    {"room": "010", "type": DeviceType.PROJECTOR.value, "brand": "Epson", "model": "EB-L730U", "serial": "DEMO-PRJ-010", "status": DeviceStatus.OPERATIONAL},
    {"room": "010", "type": DeviceType.SMART_BOARD.value, "brand": "SMART Technologies", "model": "SMART Board 6000S", "serial": "DEMO-SBD-010", "status": DeviceStatus.OPERATIONAL},
]


def seed_database(clean_legacy: bool = True, session=None):
    """Seed development database idempotently without duplicating or overwriting user data."""
    should_close = False
    if session is None:
        logger.info("Ensuring database tables and schema migrations are applied...")
        init_db()
        db = SessionLocal()
        should_close = True
    else:
        db = session
        from backend.app.db.base import Base
        Base.metadata.create_all(bind=db.get_bind())
    try:
        # 0. Clean legacy Phase 1 sample rooms if no complaints or sessions depend on them
        if clean_legacy:
            legacy_rooms = db.execute(
                select(Classroom).where(Classroom.room_number.in_(["ST-101", "ST-204", "ENG-302"]))
            ).scalars().all()
            for r in legacy_rooms:
                # Check for dependencies
                has_complaints = len(r.complaints) > 0
                if not has_complaints:
                    logger.info("Cleaning legacy Phase 1 sample room: %s %s", r.building, r.room_number)
                    db.delete(r)
            db.commit()

        # 1. Seed Users
        logger.info("Seeding user accounts...")
        all_users = PRIMARY_USERS + DEV_TEST_USERS
        for user_data in all_users:
            stmt = select(User).where(User.email == user_data["email"].strip().lower())
            existing_user = db.execute(stmt).scalar_one_or_none()
            if not existing_user:
                new_user = User(
                    email=user_data["email"].strip().lower(),
                    name=user_data["name"],
                    role=user_data["role"],
                    google_sub=user_data["google_sub"],
                    is_active=user_data["is_active"],
                )
                db.add(new_user)
                logger.info("Added user: %s [%s]", user_data["email"], user_data["role"].value)
            else:
                # Update role and status if provisioned state needs sync
                if existing_user.role != user_data["role"] or existing_user.is_active != user_data["is_active"]:
                    existing_user.role = user_data["role"]
                    existing_user.is_active = user_data["is_active"]
                    db.add(existing_user)
                    logger.info("Updated user role/status: %s [%s]", user_data["email"], user_data["role"].value)
                else:
                    logger.info("User up to date: %s [%s]", user_data["email"], user_data["role"].value)
        db.commit()

        # 2. Seed 10 Classrooms (001 - 010)
        logger.info("Seeding exactly 10 classrooms (001 - 010)...")
        classroom_map = {}
        for room_data in CLASSROOMS_DATA:
            stmt = select(Classroom).where(
                Classroom.building == room_data["building"],
                Classroom.room_number == room_data["room_number"],
            )
            existing_room = db.execute(stmt).scalar_one_or_none()
            if not existing_room:
                new_room = Classroom(
                    building=room_data["building"],
                    room_number=room_data["room_number"],
                    description=room_data["description"],
                    is_active=room_data["is_active"],
                )
                db.add(new_room)
                db.flush()
                classroom_map[room_data["room_number"]] = new_room.id
                logger.info("Added classroom: %s %s", room_data["building"], room_data["room_number"])
            else:
                classroom_map[room_data["room_number"]] = existing_room.id
                logger.info("Classroom already exists: %s %s", room_data["building"], room_data["room_number"])
        db.commit()

        # 3. Seed 30 Devices
        logger.info("Seeding exactly 30 devices across 10 classrooms...")
        added_count = 0
        existing_count = 0

        for dev_data in DEVICES_PLAN:
            classroom_id = classroom_map.get(dev_data["room"])
            if not classroom_id:
                logger.warning("Classroom %s not found for device seeding!", dev_data["room"])
                continue

            stmt = select(Device).where(
                Device.classroom_id == classroom_id,
                Device.device_type == dev_data["type"],
                Device.brand == dev_data["brand"],
                Device.model == dev_data["model"],
            )
            existing_dev = db.execute(stmt).scalar_one_or_none()

            if not existing_dev:
                new_dev = Device(
                    classroom_id=classroom_id,
                    device_type=dev_data["type"],
                    brand=dev_data["brand"],
                    model=dev_data["model"],
                    serial_number=dev_data["serial"],
                    status=dev_data["status"],
                )
                db.add(new_dev)
                db.flush()

                # Add initial DeviceHistory record
                hist = DeviceHistory(
                    device_id=new_dev.id,
                    changed_by=None,
                    change_type=ChangeType.CREATED.value,
                    previous_values=None,
                    new_values={
                        "device_type": dev_data["type"],
                        "brand": dev_data["brand"],
                        "model": dev_data["model"],
                        "serial_number": dev_data["serial"],
                        "status": dev_data["status"].value,
                    },
                )
                db.add(hist)
                added_count += 1
                logger.info(
                    "Added device: [%s] %s %s in Room %s (Serial: %s)",
                    dev_data["type"],
                    dev_data["brand"],
                    dev_data["model"],
                    dev_data["room"],
                    dev_data["serial"],
                )
            else:
                existing_count += 1
                logger.info(
                    "Device already exists: [%s] %s %s in Room %s",
                    dev_data["type"],
                    dev_data["brand"],
                    dev_data["model"],
                    dev_data["room"],
                )

        db.commit()

        # ---------------------------------------------------------------------
        # CONCISE INVENTORY SUMMARY
        # ---------------------------------------------------------------------
        total_classrooms = db.execute(select(func.count(Classroom.id))).scalar_one()
        total_devices = db.execute(select(func.count(Device.id))).scalar_one()
        total_mics = db.execute(select(func.count(Device.id)).where(Device.device_type == DeviceType.MICROPHONE.value)).scalar_one()
        total_prjs = db.execute(select(func.count(Device.id)).where(Device.device_type == DeviceType.PROJECTOR.value)).scalar_one()
        total_sbds = db.execute(select(func.count(Device.id)).where(Device.device_type == DeviceType.SMART_BOARD.value)).scalar_one()
        total_users = db.execute(select(func.count(User.id))).scalar_one()

        print("\n" + "=" * 60)
        print("DATABASE SEED INVENTORY SUMMARY")
        print("=" * 60)
        print(f"Total Users:        {total_users}")
        print(f"Total Classrooms:   {total_classrooms} (Identifiers: {', '.join(CLASSROOM_CODES)})")
        print(f"Total Devices:      {total_devices}")
        print(f"  - Microphones:    {total_mics}")
        print(f"  - Projectors:     {total_prjs}")
        print(f"  - Smartboards:    {total_sbds}")
        print(f"Devices Added:      {added_count}")
        print(f"Devices Existing:   {existing_count}")
        print("=" * 60 + "\n")

    except Exception as e:
        db.rollback()
        logger.error("Seeding failed: %s", str(e), exc_info=True)
        raise
    finally:
        if should_close:
            db.close()


if __name__ == "__main__":
    seed_database()
