"""Action Selector for CleanFix AI.

Selects approved, safe diagnostic actions from the registry based on session history,
previous step outcomes, evidence grounding, and device constraints.
"""


from server.ai.diagnosis.models import (
    NextStep,
    RetrievalResult,
    RetrievalStatus,
    SessionContext,
    SourceReference,
    StepResultStatus,
)
from server.ai.safety.action_registry import (
    ACTION_REGISTRY,
    ApprovedAction,
    get_approved_actions_for_device,
)


class ActionSelector:
    """Selects the next approved low-risk diagnostic action."""

    @classmethod
    def select_action(
        cls,
        session_context: SessionContext,
        evidence: RetrievalResult | None = None,
    ) -> tuple[NextStep | None, list[SourceReference], str | None]:
        """
        Determines the next appropriate diagnostic step.
        Returns (NextStep, sources_list, reasoning_summary).
        If no viable safe action remains, returns (None, [], reason_for_escalation).
        """
        device_type = session_context.device_type
        candidate_actions = get_approved_actions_for_device(device_type)

        if not candidate_actions:
            return None, [], f"No approved diagnostic actions exist for device category '{device_type}'"

        # Determine actions already attempted and their outcomes
        attempted_action_ids: set[str] = set()
        unable_action_categories: set[str] = set()

        for step in session_context.previous_steps:
            if step.action_id:
                attempted_action_ids.add(step.action_id)
                if step.result_status == StepResultStatus.UNABLE_TO_PERFORM:
                    # User cannot access this type of equipment (e.g. high ceiling cable)
                    action_def = ACTION_REGISTRY.get(step.action_id)
                    if action_def:
                        unable_action_categories.add(action_def.category)

        # Filter out already attempted actions and categories user is unable to perform
        viable_actions: list[ApprovedAction] = []
        for action in candidate_actions:
            if action.action_id in attempted_action_ids:
                continue
            if action.category in unable_action_categories:
                # Avoid requiring actions in categories user cannot reach/perform
                continue
            viable_actions.append(action)

        if not viable_actions:
            return (
                None,
                [],
                "All standard low-risk troubleshooting actions for this device have been attempted without success.",
            )

        # Match evidence to boost priority and cite valid manual pages
        best_action, matched_sources, grounding_note = cls._match_action_with_evidence(
            viable_actions, evidence
        )

        next_step = NextStep(
            action_id=best_action.action_id,
            instruction=best_action.instruction,
            reason=best_action.reason,
            expected_observation=best_action.expected_observation,
            safety_level=best_action.safety_level,
            requires_confirmation=best_action.requires_confirmation,
        )

        return next_step, matched_sources, grounding_note

    @classmethod
    def _match_action_with_evidence(
        cls,
        viable_actions: list[ApprovedAction],
        evidence: RetrievalResult | None,
    ) -> tuple[ApprovedAction, list[SourceReference], str]:
        """
        Ranks viable actions by checking relevance to retrieved documentation.
        Returns (best_action, sources_list, reasoning).
        """
        sources: list[SourceReference] = []

        # If evidence was found, check if any chunks reference an action
        if evidence and evidence.retrieval_status == RetrievalStatus.FOUND and evidence.evidence:
            for item in evidence.evidence:
                chunk_lower = item.text.lower()
                for action in viable_actions:
                    # Check keywords
                    action_keywords = action.title.lower().split() + action.instruction.lower().split()
                    matches = sum(1 for kw in action_keywords if len(kw) > 3 and kw in chunk_lower)
                    if matches >= 2:
                        # Found a grounded match in verified documentation!
                        sources.append(
                            SourceReference(
                                document_id=item.document_id,
                                page_number=item.page_number,
                                title=item.title,
                                chunk_id=item.chunk_id,
                                relevance_score=item.relevance_score,
                            )
                        )
                        reasoning = (
                            f"Action '{action.title}' is grounded in manufacturer documentation "
                            f"({item.title}, pg {item.page_number or 'N/A'})."
                        )
                        return action, sources, reasoning

            # Evidence was found but didn't specifically highlight one action over another
            # Still attach relevant general manual evidence if applicable
            top_evidence = evidence.evidence[0]
            sources.append(
                SourceReference(
                    document_id=top_evidence.document_id,
                    page_number=top_evidence.page_number,
                    title=top_evidence.title,
                    chunk_id=top_evidence.chunk_id,
                    relevance_score=top_evidence.relevance_score,
                )
            )
            top_action = viable_actions[0]
            reasoning = (
                f"Selected '{top_action.title}' based on verified device manual documentation "
                f"({top_evidence.title})."
            )
            return top_action, sources, reasoning

        # Case: retrieval_status == "no_match" or "failed" or None
        # Strict rule: DO NOT cite any sources when retrieval_status != found!
        top_action = viable_actions[0]
        if evidence and evidence.retrieval_status == RetrievalStatus.NO_MATCH:
            reasoning = (
                f"No specific manual chunk found in documentation. Proceeding with approved safe "
                f"standard check: '{top_action.title}'."
            )
        elif evidence and evidence.retrieval_status == RetrievalStatus.FAILED:
            reasoning = (
                f"Retrieval subsystem encountered a temporary fault. Proceeding with approved safe "
                f"fallback check: '{top_action.title}'."
            )
        else:
            reasoning = f"Proceeding with standard approved diagnostic procedure: '{top_action.title}'."

        return top_action, [], reasoning

