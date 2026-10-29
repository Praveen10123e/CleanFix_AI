import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_active_user, require_faculty_or_admin
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.common import SingleResponse
from backend.app.schemas.complaint import ComplaintRead
from backend.app.schemas.troubleshooting import (
    StepResultSubmit,
    TroubleshootingComplaintCreate,
    TroubleshootingSessionCreate,
    TroubleshootingSessionRead,
    TroubleshootingStepRead,
)
from backend.app.services.troubleshooting_service import troubleshooting_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/troubleshooting", tags=["Troubleshooting"])


@router.post(
    "/sessions",
    response_model=SingleResponse[TroubleshootingSessionRead],
    status_code=status.HTTP_201_CREATED,
    summary="Start a new troubleshooting session",
    description="Initiates a guided, safe troubleshooting session for a classroom AV device based on observed symptoms. Faculty or Admin role required.",
)
def create_troubleshooting_session(
    payload: TroubleshootingSessionCreate,
    current_user: User = Depends(require_faculty_or_admin),
    db: Session = Depends(get_db),
):
    session = troubleshooting_service.create_session(db, current_user, payload)
    return SingleResponse(data=TroubleshootingSessionRead.model_validate(session))


@router.post(
    "/sessions/{id}/steps/next",
    response_model=SingleResponse[TroubleshootingStepRead],
    status_code=status.HTTP_200_OK,
    summary="Get next troubleshooting step",
    description="Fetches the current pending step or generates the next safe step from the rule catalogue after the previous step is completed.",
)
def get_next_step(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    step = troubleshooting_service.get_next_step(db, current_user, id)
    return SingleResponse(data=TroubleshootingStepRead.model_validate(step))


@router.post(
    "/sessions/{id}/steps/{step_id}/result",
    response_model=SingleResponse[TroubleshootingStepRead],
    status_code=status.HTTP_200_OK,
    summary="Record troubleshooting step outcome",
    description="Records faculty member's test result (SUCCESS, FAILED, SKIPPED) and optional notes for a step.",
)
def record_step_result(
    id: str,
    step_id: str,
    payload: StepResultSubmit,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    step = troubleshooting_service.record_step_result(db, current_user, id, step_id, payload)
    return SingleResponse(data=TroubleshootingStepRead.model_validate(step))


@router.post(
    "/sessions/{id}/complete",
    response_model=SingleResponse[TroubleshootingSessionRead],
    status_code=status.HTTP_200_OK,
    summary="Mark session resolved",
    description="Marks the troubleshooting session as successfully resolved. Does not change device status to repaired without technician confirmation.",
)
def complete_session(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    session = troubleshooting_service.complete_session(db, current_user, id)
    return SingleResponse(data=TroubleshootingSessionRead.model_validate(session))


@router.post(
    "/sessions/{id}/complaint",
    response_model=SingleResponse[ComplaintRead],
    status_code=status.HTTP_201_CREATED,
    summary="Escalate unresolved session to technician complaint",
    description="Closes the troubleshooting session as ESCALATED_TO_COMPLAINT and creates a high/medium priority repair complaint for AV technicians.",
)
def escalate_session(
    id: str,
    payload: TroubleshootingComplaintCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    complaint = troubleshooting_service.escalate_to_complaint(db, current_user, id, payload)
    return SingleResponse(data=ComplaintRead.model_validate(complaint))

