"""Transparent Poisson counting checks for candidate prioritisation."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass

from ..models import CandidateAssessment, CascadeCandidate, CountAssessment


@dataclass(frozen=True)
class CountObservation:
    transition_energy_keV: float
    signal_window_counts: float
    background_window_counts: float
    background_scale: float = 1.0


def assess_counts(
    observation: CountObservation,
    *,
    high_significance: float = 8.0,
    usable_significance: float = 4.0,
    minimum_net_counts: float = 30.0,
) -> CountAssessment:
    if observation.signal_window_counts < 0 or observation.background_window_counts < 0:
        raise ValueError("Counts must be non-negative")
    if observation.background_scale < 0:
        raise ValueError("background_scale must be non-negative")
    net = (
        observation.signal_window_counts
        - observation.background_scale * observation.background_window_counts
    )
    variance = (
        observation.signal_window_counts
        + observation.background_scale**2 * observation.background_window_counts
    )
    uncertainty = math.sqrt(variance)
    significance = net / uncertainty if uncertainty else 0.0
    if net < minimum_net_counts or significance < usable_significance:
        status = "LOW_OR_INCONCLUSIVE"
    elif significance >= high_significance:
        status = "HIGH_STATISTICS"
    else:
        status = "USABLE_STATISTICS"
    return CountAssessment(
        transition_energy_keV=observation.transition_energy_keV,
        signal_counts=observation.signal_window_counts,
        background_counts=observation.background_window_counts,
        background_scale=observation.background_scale,
        net_counts=net,
        net_uncertainty=uncertainty,
        significance=significance,
        status=status,
    )


def _find_observation(
    observations: Iterable[CountObservation],
    energy_keV: float,
    tolerance_keV: float,
) -> CountObservation | None:
    matches = [
        row
        for row in observations
        if abs(row.transition_energy_keV - energy_keV) <= tolerance_keV
    ]
    if not matches:
        return None
    return min(matches, key=lambda row: abs(row.transition_energy_keV - energy_keV))


def assess_candidate(
    candidate: CascadeCandidate,
    observations: Iterable[CountObservation],
    *,
    tolerance_keV: float = 1.0,
) -> CandidateAssessment:
    observations = tuple(observations)
    assessments: list[CountAssessment] = []
    for energy in (
        candidate.feeder_energy_keV,
        candidate.decay_energy_keV,
        candidate.gate_energy_keV,
    ):
        observation = _find_observation(observations, energy, tolerance_keV)
        if observation is None:
            assessments.append(
                CountAssessment(
                    transition_energy_keV=energy,
                    signal_counts=0.0,
                    background_counts=0.0,
                    background_scale=1.0,
                    net_counts=0.0,
                    net_uncertainty=0.0,
                    significance=0.0,
                    status="NOT_OBSERVED",
                )
            )
        else:
            assessments.append(assess_counts(observation))
    statuses = {assessment.status for assessment in assessments}
    bottleneck = min(assessment.significance for assessment in assessments)
    total_net = sum(assessment.net_counts for assessment in assessments)
    if statuses == {"HIGH_STATISTICS"}:
        status = "HIGH_PRIORITY"
    elif "NOT_OBSERVED" in statuses:
        status = "INCOMPLETE_EVIDENCE"
    elif "LOW_OR_INCONCLUSIVE" in statuses:
        status = "LOW_PRIORITY_OR_HOLD"
    else:
        status = "REVIEWABLE"
    return CandidateAssessment(
        candidate_id=candidate.candidate_id,
        transition_assessments=tuple(assessments),
        bottleneck_significance=bottleneck,
        total_net_counts=total_net,
        status=status,
    )
