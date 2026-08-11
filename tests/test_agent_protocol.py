from dataclasses import replace
from pathlib import Path

import pytest

from ai_nuclear_spectroscopy.agents import (
    build_agent_iteration_trace,
    build_agent_reviews,
    require_human_approval,
    select_review_candidate,
)
from ai_nuclear_spectroscopy.ensdf import parse_ensdf
from ai_nuclear_spectroscopy.screening import enumerate_cascades
from ai_nuclear_spectroscopy.statistics import CountObservation, assess_candidate


def _evidence():
    dataset = parse_ensdf(
        Path("examples/synthetic_ensdf/fictional_999xx.ens").read_text(encoding="latin-1"),
        source_id="TEST",
    )[0]
    candidates = enumerate_cascades(dataset)
    observations = [
        CountObservation(energy, 1000.0, 100.0)
        for energy in (1000.0, 800.0, 700.0, 500.0)
    ]
    assessments = [assess_candidate(row, observations) for row in candidates]
    return candidates, assessments


def test_agent_review_is_a_recommendation_not_a_result() -> None:
    candidates, assessments = _evidence()
    reviews = build_agent_reviews(candidates, assessments)
    assert reviews
    assert all("not a lifetime result" in review.claim for review in reviews)
    assert all(review.recommendation in {"REVIEW", "HOLD", "REJECT"} for review in reviews)
    assert all(review.confidence in {"LOW", "MEDIUM", "HIGH"} for review in reviews)
    assert all(review.counterevidence for review in reviews)
    assert select_review_candidate(candidates, assessments) in {
        row.candidate_id for row in candidates
    }


def test_agent_iteration_trace_ends_at_human_decision() -> None:
    candidates, assessments = _evidence()
    reviews = build_agent_reviews(candidates, assessments)
    selected_id = select_review_candidate(candidates, assessments)
    trace = build_agent_iteration_trace(
        candidates,
        assessments,
        reviews,
        selected_candidate_id=selected_id,
    )
    assert [round_.role for round_ in trace] == [
        "candidate_selector",
        "evidence_critic",
        "review_synthesizer",
    ]
    assert trace[-1].verdict == "READY_FOR_HUMAN_DECISION"
    assert "human decision" in trace[-1].required_next_action


def test_agent_iteration_trace_preserves_evidence_hold() -> None:
    candidates, assessments = _evidence()
    selected_id = select_review_candidate(candidates, assessments)
    held_assessments = [
        replace(row, status="INCOMPLETE_EVIDENCE")
        if row.candidate_id == selected_id
        else row
        for row in assessments
    ]
    reviews = build_agent_reviews(candidates, held_assessments)
    trace = build_agent_iteration_trace(
        candidates,
        held_assessments,
        reviews,
        selected_candidate_id=selected_id,
    )
    assert trace[-1].verdict == "HOLD"


def test_human_gate_blocks_unapproved_gcd() -> None:
    with pytest.raises(PermissionError):
        require_human_approval(
            candidate_id="C1",
            approved=False,
            reviewer="Reviewer",
            scope="SYNTHETIC_DEMO_ONLY",
        )


def test_human_gate_rejects_scope_expansion() -> None:
    with pytest.raises(ValueError):
        require_human_approval(
            candidate_id="C1",
            approved=True,
            reviewer="Reviewer",
            scope="REAL_EXPERIMENT",
            approved_utc="2026-08-11T00:00:00Z",
        )


def test_human_gate_records_timestamp() -> None:
    approval = require_human_approval(
        candidate_id="C1",
        approved=True,
        reviewer="Reviewer",
        scope="SYNTHETIC_DEMO_ONLY",
        approved_utc="2026-08-11T00:00:00Z",
    )
    assert approval["approved_utc"] == "2026-08-11T00:00:00Z"


def test_human_gate_rejects_timestamp_without_timezone() -> None:
    with pytest.raises(ValueError):
        require_human_approval(
            candidate_id="C1",
            approved=True,
            reviewer="Reviewer",
            scope="SYNTHETIC_DEMO_ONLY",
            approved_utc="2026-08-11T00:00:00",
        )
