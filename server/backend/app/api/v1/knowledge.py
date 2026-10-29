import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.dependencies import (
    get_current_active_user,
    require_technician_or_admin,
)
from backend.app.core.exceptions import NotFoundException
from backend.app.db.session import get_db
from backend.app.models.audit_log import AuditLog
from backend.app.models.enums import DocumentStatus, DocumentType
from backend.app.models.knowledge import KnowledgeDocument
from backend.app.models.user import User
from backend.app.schemas.common import ListResponse, PaginationMeta, SingleResponse
from backend.app.schemas.knowledge import KnowledgeDocumentCreate, KnowledgeDocumentRead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


@router.post(
    "/documents",
    response_model=SingleResponse[KnowledgeDocumentRead],
    status_code=status.HTTP_201_CREATED,
    summary="Register equipment manual metadata",
    description="Registers equipment documentation metadata. Admin or Technician role required. Does not run ingestion/RAG.",
)
def create_knowledge_document(
    payload: KnowledgeDocumentCreate,
    current_user: User = Depends(require_technician_or_admin),
    db: Session = Depends(get_db),
):
    doc = KnowledgeDocument(
        document_type=payload.document_type,
        title=payload.title.strip(),
        device_type=payload.device_type.strip(),
        brand=payload.brand.strip(),
        model=payload.model.strip(),
        file_path=payload.file_path.strip(),
        uploaded_by=current_user.id,
        status=DocumentStatus.PENDING,
    )
    db.add(doc)
    db.flush()

    audit = AuditLog(
        actor_id=current_user.id,
        action="DOCUMENT_METADATA_CREATED",
        entity_type="KNOWLEDGE_DOCUMENT",
        entity_id=doc.id,
    )
    db.add(audit)
    db.commit()
    db.refresh(doc)

    logger.info("Knowledge document metadata registered: %s (id: %s) by %s", doc.title, doc.id, current_user.email)
    return SingleResponse(data=KnowledgeDocumentRead.model_validate(doc))


@router.get(
    "/documents",
    response_model=ListResponse[KnowledgeDocumentRead],
    status_code=status.HTTP_200_OK,
    summary="List knowledge documents",
    description="Lists registered equipment manual metadata, filterable by device type and brand. Accessible to all active users.",
)
def list_knowledge_documents(
    device_type: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    stmt = select(KnowledgeDocument)
    count_stmt = select(func.count(KnowledgeDocument.id))

    if device_type:
        stmt = stmt.where(KnowledgeDocument.device_type.ilike(f"%{device_type.strip()}%"))
        count_stmt = count_stmt.where(KnowledgeDocument.device_type.ilike(f"%{device_type.strip()}%"))

    if brand:
        stmt = stmt.where(KnowledgeDocument.brand.ilike(f"%{brand.strip()}%"))
        count_stmt = count_stmt.where(KnowledgeDocument.brand.ilike(f"%{brand.strip()}%"))

    if model:
        stmt = stmt.where(KnowledgeDocument.model.ilike(f"%{model.strip()}%"))
        count_stmt = count_stmt.where(KnowledgeDocument.model.ilike(f"%{model.strip()}%"))

    total = db.execute(count_stmt).scalar_one()
    items = db.execute(
        stmt.order_by(KnowledgeDocument.created_at.desc()).limit(limit).offset(offset)
    ).scalars().all()

    return ListResponse(
        data=[KnowledgeDocumentRead.model_validate(d) for d in items],
        meta=PaginationMeta(limit=limit, offset=offset, total=total),
    )


@router.get(
    "/documents/{id}",
    response_model=SingleResponse[KnowledgeDocumentRead],
    status_code=status.HTTP_200_OK,
    summary="Get knowledge document metadata",
    description="Retrieves metadata for a registered equipment manual.",
)
def get_knowledge_document(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    stmt = select(KnowledgeDocument).where(KnowledgeDocument.id == id)
    doc = db.execute(stmt).scalar_one_or_none()
    if not doc:
        raise NotFoundException(message=f"Document with ID '{id}' not found.", details={"document_id": id})

    return SingleResponse(data=KnowledgeDocumentRead.model_validate(doc))

