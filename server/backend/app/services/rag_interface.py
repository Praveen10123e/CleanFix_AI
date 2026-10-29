"""Future RAG and LLM diagnostic engine interface contract.

This module provides typed Pydantic data transfer structures and a pluggable
service interface enabling a future AI engineer to seamlessly integrate RAG
(Retrieval-Augmented Generation) and vector search without altering the database
schema or frontend API contracts.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.exceptions import NotFoundException
from backend.app.models.complaint import Complaint
from backend.app.models.device import Device
from backend.app.models.repair_record import RepairRecord
from backend.app.models.troubleshooting import (
    TroubleshootingSession,
    TroubleshootingStep,
)


class RAGDeviceContext(BaseModel):
    """Contextual metadata regarding the target AV equipment."""

    device_id: str
    classroom_id: str
    classroom_room_number: str
    classroom_building: str
    device_type: str
    brand: str
    model: str
    serial_number: Optional[str] = None
    status: str
    verified_specifications: Dict[str, Any] = Field(default_factory=dict)


class RAGStepContext(BaseModel):
    """Historical record of an individual troubleshooting step performed by faculty."""

    step_number: int
    instruction: str
    reason: Optional[str] = None
    result: Optional[str] = None
    result_note: Optional[str] = None


class RAGRepairHistoryContext(BaseModel):
    """Historical confirmed repair actions on this equipment by AV technicians."""

    repair_id: str
    complaint_id: str
    confirmed_cause: str
    repair_action: str
    parts_replaced: Optional[str] = None
    resolved_at: Optional[str] = None


class RAGTroubleshootingContext(BaseModel):
    """Complete serialized payload passed to a future RAG / LLM diagnostic pipeline."""

    session_id: str
    faculty_id: str
    symptom_text: str
    current_step: int
    status: str
    device: RAGDeviceContext
    previous_steps: List[RAGStepContext] = Field(default_factory=list)
    repair_history: List[RAGRepairHistoryContext] = Field(default_factory=list)


class RAGDiagnosticResult(BaseModel):
    """Standardized output structure expected from a future RAG / LLM diagnostic engine."""

    session_id: str
    next_step_instruction: str
    reason: str
    is_terminal: bool = False
    recommended_action: str = "EXECUTE_STEP"  # EXECUTE_STEP, RESOLVED, ESCALATE_TO_TECHNICIAN
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    source_chunk_ids: List[str] = Field(default_factory=list)


def build_rag_troubleshooting_context(db: Session, session_id: str) -> RAGTroubleshootingContext:
    """Build and serialize the comprehensive context required by a future RAG pipeline."""
    stmt_session = select(TroubleshootingSession).where(TroubleshootingSession.id == session_id)
    session = db.execute(stmt_session).scalar_one_or_none()
    if not session:
        raise NotFoundException(message=f"Session with ID '{session_id}' not found.")

    device: Device = session.device
    classroom = device.classroom

    # 1. Device Context
    device_ctx = RAGDeviceContext(
        device_id=device.id,
        classroom_id=classroom.id,
        classroom_room_number=classroom.room_number,
        classroom_building=classroom.building,
        device_type=device.device_type,
        brand=device.brand,
        model=device.model,
        serial_number=device.serial_number,
        status=device.status.value,
        verified_specifications={},
    )

    # 2. Previous Steps Context
    stmt_steps = select(TroubleshootingStep).where(
        TroubleshootingStep.session_id == session.id
    ).order_by(TroubleshootingStep.step_number.asc())
    steps = db.execute(stmt_steps).scalars().all()

    previous_steps = [
        RAGStepContext(
            step_number=s.step_number,
            instruction=s.instruction,
            reason=s.reason,
            result=s.result.value if s.result else None,
            result_note=s.result_note,
        )
        for s in steps
    ]

    # 3. Repair History Context
    stmt_repairs = (
        select(RepairRecord)
        .join(Complaint, RepairRecord.complaint_id == Complaint.id)
        .where(Complaint.device_id == device.id)
        .order_by(RepairRecord.created_at.desc())
    )
    repairs = db.execute(stmt_repairs).scalars().all()

    repair_history = [
        RAGRepairHistoryContext(
            repair_id=r.id,
            complaint_id=r.complaint_id,
            confirmed_cause=r.confirmed_cause,
            repair_action=r.repair_action,
            parts_replaced=r.parts_replaced,
            resolved_at=r.created_at.isoformat() if r.created_at else None,
        )
        for r in repairs
    ]

    return RAGTroubleshootingContext(
        session_id=session.id,
        faculty_id=session.faculty_id,
        symptom_text=session.symptom_text,
        current_step=session.current_step,
        status=session.status.value,
        device=device_ctx,
        previous_steps=previous_steps,
        repair_history=repair_history,
    )


class BaseRAGDiagnosticService(ABC):
    """Abstract interface to be implemented by a future AI / RAG module."""

    @abstractmethod
    def retrieve_evidence(
        self,
        query: str,
        device_context: RAGDeviceContext,
        top_k: int = 3,
    ) -> Dict[str, Any]:
        """Retrieve relevant manual chunks from vector storage."""
        pass

    @abstractmethod
    def generate_diagnostic_step(
        self,
        context: RAGTroubleshootingContext,
    ) -> RAGDiagnosticResult:
        """Evaluate session history and evidence to produce the next actionable test step."""
        pass


class StubRAGDiagnosticService(BaseRAGDiagnosticService):
    """Pluggable stub ensuring backend operates seamlessly without an AI API or vector store."""

    def retrieve_evidence(
        self,
        query: str,
        device_context: RAGDeviceContext,
        top_k: int = 3,
    ) -> Dict[str, Any]:
        return {
            "query": query,
            "device": f"{device_context.brand} {device_context.model}",
            "chunks": [],
            "status": "RAG_NOT_CONFIGURED",
        }

    def generate_diagnostic_step(
        self,
        context: RAGTroubleshootingContext,
    ) -> RAGDiagnosticResult:
        return RAGDiagnosticResult(
            session_id=context.session_id,
            next_step_instruction="Verify power and cable connectivity.",
            reason="Fallback rule-based diagnosis when RAG engine is absent.",
            is_terminal=False,
            recommended_action="EXECUTE_STEP",
            confidence_score=1.0,
            source_chunk_ids=[],
        )

