"""Pydantic data models for the CleanFix AI Diagnostic Subsystem."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class DeviceType(str, Enum):
    PROJECTOR = "projector"
    MICROPHONE = "microphone"
    SMART_BOARD = "smart_board"


class DecisionType(str, Enum):
    ASK_QUESTION = "ask_question"
    NEXT_STEP = "next_step"
    RESOLVED = "resolved"
    ESCALATE = "escalate"


class StepResultStatus(str, Enum):
    RESOLVED = "resolved"
    NOT_RESOLVED = "not_resolved"
    UNKNOWN = "unknown"
    UNABLE_TO_PERFORM = "unable_to_perform"


class RetrievalStatus(str, Enum):
    FOUND = "found"
    NO_MATCH = "no_match"
    FAILED = "failed"


class SafetyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class QuestionInputType(str, Enum):
    SINGLE_CHOICE = "single_choice"
    BOOLEAN = "boolean"
    TEXT = "text"


# --- Retrieval Models (AI Dev 1 Interface) ---

class EvidenceItem(BaseModel):
    """A single retrieved evidence chunk from manual documentation."""
    document_id: str = Field(description="Unique document ID (e.g. UUID or doc slug)")
    title: str = Field(description="Title of the manual or document")
    page_number: int | None = Field(default=None, description="Page number within source")
    chunk_id: str = Field(description="Specific chunk ID")
    text: str = Field(description="Extracted chunk text content")
    relevance_score: float = Field(ge=0.0, le=1.0, description="Relevance score (0.0 to 1.0)")


class RetrievalResult(BaseModel):
    """The contract returned by AI Dev 1 retrieve_evidence()."""
    query: str
    device_context: dict[str, Any] = Field(default_factory=dict)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    retrieval_status: RetrievalStatus = RetrievalStatus.FOUND


# --- Session Context Models (Backend Interface) ---

class StepHistoryItem(BaseModel):
    """A diagnostic step previously executed by faculty."""
    step_id: str = Field(description="Step identifier assigned by backend")
    action_id: str | None = Field(default=None, description="Approved Action Registry ID")
    instruction: str = Field(description="Instruction provided to user")
    result_status: StepResultStatus = Field(description="Outcome reported by user")
    user_feedback: str | None = Field(default=None, description="Optional user comments or observations")
    timestamp: str | None = Field(default=None, description="ISO 8601 timestamp")


class QuestionHistoryItem(BaseModel):
    """A question previously asked and answered."""
    question_id: str = Field(description="Question identifier")
    question_text: str = Field(description="Question text presented to user")
    answer: str = Field(description="User selected answer or text")


class SessionContext(BaseModel):
    """Structured session state supplied by the backend."""
    session_id: str
    device_id: str
    device_type: str = Field(description="'projector', 'microphone', or 'smart_board'")
    brand: str | None = None
    model: str | None = None
    device_configuration: dict[str, Any] | None = Field(default_factory=dict)
    original_symptom: str = Field(description="Original user-reported symptom")
    previous_steps: list[StepHistoryItem] = Field(default_factory=list)
    previous_questions: list[QuestionHistoryItem] = Field(default_factory=list)
    current_diagnostic_state: str | None = None
    available_retrieved_evidence: list[EvidenceItem] | None = Field(default_factory=list)
    permitted_action_categories: list[str] = Field(default_factory=list)
    applicable_safety_constraints: list[str] = Field(default_factory=list)


# --- Diagnostic Output Components ---

class NextStep(BaseModel):
    """Structured diagnostic action recommended to the user."""
    action_id: str | None = Field(default=None, description="Action ID from approved registry")
    instruction: str = Field(description="Clear, non-technical instructions")
    reason: str = Field(description="Rationale for why this step matters")
    expected_observation: str = Field(description="What the user should observe")
    safety_level: SafetyLevel = Field(default=SafetyLevel.LOW)
    requires_confirmation: bool = Field(default=True)


class DiagnosticQuestion(BaseModel):
    """Targeted question to reduce diagnostic uncertainty."""
    question_id: str
    text: str
    input_type: QuestionInputType = QuestionInputType.SINGLE_CHOICE
    options: list[str] | None = Field(
        default_factory=lambda: ["Yes", "No", "Not sure", "Unable to perform"]
    )


class SourceReference(BaseModel):
    """Grounding citation to retrieved documentation."""
    document_id: str
    page_number: int | None = None
    title: str | None = None
    chunk_id: str | None = None
    relevance_score: float | None = None
    chunk_id: Optional[str] = None
    relevance_score: Optional[float] = None


class NormalizedSymptom(BaseModel):
    """Structured interpretation of natural language symptom."""
    device_type: str
    symptom_category: str
    observed_status: str
    probable_causes: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    original_symptom: str


# --- Main Diagnosis Output ---

class DiagnosisResult(BaseModel):
    """The authoritative structured output produced by generate_diagnosis()."""
    decision: DecisionType
    reasoning_summary: str
    next_step: NextStep | None = None
    question: DiagnosticQuestion | None = None
    resolution_summary: str | None = None
    escalation_reason: str | None = None
    sources: list[SourceReference] = Field(default_factory=list)
    uncertainty: str | None = None
    normalized_symptom: NormalizedSymptom | None = None

    @model_validator(mode="after")
    def validate_decision_consistency(self) -> "DiagnosisResult":
        """Enforces schema consistency rules per decision type."""
        if self.decision == DecisionType.NEXT_STEP:
            if not self.next_step:
                raise ValueError("next_step must be provided when decision is 'next_step'")
            if self.next_step.safety_level == SafetyLevel.HIGH:
                raise ValueError("High-risk physical steps cannot be proposed to users")

        elif self.decision == DecisionType.ASK_QUESTION:
            if not self.question:
                raise ValueError("question must be provided when decision is 'ask_question'")

        elif self.decision == DecisionType.RESOLVED:
            if not self.resolution_summary:
                raise ValueError("resolution_summary must be provided when decision is 'resolved'")
            # When resolved, there should not be a next step
            self.next_step = None

        elif self.decision == DecisionType.ESCALATE:
            if not self.escalation_reason:
                raise ValueError("escalation_reason must be provided when decision is 'escalate'")
            self.next_step = None

        return self

