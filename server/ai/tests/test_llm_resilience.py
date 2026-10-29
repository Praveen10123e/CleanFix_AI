"""Tests for LLM resilience, provider error recovery, and maximum step limits."""

from server.ai.diagnosis.llm_client import MockLLMClient
from server.ai.diagnosis.models import (
    DecisionType,
    QuestionHistoryItem,
    SessionContext,
    StepHistoryItem,
    StepResultStatus,
)
from server.ai.diagnosis.service import generate_diagnosis


def test_provider_503_error_triggers_safe_fallback():
    mock_client = MockLLMClient(simulate_provider_error=True)
    ctx = SessionContext(
        session_id="sess-resilience-01",
        device_id="dev-sb-01",
        device_type="smart_board",
        original_symptom="Interactive board not responding to touch.",
        previous_questions=[
            QuestionHistoryItem(question_id="Q_SMART_IMAGE_VISIBLE", question_text="Image?", answer="Yes")
        ],
    )

    result = generate_diagnosis(ctx, llm_client=mock_client)

    assert result is not None
    assert result.decision == DecisionType.NEXT_STEP
    assert result.next_step is not None
    assert "service unavailable recovered" in (result.uncertainty or "").lower()


def test_max_unresolved_step_limit_escalation():
    """Verify that after 5 failed steps, engine automatically halts and escalates."""
    steps = [
        StepHistoryItem(
            step_id=f"step-{i}",
            action_id=f"ACT_{i}",
            instruction=f"Action step {i}",
            result_status=StepResultStatus.NOT_RESOLVED,
            user_feedback="Still not working.",
        )
        for i in range(1, 6)
    ]

    ctx = SessionContext(
        session_id="sess-max-steps",
        device_id="dev-proj-01",
        device_type="projector",
        original_symptom="Projector shows blank screen.",
        previous_steps=steps,
    )

    result = generate_diagnosis(ctx)

    assert result.decision == DecisionType.ESCALATE
    assert "Exceeded maximum self-service" in result.reasoning_summary
    assert "IT/AV engineering" in result.escalation_reason
    assert result.next_step is None


def test_unable_to_perform_all_actions_escalates():
    """Verify that if user cannot perform any remaining actions, engine escalates cleanly."""
    ctx = SessionContext(
        session_id="sess-unable-all",
        device_id="dev-proj-01",
        device_type="projector",
        original_symptom="Projector screen black.",
        previous_steps=[
            StepHistoryItem(
                step_id="step-01",
                action_id="PROJ_SOURCE_SEARCH",
                instruction="Check source",
                result_status=StepResultStatus.UNABLE_TO_PERFORM,
            ),
            StepHistoryItem(
                step_id="step-02",
                action_id="PROJ_LAPTOP_DUPLICATE_DISPLAY",
                instruction="Laptop duplicate",
                result_status=StepResultStatus.UNABLE_TO_PERFORM,
            ),
            StepHistoryItem(
                step_id="step-03",
                action_id="PROJ_CHECK_HDMI_CABLE_RESEAT",
                instruction="Check cable",
                result_status=StepResultStatus.UNABLE_TO_PERFORM,
            ),
            StepHistoryItem(
                step_id="step-04",
                action_id="PROJ_CHECK_POWER_LED",
                instruction="Check power LED",
                result_status=StepResultStatus.UNABLE_TO_PERFORM,
            ),
            StepHistoryItem(
                step_id="step-05",
                action_id="PROJ_CHECK_LENS_SHUTTER",
                instruction="Check lens shutter",
                result_status=StepResultStatus.UNABLE_TO_PERFORM,
            ),
        ],
    )

    result = generate_diagnosis(ctx)

    assert result.decision == DecisionType.ESCALATE
    assert result.escalation_reason is not None

