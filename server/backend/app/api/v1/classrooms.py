import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from backend.app.core.dependencies import (
    get_current_active_user,
    require_admin,
    require_technician_or_admin,
)
from backend.app.core.exceptions import ConflictException, NotFoundException
from backend.app.db.session import get_db
from backend.app.models.audit_log import AuditLog
from backend.app.models.classroom import Classroom
from backend.app.models.device import Device
from backend.app.models.enums import DeviceStatus
from backend.app.models.user import User
from backend.app.schemas.classroom import ClassroomCreate, ClassroomRead, ClassroomUpdate
from backend.app.schemas.common import ListResponse, PaginationMeta, SingleResponse
from backend.app.schemas.device import DeviceRead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/classrooms", tags=["Classrooms"])


@router.post(
    "",
    response_model=SingleResponse[ClassroomRead],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new classroom",
    description="Registers a new classroom with room number and building. Admin or Technician role required.",
)
def create_classroom(
    payload: ClassroomCreate,
    current_user: User = Depends(require_technician_or_admin),
    db: Session = Depends(get_db),
):
    # Check for duplicate building + room_number
    stmt = select(Classroom).where(
        Classroom.building == payload.building.strip(),
        Classroom.room_number == payload.room_number.strip(),
    )
    existing = db.execute(stmt).scalar_one_or_none()
    if existing:
        raise ConflictException(
            message=f"Classroom '{payload.room_number}' in building '{payload.building}' already exists.",
            details={"room_number": payload.room_number, "building": payload.building},
        )

    classroom = Classroom(
        room_number=payload.room_number.strip(),
        building=payload.building.strip(),
        description=payload.description.strip() if payload.description else None,
        is_active=True,
    )
    db.add(classroom)
    db.flush()

    audit = AuditLog(
        actor_id=current_user.id,
        action="CLASSROOM_CREATED",
        entity_type="CLASSROOM",
        entity_id=classroom.id,
    )
    db.add(audit)
    db.commit()
    db.refresh(classroom)

    logger.info("Classroom created: %s %s (id: %s) by %s", classroom.building, classroom.room_number, classroom.id, current_user.email)
    return SingleResponse(data=ClassroomRead.model_validate(classroom))


@router.get(
    "",
    response_model=ListResponse[ClassroomRead],
    status_code=status.HTTP_200_OK,
    summary="List active classrooms",
    description="Lists classrooms with optional search, active filtering, and pagination.",
)
def list_classrooms(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    stmt = select(Classroom)
    count_stmt = select(func.count(Classroom.id))

    if is_active is not None:
        stmt = stmt.where(Classroom.is_active == is_active)
        count_stmt = count_stmt.where(Classroom.is_active == is_active)

    if search:
        search_filter = or_(
            Classroom.room_number.ilike(f"%{search.strip()}%"),
            Classroom.building.ilike(f"%{search.strip()}%"),
            Classroom.description.ilike(f"%{search.strip()}%"),
        )
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    total = db.execute(count_stmt).scalar_one()
    items = db.execute(
        stmt.order_by(Classroom.building.asc(), Classroom.room_number.asc()).limit(limit).offset(offset)
    ).scalars().all()

    return ListResponse(
        data=[ClassroomRead.model_validate(c) for c in items],
        meta=PaginationMeta(limit=limit, offset=offset, total=total),
    )


@router.get(
    "/{id}",
    response_model=SingleResponse[ClassroomRead],
    status_code=status.HTTP_200_OK,
    summary="Get classroom details",
    description="Retrieves a single classroom by its unique UUID.",
)
def get_classroom(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    stmt = select(Classroom).where(Classroom.id == id)
    classroom = db.execute(stmt).scalar_one_or_none()
    if not classroom:
        raise NotFoundException(message=f"Classroom with ID '{id}' not found.", details={"classroom_id": id})

    return SingleResponse(data=ClassroomRead.model_validate(classroom))


@router.patch(
    "/{id}",
    response_model=SingleResponse[ClassroomRead],
    status_code=status.HTTP_200_OK,
    summary="Update classroom details",
    description="Updates room attributes or deactivates classroom. Admin only.",
)
def update_classroom(
    id: str,
    payload: ClassroomUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    stmt = select(Classroom).where(Classroom.id == id)
    classroom = db.execute(stmt).scalar_one_or_none()
    if not classroom:
        raise NotFoundException(message=f"Classroom with ID '{id}' not found.", details={"classroom_id": id})

    new_building = payload.building.strip() if payload.building is not None else classroom.building
    new_room = payload.room_number.strip() if payload.room_number is not None else classroom.room_number

    # Check for uniqueness collision
    if new_building != classroom.building or new_room != classroom.room_number:
        stmt_dup = select(Classroom).where(
            Classroom.building == new_building,
            Classroom.room_number == new_room,
            Classroom.id != id,
        )
        if db.execute(stmt_dup).scalar_one_or_none():
            raise ConflictException(
                message=f"Another classroom with room '{new_room}' in building '{new_building}' already exists.",
                details={"room_number": new_room, "building": new_building},
            )

    if payload.building is not None:
        classroom.building = new_building
    if payload.room_number is not None:
        classroom.room_number = new_room
    if payload.description is not None:
        classroom.description = payload.description.strip() if payload.description else None
    if payload.is_active is not None:
        classroom.is_active = payload.is_active

    audit = AuditLog(
        actor_id=current_user.id,
        action="CLASSROOM_UPDATED",
        entity_type="CLASSROOM",
        entity_id=classroom.id,
    )
    db.add(audit)
    db.commit()
    db.refresh(classroom)

    logger.info("Classroom updated: %s by %s", classroom.id, current_user.email)
    return SingleResponse(data=ClassroomRead.model_validate(classroom))


@router.get(
    "/{id}/devices",
    response_model=ListResponse[DeviceRead],
    status_code=status.HTTP_200_OK,
    summary="List devices in a classroom",
    description="Retrieves all devices associated with a specific classroom. Accessible by all authenticated active users.",
)
def list_classroom_devices(
    id: str,
    device_type: Optional[str] = Query(None),
    status_filter: Optional[DeviceStatus] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # Verify classroom exists
    classroom_stmt = select(Classroom).where(Classroom.id == id)
    classroom = db.execute(classroom_stmt).scalar_one_or_none()
    if not classroom:
        raise NotFoundException(message=f"Classroom with ID '{id}' not found.", details={"classroom_id": id})

    stmt = select(Device).where(Device.classroom_id == id)
    count_stmt = select(func.count(Device.id)).where(Device.classroom_id == id)

    if device_type:
        stmt = stmt.where(Device.device_type.ilike(device_type.strip()))
        count_stmt = count_stmt.where(Device.device_type.ilike(device_type.strip()))

    if status_filter:
        stmt = stmt.where(Device.status == status_filter)
        count_stmt = count_stmt.where(Device.status == status_filter)

    total = db.execute(count_stmt).scalar_one()
    items = db.execute(
        stmt.order_by(Device.device_type.asc(), Device.brand.asc()).limit(limit).offset(offset)
    ).scalars().all()

    return ListResponse(
        data=[DeviceRead.model_validate(d) for d in items],
        meta=PaginationMeta(limit=limit, offset=offset, total=total),
    )

