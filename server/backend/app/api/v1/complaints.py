import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import (
    get_current_active_user,
    require_admin,
    require_technician_or_admin,
)
from backend.app.db.session import get_db
from backend.app.models.enums import ComplaintStatus
from backend.app.models.user import User
from backend.app.schemas.common import ListResponse, PaginationMeta, SingleResponse
from backend.app.schemas.complaint import (
    ComplaintAssignmentUpdate,
    ComplaintCreate,
    ComplaintRead,
    ComplaintResolutionCreate,
    ComplaintStatusUpdate,
)
from backend.app.services.complaint_service import complaint_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.post(
    "",
    response_model=SingleResponse[ComplaintRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new complaint",
    description="Submits a complaint for a malfunctioning classroom AV device.",
)
def create_complaint(
    payload: ComplaintCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    complaint = complaint_service.create_complaint(db, current_user, payload)
    return SingleResponse(data=ComplaintRead.model_validate(complaint))


@router.get(
    "",
    response_model=ListResponse[ComplaintRead],
    status_code=status.HTTP_200_OK,
    summary="List complaints",
    description="Retrieves complaints based on caller role: Faculty sees reported complaints; Technicians see assigned/all; Admins see all.",
)
def list_complaints(
    status_filter: Optional[ComplaintStatus] = Query(None, alias="status"),
    classroom_id: Optional[str] = Query(None),
    device_id: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assigned_to_me: Optional[bool] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    complaints, total = complaint_service.list_complaints(
        db=db,
        user=current_user,
        status_filter=status_filter,
        classroom_id=classroom_id,
        device_id=device_id,
        priority=priority,
        assigned_to_me=assigned_to_me,
        limit=limit,
        offset=offset,
    )
    return ListResponse(
        data=[ComplaintRead.model_validate(c) for c in complaints],
        meta=PaginationMeta(limit=limit, offset=offset, total=total),
    )


@router.get(
    "/{id}",
    response_model=SingleResponse[ComplaintRead],
    status_code=status.HTTP_200_OK,
    summary="Get complaint details",
    description="Retrieves a single complaint and its repair record (if resolved).",
)
def get_complaint(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    complaint = complaint_service.get_complaint(db, current_user, id)
    return SingleResponse(data=ComplaintRead.model_validate(complaint))


@router.patch(
    "/{id}/assignment",
    response_model=SingleResponse[ComplaintRead],
    status_code=status.HTTP_200_OK,
    summary="Assign complaint to technician",
    description="Assigns an active technician to investigate and repair the complaint. Admin only.",
)
def assign_complaint(
    id: str,
    payload: ComplaintAssignmentUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    complaint = complaint_service.assign_complaint(db, current_user, id, payload)
    return SingleResponse(data=ComplaintRead.model_validate(complaint))


@router.patch(
    "/{id}/status",
    response_model=SingleResponse[ComplaintRead],
    status_code=status.HTTP_200_OK,
    summary="Update complaint progress status",
    description="Updates status of an assigned complaint (e.g., IN_PROGRESS). Allowed for assigned technician or Admin.",
)
def update_complaint_status(
    id: str,
    payload: ComplaintStatusUpdate,
    current_user: User = Depends(require_technician_or_admin),
    db: Session = Depends(get_db),
):
    complaint = complaint_service.update_complaint_status(db, current_user, id, payload)
    return SingleResponse(data=ComplaintRead.model_validate(complaint))


@router.post(
    "/{id}/resolution",
    response_model=SingleResponse[ComplaintRead],
    status_code=status.HTTP_200_OK,
    summary="Submit repair resolution",
    description="Files a confirmed repair record, marks the complaint as RESOLVED, and restores device status to OPERATIONAL. Allowed for assigned technician or Admin.",
)
def resolve_complaint(
    id: str,
    payload: ComplaintResolutionCreate,
    current_user: User = Depends(require_technician_or_admin),
    db: Session = Depends(get_db),
):
    complaint = complaint_service.resolve_complaint(db, current_user, id, payload)
    return SingleResponse(data=ComplaintRead.model_validate(complaint))

