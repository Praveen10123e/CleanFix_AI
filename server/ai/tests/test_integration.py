"""Integration tests for CleanFix AI RAG Retrieval + Diagnosis Subsystem.

Covers:
1. Relevant manual passage retrieved and passed to diagnosis engine.
2. Device metadata included in retrieval query and device_context.
3. No-match result reaches diagnosis engine safely without fabricated citations.
4. Missing or uninitialized index handled safely.
5. Retrieval exception does not crash integration service.
6. Evidence provenance (document_id, title, page_number, chunk_id, relevance_score) preserved.
7. Hazardous symptom triggers safe escalation immediately.
8. Unauthorized action rejected by safety validator.
9. Malformed LLM output or timeout triggers existing fallback behavior.
10. Repeated calls do not corrupt session state or duplicate records.
11. End-to-end smoke test: PDF manual -> text extraction -> BM25 indexing -> retrieval -> diagnosis -> safety validation.
"""

from __future__ import annotations

from pathlib import Path

import pymupdf
import pytest

from server.ai.diagnosis.llm_client import MockLLMClient
from server.ai.diagnosis.models import (
    DecisionType,
    NextStep,
    QuestionHistoryItem,
    SafetyLevel,
    SessionContext,
    StepHistoryItem,
    StepResultStatus,
)
from server.ai.retrieval.ingestion import ingest_pdf
from server.ai.safety.action_registry import ACTION_REGISTRY
from server.ai.safety.validator import SafetyValidator
from server.ai.service import (
    build_device_context,
    build_retrieval_query,
    diagnose_session,
)


def _create_synthetic_test_pdf(pdf_path: Path, text: str) -> Path:
    """Helper creating a minimal test PDF clearly labeled as synthetic test data."""
    doc = pymupdf.open()
    page = doc.new_page()
    labeled_text = (
        "--- SYNTHETIC TEST AV MANUAL (FOR AUTOMATED TESTING ONLY) ---\n"
        + text
    )
    rect = pymupdf.Rect(50, 50, 550, 750)
    page.insert_textbox(rect, labeled_text)
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


# --- Scenario 1: Relevant manual passage retrieved and passed to diagnosis engine ---
def test_scenario_01_relevant_passage_retrieved_and_diagnosed(tmp_path):
    pdf = tmp_path / "epson_test_manual.pdf"
    _create_synthetic_test_pdf(
        pdf,
        "Epson PowerLite 2250U Projector: If No Signal appears, press the Source Search button "
        "on the remote control or control panel to switch to HDMI 1 or Computer 1."
    )
    index_path = tmp_path / "chunks.jsonl"
    ingest_pdf(
        pdf,
        index_path,
        metadata={
            "document_id": "doc-epson-pl2250u-test",
            "title": "Epson PowerLite 2250U Test Guide",
            "device_type": "projector",
            "brand": "Epson",
            "model": "PowerLite 2250U",
        },
    )

    ctx = SessionContext(
        session_id="test-sess-01",
        device_id="proj-hall-1",
        device_type="projector",
        brand="Epson",
        model="PowerLite 2250U",
        original_symptom="The projector turns on and has a blue light, but shows No Signal when I connect my laptop.",
        previous_questions=[
            QuestionHistoryItem(
                question_id="Q_PROJ_POWER_LIGHT",
                question_text="Power light status",
                answer="Solid blue or green",
            )
        ],
    )

    result = diagnose_session(ctx, index_path=index_path)

    assert result.decision == DecisionType.NEXT_STEP
    assert result.next_step is not None
    assert result.next_step.action_id == "PROJ_SOURCE_SEARCH"
    assert len(result.sources) >= 1
    assert result.sources[0].document_id == "doc-epson-pl2250u-test"
    assert result.sources[0].page_number == 1
    assert "Epson PowerLite 2250U Test Guide" in result.reasoning_summary


# --- Scenario 2: Device metadata is included in the retrieval query when available ---
def test_scenario_02_device_metadata_included_in_query_and_context():
    ctx = SessionContext(
        session_id="test-sess-02",
        device_id="mic-podium-1",
        device_type="microphone",
        brand="Shure",
        model="BLX24/SM58",
        device_configuration={"channel": "Group 1 Channel 4"},
        original_symptom="Wireless microphone has no sound coming through the room speakers.",
        previous_questions=[
            QuestionHistoryItem(
                question_id="Q_MIC_SWITCH_STATE",
                question_text="Is the switch set to ON?",
                answer="Yes, toggled ON",
            )
        ],
        previous_steps=[
            StepHistoryItem(
                step_id="step-1",
                action_id="MIC_CHECK_BATTERY_LED",
                instruction="Check battery LED",
                result_status=StepResultStatus.NOT_RESOLVED,
                user_feedback="Battery LED is green, still completely silent",
            )
        ],
    )

    query = build_retrieval_query(ctx)
    query_lower = query.lower()

    # Query must contain brand, model terms, and device type
    assert "shure" in query_lower
    assert "microphone" in query_lower
    assert "blx24" in query_lower or "sm58" in query_lower
    # Context from history included
    assert "silent" in query_lower

    device_ctx = build_device_context(ctx)
    assert device_ctx["brand"] == "Shure"
    assert device_ctx["model"] == "BLX24/SM58"
    assert device_ctx["device_type"] == "microphone"
    assert device_ctx["channel"] == "Group 1 Channel 4"


# --- Scenario 3: A no-match result reaches the diagnosis engine correctly ---
def test_scenario_03_no_match_result_handled_without_fabricated_citations(tmp_path):
    # Index only contains projector manual
    pdf = tmp_path / "projector_manual.pdf"
    _create_synthetic_test_pdf(pdf, "Projector source search HDMI input selection.")
    index_path = tmp_path / "chunks.jsonl"
    ingest_pdf(pdf, index_path, metadata={"device_type": "projector"})

    # Session is for an unindexed microphone issue
    ctx = SessionContext(
        session_id="test-sess-03",
        device_id="mic-obscure-99",
        device_type="microphone",
        original_symptom="Obscure lavalier microphone vintage frequency mismatch.",
        previous_questions=[
            QuestionHistoryItem(
                question_id="Q_MIC_SWITCH_STATE",
                question_text="Is the switch ON?",
                answer="Yes",
            )
        ],
    )

    result = diagnose_session(ctx, index_path=index_path)

    # Must NOT fabricate citations
    assert result.sources == []
    assert result.decision == DecisionType.NEXT_STEP
    assert result.next_step is not None
    # Step must come from approved microphone actions
    assert result.next_step.action_id in ACTION_REGISTRY
    assert "No specific manual chunk found" in result.reasoning_summary


# --- Scenario 4: A missing or uninitialized index is handled safely ---
def test_scenario_04_missing_index_handled_safely(tmp_path):
    missing_index = tmp_path / "does_not_exist" / "missing_chunks.jsonl"

    ctx = SessionContext(
        session_id="test-sess-04",
        device_id="proj-101",
        device_type="projector",
        original_symptom="Projector screen says No Signal.",
        previous_questions=[
            QuestionHistoryItem(
                question_id="Q_PROJ_POWER_LIGHT",
                question_text="Power light?",
                answer="Solid blue or green",
            )
        ],
    )

    # Missing index must not raise FileNotFoundError or crash
    result = diagnose_session(ctx, index_path=missing_index)

    assert result is not None
    assert result.sources == []
    assert result.decision == DecisionType.NEXT_STEP
    assert result.next_step is not None
    assert result.next_step.action_id in ACTION_REGISTRY


# --- Scenario 5: A retrieval exception does not crash the integration service ---
def test_scenario_05_retrieval_exception_does_not_crash(monkeypatch):
    class CrashingRetriever:
        def retrieve(self, *args, **kwargs):
            raise RuntimeError("Simulated unrecoverable BM25 index read error / disk fault")

    ctx = SessionContext(
        session_id="test-sess-05",
        device_id="sb-room-2",
        device_type="smart_board",
        original_symptom="Interactive smart board does not respond to touch.",
        previous_questions=[
            QuestionHistoryItem(
                question_id="Q_SMART_IMAGE_VISIBLE",
                question_text="Is desktop visible?",
                answer="Yes",
            )
        ],
    )

    # Must catch exception and fallback gracefully
    result = diagnose_session(ctx, retriever=CrashingRetriever())

    assert result is not None
    assert result.sources == []
    assert result.decision == DecisionType.NEXT_STEP
    assert result.next_step.action_id in ACTION_REGISTRY
    assert "temporary fault" in result.reasoning_summary.lower()


# --- Scenario 6: Evidence provenance is preserved in resulting diagnosis ---
def test_scenario_06_evidence_provenance_preserved(tmp_path):
    pdf = tmp_path / "smartboard_guide.pdf"
    _create_synthetic_test_pdf(
        pdf,
        "SMART Board 7000R: Ensure the USB touch cable (USB Type-B to Type-A) is securely "
        "connected between your computer and the wall plate for touch response."
    )
    index_path = tmp_path / "chunks.jsonl"
    ingest_pdf(
        pdf,
        index_path,
        metadata={
            "document_id": "doc-smart-provenance-101",
            "title": "SMART Board 7000R User Guide",
            "device_type": "smart_board",
            "brand": "SMART",
            "model": "7000R",
        },
    )

    ctx = SessionContext(
        session_id="test-sess-06",
        device_id="sb-7000r-1",
        device_type="smart_board",
        brand="SMART",
        model="7000R",
        original_symptom="Board displays laptop screen but does not respond to touch or pen.",
        previous_questions=[
            QuestionHistoryItem(
                question_id="Q_SMART_IMAGE_VISIBLE",
                question_text="Can you see desktop?",
                answer="Yes",
            )
        ],
    )

    result = diagnose_session(ctx, index_path=index_path)

    assert result.decision == DecisionType.NEXT_STEP
    assert len(result.sources) >= 1
    src = result.sources[0]

    # Verify provenance fields
    assert src.document_id == "doc-smart-provenance-101"
    assert src.title == "SMART Board 7000R User Guide"
    assert src.page_number == 1
    assert src.chunk_id is not None
    assert src.chunk_id.startswith("doc-smart-provenance-101-p1-")
    assert src.relevance_score is not None
    assert 0.0 <= src.relevance_score <= 1.0


# --- Scenario 7: A hazardous symptom triggers safe escalation ---
@pytest.mark.parametrize(
    "hazardous_symptom,expected_marker",
    [
        ("There is smoke and burning smell coming from the ceiling projector!", "smoke"),
        ("I saw electric sparks when plugging into the classroom amplifier!", "sparks"),
        ("I felt an electric shock when touching the microphone casing!", "electric_shock"),
        ("The power cord is frayed with bare exposed wires near the floor!", "exposed_wiring"),
        ("Someone spilled water directly into the mixing board!", "liquid_damage"),
        ("The projector mount is loose and it looks like it is falling down!", "structural_hazard"),
    ],
)
def test_scenario_07_hazardous_symptom_triggers_immediate_escalation(hazardous_symptom, expected_marker):
    ctx = SessionContext(
        session_id="test-sess-07-hazard",
        device_id="proj-danger-1",
        device_type="projector",
        original_symptom=hazardous_symptom,
    )

    result = diagnose_session(ctx)

    assert result.decision == DecisionType.ESCALATE
    assert result.escalation_reason is not None
    assert "Immediate physical hazard detected" in result.escalation_reason
    assert result.next_step is None
    assert result.sources == []


# --- Scenario 8: An unauthorized action is rejected by the safety validator ---
def test_scenario_08_unauthorized_action_rejected_by_safety_validator():
    # 1. High risk action
    high_risk_step = NextStep(
        action_id="PROJ_SOURCE_SEARCH",
        instruction="Standard instruction.",
        reason="Standard reason.",
        expected_observation="Screen appears.",
        safety_level=SafetyLevel.HIGH,
    )
    is_valid, err = SafetyValidator.validate_proposed_step(high_risk_step, "projector")
    assert is_valid is False
    assert "High-risk" in err

    # 2. Prohibited keywords (opening chassis, unscrewing, replacing lamp)
    prohibited_step = NextStep(
        action_id="PROJ_SOURCE_SEARCH",
        instruction="Open the casing, unscrew the lamp cover, and replace the bulb.",
        reason="Check lamp.",
        expected_observation="Lamp replaced.",
        safety_level=SafetyLevel.LOW,
    )
    is_valid, err = SafetyValidator.validate_proposed_step(prohibited_step, "projector")
    assert is_valid is False
    assert "Violates safety policy" in err

    # 3. Unregistered action ID
    unregistered_step = NextStep(
        action_id="UNREGISTERED_ACTION_DO_NOT_ALLOW",
        instruction="Do something undocumented.",
        reason="Unknown reason.",
        expected_observation="Something happens.",
        safety_level=SafetyLevel.LOW,
    )
    is_valid, err = SafetyValidator.validate_proposed_step(unregistered_step, "projector")
    assert is_valid is False
    assert "not in the approved Action Registry" in err


# --- Scenario 9: Malformed LLM output or timeout triggers existing fallback ---
def test_scenario_09_llm_failure_triggers_resilient_fallback():
    ctx = SessionContext(
        session_id="test-sess-09",
        device_id="proj-fall-1",
        device_type="projector",
        original_symptom="Projector displays No Signal.",
        previous_questions=[
            QuestionHistoryItem(
                question_id="Q_PROJ_POWER_LIGHT",
                question_text="Power light?",
                answer="Solid blue or green",
            )
        ],
    )

    # Test malformed LLM output recovery
    malformed_client = MockLLMClient(simulate_malformed=True)
    res_malformed = diagnose_session(ctx, llm_client=malformed_client)
    assert res_malformed is not None
    assert res_malformed.decision == DecisionType.NEXT_STEP
    assert res_malformed.next_step.action_id in ACTION_REGISTRY
    assert "malformed" in (res_malformed.uncertainty or "").lower()

    # Test timeout recovery
    timeout_client = MockLLMClient(simulate_timeout=True, timeout_seconds=0.01)
    res_timeout = diagnose_session(ctx, llm_client=timeout_client)
    assert res_timeout is not None
    assert res_timeout.decision == DecisionType.NEXT_STEP
    assert res_timeout.next_step.action_id in ACTION_REGISTRY
    assert "timeout" in (res_timeout.uncertainty or "").lower() or "timed out" in (res_timeout.uncertainty or "").lower()


# --- Scenario 10: Repeated calls do not corrupt session state or duplicate records ---
def test_scenario_10_repeated_calls_preserve_session_state(tmp_path):
    pdf = tmp_path / "manual.pdf"
    _create_synthetic_test_pdf(pdf, "Press Source Search to switch HDMI port on projector.")
    index_path = tmp_path / "chunks.jsonl"
    ingest_pdf(pdf, index_path, metadata={"document_id": "doc-repeat", "device_type": "projector"})

    ctx = SessionContext(
        session_id="test-sess-10",
        device_id="proj-repeat-1",
        device_type="projector",
        original_symptom="Projector shows No Signal.",
        previous_questions=[
            QuestionHistoryItem(
                question_id="Q_PROJ_POWER_LIGHT",
                question_text="Power?",
                answer="Solid blue or green",
            )
        ],
        previous_steps=[
            StepHistoryItem(
                step_id="step-1",
                action_id="PROJ_CHECK_POWER_LED",
                instruction="Inspect power LED",
                result_status=StepResultStatus.NOT_RESOLVED,
                user_feedback="Power is solid green, still no signal.",
            )
        ],
    )

    initial_steps_count = len(ctx.previous_steps)
    initial_questions_count = len(ctx.previous_questions)
    initial_symptom = ctx.original_symptom

    # Call 1
    res1 = diagnose_session(ctx, index_path=index_path)

    # Call 2
    res2 = diagnose_session(ctx, index_path=index_path)

    # Verify input object integrity (no side-effect mutations on history lists)
    assert len(ctx.previous_steps) == initial_steps_count
    assert len(ctx.previous_questions) == initial_questions_count
    assert ctx.original_symptom == initial_symptom

    # Results must be consistent
    assert res1.decision == res2.decision
    assert res1.next_step.action_id == res2.next_step.action_id
    assert res1.sources == res2.sources


# --- Scenario 11: Offline End-to-End Smoke Test ---
def test_offline_end_to_end_smoke_test(tmp_path):
    """Full pipeline smoke test:

    PDF manual -> text extraction and chunking -> BM25 indexing ->
    evidence retrieval -> generate_diagnosis() -> safety validation -> structured result.
    """
    manual_pdf = tmp_path / "synthetic_epson_manual.pdf"
    _create_synthetic_test_pdf(
        manual_pdf,
        "Epson PowerLite 2250U Official Troubleshooting Section: "
        "When connecting a laptop via HDMI and 'No Signal' appears on screen, "
        "press the 'Source Search' button on the projector remote control. "
        "This cycles through inputs until HDMI 1 is locked. "
        "Also verify that Windows Key + P is set to Duplicate."
    )

    # 1. Text extraction and chunking -> BM25 indexing
    index_file = tmp_path / "knowledge_index.jsonl"
    chunks_created = ingest_pdf(
        manual_pdf,
        index_file,
        metadata={
            "document_id": "synthetic-epson-pl2250u",
            "title": "Epson PowerLite 2250U Synthetic Test Manual",
            "device_type": "projector",
            "brand": "Epson",
            "model": "PowerLite 2250U",
        },
    )
    assert chunks_created >= 1
    assert index_file.exists()

    # 2. Troubleshooting session setup
    session = SessionContext(
        session_id="smoke-session-001",
        device_id="hall-a-proj",
        device_type="projector",
        brand="Epson",
        model="PowerLite 2250U",
        original_symptom="The projector turns on with blue light, but shows No Signal when I connect my laptop.",
        previous_questions=[
            QuestionHistoryItem(
                question_id="Q_PROJ_POWER_LIGHT",
                question_text="Power light status?",
                answer="Solid blue or green",
            )
        ],
    )

    # 3. Evidence retrieval + generate_diagnosis() via integration service
    diagnosis = diagnose_session(session, index_path=index_file)

    # 4. Safety validation on the returned action
    assert diagnosis.decision == DecisionType.NEXT_STEP
    assert diagnosis.next_step is not None
    is_safe, safety_err = SafetyValidator.validate_proposed_step(
        diagnosis.next_step,
        device_type=session.device_type,
    )
    assert is_safe is True
    assert safety_err is None

    # 5. Provenance and grounding assertions
    assert len(diagnosis.sources) >= 1
    top_source = diagnosis.sources[0]
    assert top_source.document_id == "synthetic-epson-pl2250u"
    assert top_source.page_number == 1
    assert top_source.title == "Epson PowerLite 2250U Synthetic Test Manual"
    assert top_source.chunk_id is not None
    assert top_source.relevance_score is not None

    # 6. Structured result inspection
    assert diagnosis.next_step.action_id == "PROJ_SOURCE_SEARCH"
    assert diagnosis.next_step.safety_level == SafetyLevel.LOW
    assert diagnosis.next_step.requires_confirmation is True
    assert "Source Search" in diagnosis.next_step.instruction
    assert "No Signal" in diagnosis.next_step.reason
