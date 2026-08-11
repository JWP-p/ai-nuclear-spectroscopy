from pathlib import Path

import pytest

from ai_nuclear_spectroscopy.ensdf import EnsdfParseError, parse_ensdf, parse_half_life

FIXTURE = Path("examples/synthetic_ensdf/fictional_999xx.ens")


def test_synthetic_ensdf_is_parsed_and_placed() -> None:
    datasets = parse_ensdf(FIXTURE.read_text(encoding="latin-1"), source_id="TEST")
    assert len(datasets) == 1
    dataset = datasets[0]
    assert dataset.nucleus == "999Xx"
    assert len(dataset.levels) == 5
    assert len(dataset.transitions) == 4
    assert all(row.placement_status == "placed_energy_closure" for row in dataset.transitions)
    assert [row.energy_keV for row in dataset.transitions] == [1000.0, 800.0, 700.0, 500.0]


def test_half_life_units_and_relations() -> None:
    assert parse_half_life("0.20 NS", "2").value_ps == pytest.approx(200.0)
    assert parse_half_life("> 4 NS").relation == "lower_limit"
    assert parse_half_life("STABLE").relation == "stable"
    assert parse_half_life("").relation == "unknown"


def test_empty_ensdf_fails_closed() -> None:
    with pytest.raises(EnsdfParseError):
        parse_ensdf("\n", source_id="TEST")
