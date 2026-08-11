import math

import pytest

from ai_nuclear_spectroscopy.gcd import (
    PRDModel,
    build_prd_covariance,
    estimate_lifetime,
    four_region_subtract,
    iterative_centroid,
    propagate_prd_difference_uncertainty,
)


def test_four_region_inclusion_exclusion_and_variance() -> None:
    result = four_region_subtract(
        [100.0, 120.0],
        [20.0, 20.0],
        [10.0, 10.0],
        [5.0, 5.0],
        scale_x=0.5,
        scale_y=1.0,
        scale_xy=0.5,
    )
    assert result.values == pytest.approx((82.5, 102.5))
    assert all(value > 0 for value in result.variances)


def test_signed_iterative_centroid_recovers_peak() -> None:
    times = [float(value) for value in range(-1000, 1001, 20)]
    weights = [1000.0 * math.exp(-0.5 * ((time - 140.0) / 120.0) ** 2) for time in times]
    centroid = iterative_centroid(times, weights, weights, half_width_ps=500.0)
    assert centroid.converged
    assert centroid.mean_ps == pytest.approx(140.0, abs=0.1)


def test_prd_covariance_and_lifetime_uncertainty() -> None:
    model = PRDModel(5000.0, 100.0, 0.02, 0.0, 100.0, 1500.0)
    covariance = build_prd_covariance(
        model,
        [
            (300.0, 600.0, 5.0),
            (500.0, 900.0, 5.0),
            (700.0, 1000.0, 5.0),
            (1100.0, 400.0, 5.0),
            (1300.0, 800.0, 5.0),
        ],
    )
    sigma = propagate_prd_difference_uncertainty(
        model,
        covariance,
        decay_energy_keV=700.0,
        feeder_energy_keV=800.0,
    )
    assert sigma > 0.0
    delay = iterative_centroid([0.0, 100.0, 200.0], [0.0, 1.0, 0.0], [1.0, 1.0, 1.0])
    anti = iterative_centroid([-200.0, -100.0, 0.0], [0.0, 1.0, 0.0], [1.0, 1.0, 1.0])
    estimate = estimate_lifetime(
        delay=delay,
        anti=anti,
        decay_energy_keV=700.0,
        feeder_energy_keV=800.0,
        prd_model=model,
        prd_covariance=covariance,
    )
    assert estimate.mean_life_ps > 0
    assert estimate.prd_status == "IN_RANGE"
    assert estimate.scientific_status == "SYNTHETIC_ESTIMATE_NOT_FORMAL_RELEASE"


def test_prd_extrapolation_is_a_hold() -> None:
    model = PRDModel(5000.0, 100.0, 0.02, 0.0, 100.0, 900.0)
    covariance = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1e-8))
    delay = iterative_centroid([0.0, 100.0, 200.0], [0.0, 1.0, 0.0], [1.0, 1.0, 1.0])
    anti = iterative_centroid([-200.0, -100.0, 0.0], [0.0, 1.0, 0.0], [1.0, 1.0, 1.0])
    estimate = estimate_lifetime(
        delay=delay,
        anti=anti,
        decay_energy_keV=1000.0,
        feeder_energy_keV=800.0,
        prd_model=model,
        prd_covariance=covariance,
    )
    assert estimate.prd_status == "EXTRAPOLATED_HOLD"
