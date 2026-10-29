import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from backend.app.core.dependencies import (
    get_current_active_user,
    require_technician_or_admin,
)
from backend.app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from backend.app.db.session import get_db
from backend.app.models.audit_log import AuditLog
from backend.app.models.classroom import Classroom
from backend.app.models.device import Device
from backend.app.models.device_history import DeviceHistory
from backend.app.models.enums import ChangeType, DeviceStatus
from backend.app.models.user import User
from backend.app.schemas.common import ListResponse, PaginationMeta, SingleResponse
from backend.app.schemas.device import DeviceCreate, DeviceRead, DeviceUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.post(
    "",
    response_model=SingleResponse[DeviceRead],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new device",
    description="Registers an AV device assigned to a classroom. Technician or Admin role required.",
)
def create_device(
    payload: DeviceCreate,
    current_user: User = Depends(require_technician_or_admin),
    db: Session = Depends(get_db),
):
    # Verify target classroom exists and is active
    stmt_room = select(Classroom).where(Classroom.id == payload.classroom_id)
    classroom = db.execute(stmt_room).scalar_one_or_none()
    if not classroom:
        raise NotFoundException(
            message=f"Target classroom with ID '{payload.classroom_id}' does not exist.",
            details={"classroom_id": payload.classroom_id},
        )

    # Check serial number uniqueness if provided
    if payload.serial_number:
        stmt_sn = select(Device).where(Device.serial_number == payload.serial_number.strip())
        if db.execute(stmt_sn).scalar_one_or_none():
            raise ConflictException(
                message=f"Device with serial number '{payload.serial_number}' already registered.",
                details={"serial_number": payload.serial_number},
            )

    device = Device(
        classroom_id=payload.classroom_id,
        device_type=payload.device_type.strip(),
        brand=payload.brand.strip(),
        model=payload.model.strip(),
        serial_number=payload.serial_number.strip() if payload.serial_number else None,
        status=payload.status,
    )
    db.add(device)
    db.flush()

    # Log device history
    history = DeviceHistory(
        device_id=device.id,
        changed_by=current_user.id,
        change_type=ChangeType.CREATED.value,
        previous_values=None,
        new_values={
            "classroom_id": device.classroom_id,
            "device_type": device.device_type,
            "brand": device.brand,
            "model": device.model,
            "serial_number": device.serial_number,
            "status": device.status.value,
        },
    )
    db.add(history)

    # Log audit
    audit = AuditLog(
        actor_id=current_user.id,
        action="DEVICE_REGISTERED",
        entity_type="DEVICE",
        entity_id=device.id,
    )
    db.add(audit)
    db.commit()
    db.refresh(device)

    logger.info("Device created: %s %s (id: %s) by %s", device.brand, device.model, device.id, current_user.email)
    return SingleResponse(data=DeviceRead.model_validate(device))


@router.get(
    "/{id}",
    response_model=SingleResponse[DeviceRead],
    status_code=status.HTTP_200_OK,
    summary="Get device details",
    description="Retrieves equipment specifications and operational status for a device.",
)
def get_device(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    stmt = select(Device).where(Device.id == id)
    device = db.execute(stmt).scalar_one_or_none()
    if not device:
        raise NotFoundException(message=f"Device with ID '{id}' not found.", details={"device_id": id})

    return SingleResponse(data=DeviceRead.model_validate(device))


@router.patch(
    "/{id}",
    response_model=SingleResponse[DeviceRead],
    status_code=status.HTTP_200_OK,
    summary="Update device status or specifications",
    description="Updates device status, location, or metadata, and records audit and history. Technician or Admin role required.",
)
def update_device(
    id: str,
    payload: DeviceUpdate,
    current_user: User = Depends(require_technician_or_admin),
    db: Session = Depends(get_db),
):
    stmt = select(Device).where(Device.id == id)
    device = db.execute(stmt).scalar_one_or_none()
    if not device:
        raise NotFoundException(message=f"Device with ID '{id}' not found.", details={"device_id": id})

    # Validate target classroom if updating location
    if payload.classroom_id is not None and payload.classroom_id != device.classroom_id:
        stmt_cr = select(Classroom).where(Classroom.id == payload.classroom_id)
        if not db.execute(stmt_cr).scalar_one_or_none():
            raise NotFoundException(
                message=f"Target classroom '{payload.classroom_id}' does not exist.",
                details={"classroom_id": payload.classroom_id},
            )

    # Validate serial number uniqueness
    if payload.serial_number is not None and payload.serial_number != device.serial_number:
        stmt_sn = select(Device).where(
            Device.serial_number == payload.serial_number.strip(),
            Device.id != id,
        )
        if db.execute(stmt_sn).scalar_one_or_none():
            raise ConflictException(
                message=f"Device with serial number '{payload.serial_number}' already registered.",
                details={"serial_number": payload.serial_number},
            )

    # Collect previous values
    prev_values = {
        "classroom_id": device.classroom_id,
        "device_type": device.device_type,
        "brand": device.brand,
        "model": device.model,
        "serial_number": device.serial_number,
        "status": device.status.value,
    }

    # Determine change type
    change_type = ChangeType.UPDATED.value
    if payload.status is not None and payload.status != device.status:
        change_type = ChangeType.STATUS_CHANGE.value
    elif payload.classroom_id is not None and payload.classroom_id != device.classroom_id:
        change_type = ChangeType.RELOCATED.value

    # Apply changes
    if payload.classroom_id is not None:
        device.classroom_id = payload.classroom_id
    if payload.device_type is not None:
        device.device_type = payload.device_type.strip()
    if payload.brand is not None:
        device.brand = payload.brand.strip()
    if payload.model is not None:
        device.model = payload.model.strip()
    if payload.serial_number is not None:
        device.serial_number = payload.serial_number.strip() if payload.serial_number else None
    if payload.status is not None:
        device.status = payload.status

    new_values = {
        "classroom_id": device.classroom_id,
        "device_type": device.device_type,
        "brand": device.brand,
        "model": device.model,
        "serial_number": device.serial_number,
        "status": device.status.value,
    }

    # Record history
    history = DeviceHistory(
        device_id=device.id,
        changed_by=current_user.id,
        change_type=change_type,
        previous_values=prev_values,
        new_values=new_values,
    )
    db.add(history)

    # Record audit log
    audit = AuditLog(
        actor_id=current_user.id,
        action="DEVICE_UPDATED",
        entity_type="DEVICE",
        entity_id=device.id,
    )
    db.add(audit)
    db.commit()
    db.refresh(device)

    logger.info("Device updated: %s (change_type: %s) by %s", device.id, change_type, current_user.email)
    return SingleResponse(data=DeviceRead.model_validate(device))

