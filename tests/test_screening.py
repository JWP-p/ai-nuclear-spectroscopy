from pathlib import Path

from ai_nuclear_spectroscopy.ensdf import parse_ensdf
from ai_nuclear_spectroscopy.screening import enumerate_cascades


def _candidates():
    path = Path("examples/synthetic_ensdf/fictional_999xx.ens")
    dataset = parse_ensdf(path.read_text(encoding="latin-1"), source_id="TEST")[0]
    return enumerate_cascades(dataset)


def test_source_local_three_transition_cascades_cover_both_gate_orientations() -> None:
    candidates = _candidates()
    assert len(candidates) == 4
    assert {candidate.gate_position for candidate in candidates} == {"upstream", "downstream"}
    assert all(candidate.source_id == "TEST" for candidate in candidates)


def test_candidate_ids_and_order_are_deterministic() -> None:
    first = _candidates()
    second = _candidates()
    assert [row.candidate_id for row in first] == [row.candidate_id for row in second]
    assert first[0].physics_score >= first[-1].physics_score
