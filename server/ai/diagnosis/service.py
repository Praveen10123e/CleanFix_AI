"""Service interface for CleanFix AI Diagnostic Engine.

Provides the shared function `generate_diagnosis` invoked by the FastAPI backend.
"""


from server.ai.diagnosis.llm_client import LLMClient
from server.ai.diagnosis.models import (
    DiagnosisResult,
    RetrievalResult,
    SessionContext,
)
from server.ai.diagnosis.orchestrator import DiagnosticOrchestrator


def generate_diagnosis(
    session_context: SessionContext,
    evidence: RetrievalResult | None = None,
    llm_client: LLMClient | None = None,
) -> DiagnosisResult:
    """
    Main entry point for generating diagnostic reasoning and safe action selection.

    Args:
        session_context: Authoritative session state from the backend.
        evidence: Retrieved documentation chunks from AI Developer 1.
        llm_client: Optional custom LLM client (defaults to configured provider / mock).

    Returns:
        DiagnosisResult: Validated Pydantic output containing next_step, question,
                         resolution, or escalation.
    """
    orchestrator = DiagnosticOrchestrator(llm_client=llm_client)
    return orchestrator.orchestrate(session_context=session_context, evidence=evidence)

