import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.dependencies import require_admin
from backend.app.core.exceptions import ConflictException, NotFoundException
from backend.app.db.session import get_db
from backend.app.models.audit_log import AuditLog
from backend.app.models.enums import UserRole
from backend.app.models.user import User
from backend.app.schemas.common import ListResponse, PaginationMeta, SingleResponse
from backend.app.schemas.report import ReportSummaryData
from backend.app.schemas.user import UserCreate, UserRead, UserUpdate
from backend.app.services.report_service import generate_report_summary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Administration"])


@router.post(
    "/users",
    response_model=SingleResponse[UserRead],
    status_code=status.HTTP_201_CREATED,
    summary="Provision a new user",
    description="Admin creates and provisions an authorized user with designated role. Only administrators can perform this action.",
)
def create_user(
    payload: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    normalized_email = payload.email.strip().lower()

    # Check for existing user email
    stmt = select(User).where(User.email == normalized_email)
    existing = db.execute(stmt).scalar_one_or_none()
    if existing:
        raise ConflictException(
            message=f"User with email '{normalized_email}' already exists.",
            details={"email": normalized_email},
        )

    # Check google_sub uniqueness if provided
    if payload.google_sub:
        stmt_sub = select(User).where(User.google_sub == payload.google_sub.strip())
        if db.execute(stmt_sub).scalar_one_or_none():
            raise ConflictException(
                message="User with this Google identity already registered.",
                details={"google_sub": payload.google_sub},
            )

    new_user = User(
        email=normalized_email,
        name=payload.name.strip(),
        role=payload.role,
        google_sub=payload.google_sub.strip() if payload.google_sub else None,
        is_active=True,
    )
    db.add(new_user)
    db.flush()

    # Record audit log
    audit = AuditLog(
        actor_id=current_user.id,
        action="USER_PROVISIONED",
        entity_type="USER",
        entity_id=new_user.id,
    )
    db.add(audit)
    db.commit()
    db.refresh(new_user)

    logger.info("Admin %s provisioned user: %s [%s]", current_user.email, new_user.email, new_user.role.value)
    return SingleResponse(data=UserRead.model_validate(new_user))


@router.get(
    "/users",
    response_model=ListResponse[UserRead],
    status_code=status.HTTP_200_OK,
    summary="List provisioned users",
    description="Retrieves a paginated list of provisioned users, filterable by role and active status. Admin only.",
)
def list_users(
    role: Optional[UserRole] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    stmt = select(User)
    count_stmt = select(func.count(User.id))

    if role is not None:
        stmt = stmt.where(User.role == role)
        count_stmt = count_stmt.where(User.role == role)

    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
        count_stmt = count_stmt.where(User.is_active == is_active)

    total = db.execute(count_stmt).scalar_one()
    items = db.execute(stmt.order_by(User.created_at.desc()).limit(limit).offset(offset)).scalars().all()

    return ListResponse(
        data=[UserRead.model_validate(u) for u in items],
        meta=PaginationMeta(limit=limit, offset=offset, total=total),
    )


@router.patch(
    "/users/{id}",
    response_model=SingleResponse[UserRead],
    status_code=status.HTTP_200_OK,
    summary="Update user role or status",
    description="Updates a user's role, name, or active status (deactivation). Admin only.",
)
def update_user(
    id: str,
    payload: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    stmt = select(User).where(User.id == id)
    user = db.execute(stmt).scalar_one_or_none()
    if not user:
        raise NotFoundException(message=f"User with ID '{id}' not found.", details={"user_id": id})

    if payload.name is not None:
        user.name = payload.name.strip()
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active

    audit = AuditLog(
        actor_id=current_user.id,
        action="USER_UPDATED",
        entity_type="USER",
        entity_id=user.id,
    )
    db.add(audit)
    db.commit()
    db.refresh(user)

    logger.info("Admin %s updated user %s", current_user.email, user.email)
    return SingleResponse(data=UserRead.model_validate(user))


@router.get(
    "/reports/summary",
    response_model=SingleResponse[ReportSummaryData],
    status_code=status.HTTP_200_OK,
    summary="Get AV equipment and maintenance report summary",
    description="Returns dynamic database-derived metrics on classroom AV equipment, device breakdown, complaints, and repairs. Admin only.",
)
def get_reports_summary(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    summary_data = generate_report_summary(db)
    return SingleResponse(data=summary_data)

