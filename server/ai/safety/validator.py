"""Safety validator ensuring diagnostic steps, citations, and symptom inputs comply with strict safety rules."""

import re

from server.ai.diagnosis.models import (
    EvidenceItem,
    NextStep,
    SafetyLevel,
    SourceReference,
)
from server.ai.safety.action_registry import (
    get_approved_action,
)
from server.ai.safety.constraints import (
    check_prohibited_actions,
    is_safety_hazard,
)


class SafetyValidator:
    """Validates diagnostic proposals against safety rules, approved registries, and grounding."""

    @staticmethod
    def validate_symptom_safety(symptom_text: str) -> tuple[str, str] | None:
        """
        Scans symptom descriptions for critical safety hazards.
        Returns (hazard_type, message) if a hazard is detected, else None.
        """
        return is_safety_hazard(symptom_text)

    @staticmethod
    def validate_proposed_step(
        step: NextStep,
        device_type: str,
        permitted_categories: list[str] | None = None,
    ) -> tuple[bool, str | None]:
        """
        Verifies that a proposed diagnostic step is safe, registered, and appropriate.
        Returns (is_valid, rejection_reason).
        """
        if not step:
            return False, "Step is empty or null"

        # 1. Prohibit high-risk steps
        if step.safety_level == SafetyLevel.HIGH:
            return False, "Safety rejection: High-risk physical actions cannot be recommended to users"

        # 2. Check for prohibited action keywords in instructions
        prohibited_err = check_prohibited_actions(step.instruction)
        if prohibited_err:
            return False, f"Safety rejection: {prohibited_err}"

        reason_err = check_prohibited_actions(step.reason)
        if reason_err:
            return False, f"Safety rejection: {reason_err}"

        # 3. Verify action registry grounding
        if not step.action_id:
            return False, "Action rejection: Step must be associated with an approved action_id"

        approved = get_approved_action(step.action_id)
        if not approved:
            return False, f"Action rejection: action_id '{step.action_id}' is not in the approved Action Registry"

        # 4. Verify device type alignment
        if approved.device_type != device_type:
            return False, (
                f"Action rejection: action '{step.action_id}' is approved for '{approved.device_type}', "
                f"not '{device_type}'"
            )

        # 5. Verify permitted action categories if specified
        if permitted_categories and approved.category not in permitted_categories:
            return False, (
                f"Action rejection: action category '{approved.category}' is not in permitted categories: "
                f"{permitted_categories}"
            )

        return True, None

    @staticmethod
    def validate_source_grounding(
        sources: list[SourceReference],
        evidence: list[EvidenceItem],
    ) -> tuple[bool, str | None]:
        """
        Ensures that all cited sources exist in the provided retrieved evidence.
        Prevents hallucinated manual IDs and false citations.
        Returns (is_valid, violation_reason).
        """
        if not sources:
            return True, None

        if not evidence:
            return False, "Grounding rejection: Sources cited but no evidence was provided (no_match/failed)"

        valid_doc_ids = {item.document_id for item in evidence}

        for source in sources:
            if source.document_id not in valid_doc_ids:
                return False, (
                    f"Grounding rejection: Cited document_id '{source.document_id}' was not found in "
                    f"retrieved evidence {list(valid_doc_ids)}"
                )

        return True, None

    @staticmethod
    def sanitize_untrusted_input(text: str) -> str:
        """
        Neutralizes prompt injection patterns and delimiters in untrusted text.
        Preserves natural symptom description.
        """
        if not text:
            return ""

        # Remove common prompt injection attack vectors
        sanitized = text
        injection_patterns = [
            r"ignore\s+(all\s+)?(previous|above)\s+instructions?",
            r"system\s+(prompt\s+)?override",
            r"you\s+are\s+now\s+in\s+developer\s+mode",
            r"disregard\s+safety\s+rules?",
            r"bypass\s+all\s+constraints?",
            r"admin\s+mode\s+enabled",
        ]

        for pat in injection_patterns:
            sanitized = re.sub(pat, "[BLOCKED_OVERRIDE_ATTEMPT]", sanitized, flags=re.IGNORECASE)

        # Strip XML/Markdown system prompt delimiter mimics
        sanitized = sanitized.replace("<system>", "").replace("</system>", "")
        sanitized = sanitized.replace("```system", "```")

        return sanitized.strip()

