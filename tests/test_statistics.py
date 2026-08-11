import pytest

from ai_nuclear_spectroscopy.models import CascadeCandidate
from ai_nuclear_spectroscopy.statistics import CountObservation, assess_candidate, assess_counts


def test_poisson_background_propagation() -> None:
    result = assess_counts(CountObservation(500.0, 400.0, 100.0, 0.5))
    assert result.net_counts == pytest.approx(350.0)
    assert result.net_uncertainty == pytest.approx((400.0 + 25.0) ** 0.5)
    assert result.status == "HIGH_STATISTICS"


def test_missing_transition_is_kept_as_incomplete_evidence() -> None:
    candidate = CascadeCandidate(
        candidate_id="C1",
        nucleus="999Xx",
        target_level_id="L1",
        target_energy_keV=1000.0,
        target_jpi="2+",
        lifetime_status="unknown",
        feeder_transition_id="F",
        decay_transition_id="D",
        gate_transition_id="G",
        feeder_energy_keV=100.0,
        decay_energy_keV=200.0,
        gate_energy_keV=300.0,
        gate_position="downstream",
        intensity_score=1.0,
        physics_score=50.0,
        source_id="TEST",
    )
    result = assess_candidate(
        candidate,
        [CountObservation(100.0, 500.0, 20.0), CountObservation(200.0, 500.0, 20.0)],
    )
    assert result.status == "INCOMPLETE_EVIDENCE"
    assert result.transition_assessments[-1].status == "NOT_OBSERVED"


def test_negative_counts_are_rejected() -> None:
    with pytest.raises(ValueError):
        assess_counts(CountObservation(500.0, -1.0, 0.0))
