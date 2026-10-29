"""Deterministic Diagnostic Reasoning Mock Engine for CleanFix AI.

Implements all diagnostic reasoning, adaptive questioning, safe action selection,
source grounding, and workflow state transitions without requiring external LLM API keys.
Guarantees full compatibility with the shared test scenarios.
"""


from server.ai.diagnosis.action_selector import ActionSelector
from server.ai.diagnosis.models import (
    DecisionType,
    DiagnosisResult,
    RetrievalResult,
    SessionContext,
    StepResultStatus,
)
from server.ai.diagnosis.normalizer import SymptomNormalizer
from server.ai.diagnosis.question_selector import QuestionSelector
from server.ai.safety.constraints import MAX_UNRESOLVED_STEPS, is_safety_hazard
from server.ai.safety.validator import SafetyValidator


class MockDiagnosticEngine:
    """Deterministic, rule-grounded diagnostic engine for CleanFix AI."""

    @classmethod
    def diagnose(
        cls,
        session_context: SessionContext,
        evidence: RetrievalResult | None = None,
    ) -> DiagnosisResult:
        """
        Executes end-to-end diagnostic reasoning flow.
        """
        # Step 1: Sanitize input and check for immediate critical safety hazards
        sanitized_symptom = SafetyValidator.sanitize_untrusted_input(session_context.original_symptom)
        hazard = is_safety_hazard(sanitized_symptom)
        if hazard:
            hazard_type, message = hazard
            return DiagnosisResult(
                decision=DecisionType.ESCALATE,
                reasoning_summary=f"Critical safety hazard detected ({hazard_type}): {message}. Halting all troubleshooting immediately.",
                escalation_reason=(
                    f"Immediate physical hazard detected: {message}. "
                    "For your safety, do not touch the equipment or attempt further troubleshooting. "
                    "An emergency AV technician dispatch ticket has been created."
                ),
                sources=[],
                uncertainty=None,
            )

        # Step 2: Handle previous step outcome (State-based workflow transitions)
        if session_context.previous_steps:
            last_step = session_context.previous_steps[-1]

            # Rule: Confirmed resolution
            if last_step.result_status == StepResultStatus.RESOLVED:
                action_text = last_step.instruction
                feedback = f" User reported: '{last_step.user_feedback}'." if last_step.user_feedback else ""
                return DiagnosisResult(
                    decision=DecisionType.RESOLVED,
                    reasoning_summary=f"The reported issue was successfully resolved by previous action ({last_step.action_id or 'standard step'}).{feedback}",
                    resolution_summary=(
                        f"Troubleshooting complete. The equipment issue was resolved following step: "
                        f"'{action_text}'. Normal classroom operation restored."
                    ),
                    sources=[],
                    uncertainty=None,
                )

            # Rule: Step limit exhaustion
            if len(session_context.previous_steps) >= MAX_UNRESOLVED_STEPS:
                return DiagnosisResult(
                    decision=DecisionType.ESCALATE,
                    reasoning_summary=f"Exceeded maximum self-service troubleshooting limit ({MAX_UNRESOLVED_STEPS} steps).",
                    escalation_reason=(
                        f"All {MAX_UNRESOLVED_STEPS} standard self-service troubleshooting procedures "
                        "were attempted without resolving the issue. Escalating to on-campus IT/AV engineering "
                        "for physical inspection and hardware replacement."
                    ),
                    sources=[],
                    uncertainty=None,
                )

        # Step 3: Normalize natural-language symptom
        normalized = SymptomNormalizer.normalize(
            raw_symptom=sanitized_symptom,
            device_type_hint=session_context.device_type,
        )

        # Step 4: Check if adaptive clarifying question should be asked
        # Ask question if no steps have been executed and no question has been answered yet
        should_ask_question = (
            len(session_context.previous_steps) == 0
            and len(session_context.previous_questions) == 0
            and len(normalized.missing_information) > 1
        )

        if should_ask_question:
            question = QuestionSelector.select_question(session_context, normalized)
            if question:
                return DiagnosisResult(
                    decision=DecisionType.ASK_QUESTION,
                    reasoning_summary=(
                        f"Initial symptom interpretation '{normalized.symptom_category}' requires "
                        f"clarification on: {normalized.missing_information[0]}."
                    ),
                    question=question,
                    sources=[],
                    uncertainty=f"Unconfirmed: {', '.join(normalized.missing_information)}",
                    normalized_symptom=normalized,
                )

        # Step 5: Select next approved safe diagnostic action
        next_step, sources, reasoning = ActionSelector.select_action(session_context, evidence)

        # If no viable action remains, escalate
        if not next_step:
            return DiagnosisResult(
                decision=DecisionType.ESCALATE,
                reasoning_summary=reasoning or "No further approved safe actions available for user self-service.",
                escalation_reason=(
                    "Standard user-accessible diagnostic actions have been exhausted without resolving the problem. "
                    "Creating IT technician support ticket."
                ),
                sources=[],
                uncertainty=None,
                normalized_symptom=normalized,
            )

        # Step 6: Validate proposed step against safety rules and Action Registry
        is_valid_step, step_err = SafetyValidator.validate_proposed_step(
            step=next_step,
            device_type=session_context.device_type,
            permitted_categories=session_context.permitted_action_categories,
        )
        if not is_valid_step:
            # Deterministic safety fallback: escalate rather than recommending an invalid or unsafe step
            return DiagnosisResult(
                decision=DecisionType.ESCALATE,
                reasoning_summary=f"Safety policy rejected proposed step: {step_err}",
                escalation_reason="Diagnostic step could not meet strict safety policies. Escalating to IT staff.",
                sources=[],
                uncertainty=None,
                normalized_symptom=normalized,
            )

        # Step 7: Validate source citations against retrieved evidence
        if evidence:
            is_valid_sources, _ = SafetyValidator.validate_source_grounding(sources, evidence.evidence)
            if not is_valid_sources:
                # Discard invalid citations to prevent hallucination leakage
                sources = []

        # Return validated Next Step
        return DiagnosisResult(
            decision=DecisionType.NEXT_STEP,
            reasoning_summary=reasoning,
            next_step=next_step,
            sources=sources,
            uncertainty=(
                f"Candidate causes: {'; '.join(normalized.probable_causes[:2])}. "
                "Hardware cause remains unconfirmed until step observation."
            ),
            normalized_symptom=normalized,
        )

