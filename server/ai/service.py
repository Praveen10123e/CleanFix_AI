"""Integration Service for CleanFix AI RAG Retrieval and Diagnosis Engine.

Coordinates the end-to-end troubleshooting workflow:
1. Accepts the current session context.
2. Builds an information-rich retrieval query and device metadata context.
3. Retrieves relevant manual evidence from the BM25 index.
4. Passes the typed RetrievalResult to generate_diagnosis().
5. Returns the structured DiagnosisResult.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from server.ai.diagnosis.llm_client import LLMClient
from server.ai.diagnosis.models import (
    DiagnosisResult,
    RetrievalResult,
    RetrievalStatus,
    SessionContext,
)
from server.ai.diagnosis.service import generate_diagnosis
from server.ai.retrieval.retriever import (
    DEFAULT_INDEX,
    BM25Retriever,
    retrieve_evidence,
)
from server.ai.safety.validator import SafetyValidator

logger = logging.getLogger(__name__)


def build_device_context(session_context: SessionContext) -> dict[str, Any]:
    """Constructs device metadata dictionary for retrieval filtering.

    Used by BM25Retriever to match chunks associated with the specific
    device_type, brand, and model when provided.
    """
    context: dict[str, Any] = {}
    if session_context.device_type:
        context["device_type"] = session_context.device_type
    if session_context.brand:
        context["brand"] = session_context.brand
    if session_context.model:
        context["model"] = session_context.model
    if session_context.device_configuration:
        for k, v in session_context.device_configuration.items():
            if v is not None:
                context[k] = v
    return context


def build_retrieval_query(session_context: SessionContext) -> str:
    """Constructs an information-rich retrieval query from session context.

    Combines:
    - Target device terms (brand, model, device_type)
    - User's original reported symptom
    - Key contextual answers from previous clarifying questions
    - Relevant faculty feedback from previous steps
    """
    query_parts: list[str] = []

    # 1. Device identity terms
    device_terms: list[str] = []
    if session_context.brand:
        device_terms.append(session_context.brand)
    if session_context.model:
        device_terms.append(session_context.model)
    if session_context.device_type:
        device_terms.append(session_context.device_type)

    # 2. Original symptom description
    symptom_text = SafetyValidator.sanitize_untrusted_input(session_context.original_symptom or "").strip()

    for term in device_terms:
        if term.lower() not in symptom_text.lower():
            query_parts.append(term)
    if symptom_text:
        query_parts.append(symptom_text)

    # 3. Add relevant context from previous questions answered
    for q in session_context.previous_questions:
        ans = (q.answer or "").strip()
        # Include informative answers (e.g., "HDMI cable", "Windows Laptop", "Solid blue")
        if ans and ans.lower() not in ("yes", "no", "not sure", "unable to perform"):
            query_parts.append(ans)

    # 4. Add user feedback from previous steps if available
    for s in session_context.previous_steps:
        if s.user_feedback:
            feedback_clean = SafetyValidator.sanitize_untrusted_input(s.user_feedback).strip()
            if feedback_clean and feedback_clean.lower() not in ("yes", "no", "resolved", "not working"):
                query_parts.append(feedback_clean)

    # De-duplicate words while preserving order for clean BM25 token coverage
    raw_query = " ".join(query_parts)
    tokens = raw_query.split()
    seen = set()
    deduped = []
    for tok in tokens:
        lower_tok = tok.lower()
        if lower_tok not in seen:
            seen.add(lower_tok)
            deduped.append(tok)

    return " ".join(deduped) if deduped else (session_context.original_symptom or "")


def diagnose_session(
    session_context: SessionContext | dict[str, Any],
    *,
    index_path: str | Path | None = None,
    top_k: int = 5,
    retriever: BM25Retriever | None = None,
    llm_client: LLMClient | None = None,
) -> DiagnosisResult:
    """Primary integration service orchestrating RAG retrieval and diagnosis.

    Flow:
    1. Validates and normalizes session context.
    2. Builds targeted retrieval query and device metadata context.
    3. Retrieves relevant manual evidence from the BM25 index.
    4. Passes the actual RetrievalResult to generate_diagnosis().
    5. Returns the structured DiagnosisResult.

    Safety:
    - Detects critical hazards immediately and halts self-service troubleshooting.
    - Missing index or retrieval failure produces safe fallback without crashing.
    - Does not mutate input session context records.
    """
    # 1. Ensure valid SessionContext model
    if isinstance(session_context, dict):
        ctx = SessionContext.model_validate(session_context)
    else:
        ctx = session_context

    # 2. Check for immediate critical hazards (smoke, sparks, burning smells, exposed wires)
    sanitized_symptom = SafetyValidator.sanitize_untrusted_input(ctx.original_symptom or "")
    if SafetyValidator.validate_symptom_safety(sanitized_symptom):
        empty_result = RetrievalResult(
            query=sanitized_symptom,
            device_context=build_device_context(ctx),
            evidence=[],
            retrieval_status=RetrievalStatus.NO_MATCH,
        )
        return generate_diagnosis(ctx, evidence=empty_result, llm_client=llm_client)

    # 3. Build query and device metadata context
    query = build_retrieval_query(ctx)
    device_context = build_device_context(ctx)

    # 4. Retrieve relevant evidence from BM25 index
    try:
        if retriever is not None:
            retrieval_result = retriever.retrieve(query=query, device_context=device_context)
        else:
            retrieval_result = retrieve_evidence(
                query=query,
                device_context=device_context,
                index_path=index_path or DEFAULT_INDEX,
                top_k=top_k,
            )
    except Exception:
        logger.exception("Retrieval failed with unexpected error")
        retrieval_result = RetrievalResult(
            query=query,
            device_context=device_context,
            evidence=[],
            retrieval_status=RetrievalStatus.FAILED,
        )

    # 5. Invoke diagnosis engine with session context and retrieved evidence
    diagnosis_result = generate_diagnosis(
        session_context=ctx,
        evidence=retrieval_result,
        llm_client=llm_client,
    )

    return diagnosis_result


# Public aliases
run_diagnostic_pipeline = diagnose_session
diagnose = diagnose_session
