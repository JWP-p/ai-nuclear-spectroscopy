"""Four-region subtraction, signed centroids, and GCD lifetime estimates."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass

from ..models import Centroid, LifetimeEstimate
from .prd import PRDModel, propagate_prd_difference_uncertainty


@dataclass(frozen=True)
class FourRegionSpectrum:
    values: tuple[float, ...]
    variances: tuple[float, ...]
    formula: str


def _as_tuple(values: Iterable[float]) -> tuple[float, ...]:
    return tuple(float(value) for value in values)


def four_region_subtract(
    peak: Iterable[float],
    background_x: Iterable[float],
    background_y: Iterable[float],
    background_xy: Iterable[float],
    *,
    scale_x: float,
    scale_y: float,
    scale_xy: float,
) -> FourRegionSpectrum:
    """Compute P-P - sx(B-P) - sy(P-B) + sxy(B-B)."""
    arrays = tuple(map(_as_tuple, (peak, background_x, background_y, background_xy)))
    lengths = {len(array) for array in arrays}
    if len(lengths) != 1 or not lengths or next(iter(lengths)) == 0:
        raise ValueError("All four spectra must have the same non-zero length")
    if min(scale_x, scale_y, scale_xy) < 0:
        raise ValueError("Region scale factors must be non-negative")
    peak_values, bg_x_values, bg_y_values, bg_xy_values = arrays
    values = tuple(
        p - scale_x * x - scale_y * y + scale_xy * xy
        for p, x, y, xy in zip(
            peak_values,
            bg_x_values,
            bg_y_values,
            bg_xy_values,
            strict=True,
        )
    )
    variances = tuple(
        max(p, 0.0)
        + scale_x**2 * max(x, 0.0)
        + scale_y**2 * max(y, 0.0)
        + scale_xy**2 * max(xy, 0.0)
        for p, x, y, xy in zip(
            peak_values,
            bg_x_values,
            bg_y_values,
            bg_xy_values,
            strict=True,
        )
    )
    return FourRegionSpectrum(
        values=values,
        variances=variances,
        formula="peak - scale_x*background_x - scale_y*background_y + scale_xy*background_xy",
    )


def _centroid_in_window(
    times_ps: tuple[float, ...],
    weights: tuple[float, ...],
    variances: tuple[float, ...],
    low_ps: float,
    high_ps: float,
    *,
    iterations: int,
) -> Centroid:
    selected = [
        (time, weight, variance)
        for time, weight, variance in zip(times_ps, weights, variances, strict=True)
        if low_ps <= time <= high_ps
    ]
    sum_weights = sum(weight for _, weight, _ in selected)
    if abs(sum_weights) < 1e-12:
        raise ValueError("Signed spectrum has zero net weight in the centroid window")
    mean = sum(time * weight for time, weight, _ in selected) / sum_weights
    variance_mean = sum(
        variance * (time - mean) ** 2 for time, _, variance in selected
    ) / abs(sum_weights) ** 2
    return Centroid(
        mean_ps=mean,
        uncertainty_ps=math.sqrt(max(variance_mean, 0.0)),
        sum_weights=sum_weights,
        absolute_sum_weights=sum(abs(weight) for _, weight, _ in selected),
        iterations=iterations,
        converged=False,
        two_cycle_resolved=False,
        window_low_ps=low_ps,
        window_high_ps=high_ps,
    )


def iterative_centroid(
    times_ps: Iterable[float],
    weights: Iterable[float],
    variances: Iterable[float],
    *,
    half_width_ps: float = 1200.0,
    max_iterations: int = 20,
    tolerance_ps: float = 0.01,
) -> Centroid:
    """Compute an iterative signed centroid with explicit two-cycle handling."""
    times = _as_tuple(times_ps)
    values = _as_tuple(weights)
    errors = _as_tuple(variances)
    if not times or len({len(times), len(values), len(errors)}) != 1:
        raise ValueError("times, weights, and variances must have the same non-zero length")
    if any(variance < 0 for variance in errors):
        raise ValueError("variances must be non-negative")
    if half_width_ps <= 0 or max_iterations <= 0 or tolerance_ps < 0:
        raise ValueError("Invalid centroid iteration settings")
    order = sorted(range(len(times)), key=times.__getitem__)
    times = tuple(times[index] for index in order)
    values = tuple(values[index] for index in order)
    errors = tuple(errors[index] for index in order)
    bin_width = min(
        (right - left for left, right in zip(times, times[1:], strict=False) if right > left),
        default=0.0,
    )
    effective_tolerance = max(tolerance_ps, bin_width)
    current = _centroid_in_window(
        times,
        values,
        errors,
        times[0],
        times[-1],
        iterations=0,
    )
    two_back: Centroid | None = None
    for iteration in range(1, max_iterations + 1):
        low = current.mean_ps - half_width_ps
        high = current.mean_ps + half_width_ps
        next_value = _centroid_in_window(
            times,
            values,
            errors,
            low,
            high,
            iterations=iteration,
        )
        if abs(next_value.mean_ps - current.mean_ps) <= effective_tolerance:
            return Centroid(**{**next_value.__dict__, "converged": True})
        if (
            two_back is not None
            and abs(next_value.mean_ps - two_back.mean_ps) <= effective_tolerance
        ):
            mean = 0.5 * (next_value.mean_ps + current.mean_ps)
            half_cycle = 0.5 * abs(next_value.mean_ps - current.mean_ps)
            return Centroid(
                mean_ps=mean,
                uncertainty_ps=math.hypot(
                    max(next_value.uncertainty_ps, current.uncertainty_ps),
                    half_cycle,
                ),
                sum_weights=0.5 * (next_value.sum_weights + current.sum_weights),
                absolute_sum_weights=0.5
                * (next_value.absolute_sum_weights + current.absolute_sum_weights),
                iterations=iteration,
                converged=True,
                two_cycle_resolved=True,
                window_low_ps=mean - half_width_ps,
                window_high_ps=mean + half_width_ps,
            )
        two_back = current
        current = next_value
    return current


def estimate_lifetime(
    *,
    delay: Centroid,
    anti: Centroid,
    decay_energy_keV: float,
    feeder_energy_keV: float,
    prd_model: PRDModel,
    prd_covariance: tuple[tuple[float, float, float], ...],
) -> LifetimeEstimate:
    delta_c = delay.mean_ps - anti.mean_ps
    delta_c_uncertainty = math.hypot(delay.uncertainty_ps, anti.uncertainty_ps)
    delta_r = prd_model.difference_ps(decay_energy_keV, feeder_energy_keV)
    delta_r_uncertainty = propagate_prd_difference_uncertainty(
        prd_model,
        prd_covariance,
        decay_energy_keV=decay_energy_keV,
        feeder_energy_keV=feeder_energy_keV,
    )
    mean_life = 0.5 * (delta_c - delta_r)
    mean_life_uncertainty = 0.5 * math.hypot(delta_c_uncertainty, delta_r_uncertainty)
    half_life = math.log(2.0) * mean_life
    half_life_uncertainty = math.log(2.0) * mean_life_uncertainty
    in_range = prd_model.in_calibration_range(decay_energy_keV, feeder_energy_keV)
    prd_status = "IN_RANGE" if in_range else "EXTRAPOLATED_HOLD"
    if mean_life <= 0:
        scientific_status = "NON_POSITIVE_ESTIMATE_HOLD"
    elif not in_range:
        scientific_status = "SYNTHETIC_ESTIMATE_EXTRAPOLATED_HOLD"
    else:
        scientific_status = "SYNTHETIC_ESTIMATE_NOT_FORMAL_RELEASE"
    uncertainty_scope = [
        "centroid_counting_statistics",
        "prd_parameter_covariance",
        "gate_window_systematics_not_included",
        "detector_response_model_systematics_not_included",
    ]
    if not in_range:
        uncertainty_scope.append("prd_extrapolation_model_uncertainty_not_quantified")
    return LifetimeEstimate(
        delay_centroid_ps=delay.mean_ps,
        anti_centroid_ps=anti.mean_ps,
        delta_c_ps=delta_c,
        delta_c_uncertainty_ps=delta_c_uncertainty,
        delta_r_ps=delta_r,
        delta_r_uncertainty_ps=delta_r_uncertainty,
        mean_life_ps=mean_life,
        mean_life_uncertainty_ps=mean_life_uncertainty,
        half_life_ps=half_life,
        half_life_uncertainty_ps=half_life_uncertainty,
        prd_status=prd_status,
        scientific_status=scientific_status,
        uncertainty_scope=tuple(uncertainty_scope),
    )
