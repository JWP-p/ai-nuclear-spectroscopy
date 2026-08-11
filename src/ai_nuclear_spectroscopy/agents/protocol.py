"""Evidence-first protocol for AI participation in a scientific workflow.

This module does not call a model. It defines the structured contract that any
model adapter must satisfy, and it keeps model recommendations separate from
human approval and formal scientific release.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum

from ..models import AgentReview, AgentRound, CandidateAssessment, CascadeCandidate


class ScientificStage(StrEnum):
    SOURCE_PARSED = "SOURCE_PARSED"
    CANDIDATES_SCREENED = "CANDIDATES_SCREENED"
    STATISTICS_ASSESSED = "STATISTICS_ASSESSED"
    AGENT_REVIEWED = "AGENT_REVIEWED"
    HUMAN_APPROVED = "HUMAN_APPROVED"
    GCD_ESTIMATED = "GCD_ESTIMATED"
    FORMAL_RELEASE = "FORMAL_RELEASE"


def build_agent_reviews(
    candidates: Iterable[CascadeCandidate],
    assessments: Iterable[CandidateAssessment],
) -> list[AgentReview]:
    """Create auditable recommendations from explicit physics and count evidence."""
    assessment_by_id = {row.candidate_id: row for row in assessments}
    reviews: list[AgentReview] = []
    for candidate in candidates:
        assessment = assessment_by_id.get(candidate.candidate_id)
        if assessment is None:
            continue
        evidence = (
            f"physics_score={candidate.physics_score:.3f}",
            f"intensity_score={candidate.intensity_score:.3f}",
            f"statistics_status={assessment.status}",
            f"bottleneck_significance={assessment.bottleneck_significance:.3f}",
            f"total_net_counts={assessment.total_net_counts:.1f}",
        )
        counterevidence: list[str] = [
            "detector_specific_contamination_and_response_not_validated"
        ]
        if candidate.lifetime_status != "unknown":
            counterevidence.append(f"target_lifetime_status={candidate.lifetime_status}")
        if assessment.status != "HIGH_PRIORITY":
            counterevidence.append("not_all_three_transitions_have_high_statistics")
        if candidate.gate_position == "upstream":
            counterevidence.append("upstream_gate_requires_direction-specific_validation")
        if assessment.status in {"HIGH_PRIORITY", "REVIEWABLE"}:
            recommendation = "REVIEW"
            confidence = "MEDIUM"
        else:
            recommendation = "HOLD"
            confidence = "LOW"
        reviews.append(
            AgentReview(
                candidate_id=candidate.candidate_id,
                claim=(
                    "This source-local F-D-G path is a candidate for the next review stage, "
                    "not a lifetime result."
                ),
                supporting_evidence=evidence,
                counterevidence=tuple(counterevidence),
                recommendation=recommendation,
                confidence=confidence,
                required_next_action=(
                    "A human reviewer must verify source identity, peak completeness, "
                    "gate direction, contamination, and detector-response range."
                ),
            )
        )
    return reviews


def select_review_candidate(
    candidates: Iterable[CascadeCandidate],
    assessments: Iterable[CandidateAssessment],
) -> str:
    """Choose a review target; this is not an automatic scientific approval."""
    assessment_by_id = {row.candidate_id: row for row in assessments}
    eligible = [
        candidate
        for candidate in candidates
        if candidate.candidate_id in assessment_by_id
    ]
    if not eligible:
        raise ValueError("No candidates have statistics assessments")
    selected = max(
        eligible,
        key=lambda candidate: (
            assessment_by_id[candidate.candidate_id].status == "HIGH_PRIORITY",
            assessment_by_id[candidate.candidate_id].bottleneck_significance,
            candidate.physics_score,
        ),
    )
    return selected.candidate_id


def build_agent_iteration_trace(
    candidates: Iterable[CascadeCandidate],
    assessments: Iterable[CandidateAssessment],
    reviews: Iterable[AgentReview],
    *,
    selected_candidate_id: str,
) -> tuple[AgentRound, ...]:
    """Build an inspectable selector-critic-synthesis trace.

    This deterministic offline trace demonstrates the contract used by the
    prompt templates. It is not presented as an actual model interaction.
    """
    candidate_by_id = {row.candidate_id: row for row in candidates}
    assessment_by_id = {row.candidate_id: row for row in assessments}
    review_by_id = {row.candidate_id: row for row in reviews}
    try:
        candidate = candidate_by_id[selected_candidate_id]
        assessment = assessment_by_id[selected_candidate_id]
        review = review_by_id[selected_candidate_id]
    except KeyError as error:
        raise ValueError("Selected candidate lacks a complete agent-review record") from error

    selector = AgentRound(
        round_index=1,
        role="candidate_selector",
        candidate_id=selected_candidate_id,
        verdict=review.recommendation,
        evidence=review.supporting_evidence,
        unresolved=review.counterevidence,
        required_next_action="Send the leading candidate to an independent evidence critic.",
    )

    critic_failures: list[str] = []
    if len(assessment.transition_assessments) != 3:
        critic_failures.append("candidate_does_not_have_exactly_three_transition_assessments")
    if assessment.status in {"INCOMPLETE_EVIDENCE", "LOW_PRIORITY_OR_HOLD"}:
        critic_failures.append(f"statistics_status={assessment.status}")
    if not candidate.source_id:
        critic_failures.append("source_identity_missing")
    critic_verdict = (
        "SUPPORTED_FOR_HUMAN_REVIEW"
        if review.recommendation == "REVIEW" and not critic_failures
        else "HOLD"
    )
    critic = AgentRound(
        round_index=2,
        role="evidence_critic",
        candidate_id=selected_candidate_id,
        verdict=critic_verdict,
        evidence=(
            f"source_id={candidate.source_id}",
            f"transition_assessment_count={len(assessment.transition_assessments)}",
            f"statistics_status={assessment.status}",
            "counterevidence_was_preserved_from_selector",
        ),
        unresolved=tuple(critic_failures) + review.counterevidence,
        required_next_action=(
            "A human must verify source identity, F-D-G direction, peak completeness, "
            "contamination, and detector applicability."
        ),
    )

    synthesis_verdict = (
        "READY_FOR_HUMAN_DECISION"
        if critic.verdict == "SUPPORTED_FOR_HUMAN_REVIEW"
        else "HOLD"
    )
    synthesis = AgentRound(
        round_index=3,
        role="review_synthesizer",
        candidate_id=selected_candidate_id,
        verdict=synthesis_verdict,
        evidence=(
            f"selector_verdict={selector.verdict}",
            f"critic_verdict={critic.verdict}",
            f"candidate_id={selected_candidate_id}",
        ),
        unresolved=critic.unresolved,
        required_next_action=(
            "Record an explicit, scoped human decision; do not infer approval from this trace."
        ),
    )
    return (selector, critic, synthesis)


def require_human_approval(
    *,
    candidate_id: str,
    approved: bool,
    reviewer: str,
    scope: str,
    approved_utc: str = "",
) -> dict[str, str | bool]:
    """Return an explicit gate record or stop before GCD estimation."""
    if not approved:
        raise PermissionError("GCD estimation is blocked until a human reviewer approves the path")
    if not reviewer.strip():
        raise ValueError("reviewer is required for an approval record")
    try:
        parsed_time = datetime.fromisoformat(approved_utc.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("approved_utc must be a valid ISO 8601 timestamp") from error
    if parsed_time.tzinfo is None:
        raise ValueError("approved_utc must include a timezone")
    if scope != "SYNTHETIC_DEMO_ONLY":
        raise ValueError(
            "This public reference implementation accepts approval only for the synthetic demo"
        )
    return {
        "candidate_id": candidate_id,
        "approved": True,
        "reviewer": reviewer,
        "scope": scope,
        "approved_utc": approved_utc,
        "statement": (
            "Approval authorizes the synthetic demonstration only and is not a formal "
            "experimental lifetime release."
        ),
    }
