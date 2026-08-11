"""Prompt-response-difference model and covariance propagation."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class PRDModel:
    """R(E) = a / sqrt(b + E) + c E + d."""

    a: float
    b: float
    c: float
    d: float
    energy_min_keV: float
    energy_max_keV: float

    def response_ps(self, energy_keV: float) -> float:
        if self.b + energy_keV <= 0:
            raise ValueError("PRD square-root domain error")
        return self.a / math.sqrt(self.b + energy_keV) + self.c * energy_keV + self.d

    def difference_ps(self, decay_energy_keV: float, feeder_energy_keV: float) -> float:
        return self.response_ps(decay_energy_keV) - self.response_ps(feeder_energy_keV)

    def in_calibration_range(self, *energies_keV: float) -> bool:
        return all(self.energy_min_keV <= energy <= self.energy_max_keV for energy in energies_keV)


def prd_difference_jacobian(
    model: PRDModel,
    decay_energy_keV: float,
    feeder_energy_keV: float,
) -> tuple[float, float, float]:
    """Jacobian of R(E_decay)-R(E_feeder) with respect to (a, b, c)."""
    if model.b + decay_energy_keV <= 0 or model.b + feeder_energy_keV <= 0:
        raise ValueError("PRD square-root domain error")
    inv_decay = 1.0 / math.sqrt(model.b + decay_energy_keV)
    inv_feeder = 1.0 / math.sqrt(model.b + feeder_energy_keV)
    return (
        inv_decay - inv_feeder,
        0.5
        * model.a
        * (
            (model.b + feeder_energy_keV) ** -1.5
            - (model.b + decay_energy_keV) ** -1.5
        ),
        decay_energy_keV - feeder_energy_keV,
    )


def _invert(matrix: list[list[float]]) -> list[list[float]]:
    size = len(matrix)
    if size == 0 or any(len(row) != size for row in matrix):
        raise ValueError("matrix must be non-empty and square")
    augmented = [
        list(row) + [1.0 if left == right else 0.0 for right in range(size)]
        for left, row in enumerate(matrix)
    ]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-18:
            raise ValueError("singular PRD normal matrix")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        scale = augmented[column][column]
        augmented[column] = [value / scale for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(augmented[row], augmented[column], strict=True)
            ]
    return [row[size:] for row in augmented]


def build_prd_covariance(
    model: PRDModel,
    fit_points: Iterable[tuple[float, float, float]],
) -> tuple[tuple[float, float, float], ...]:
    """Rebuild covariance from weighted PRD-difference equations.

    Each fit point is ``(decay_energy_keV, feeder_energy_keV, sigma_ps)``.
    The absolute offset ``d`` cancels in a response difference.
    """
    normal = [[0.0 for _ in range(3)] for _ in range(3)]
    count = 0
    for decay, feeder, sigma in fit_points:
        if sigma <= 0:
            raise ValueError("PRD fit uncertainty must be positive")
        jacobian = prd_difference_jacobian(model, decay, feeder)
        weight = 1.0 / sigma**2
        for left in range(3):
            for right in range(3):
                normal[left][right] += weight * jacobian[left] * jacobian[right]
        count += 1
    if count < 3:
        raise ValueError("At least three independent PRD fit equations are required")
    covariance = _invert(normal)
    return tuple(tuple(value for value in row) for row in covariance)


def propagate_prd_difference_uncertainty(
    model: PRDModel,
    covariance: tuple[tuple[float, float, float], ...],
    *,
    decay_energy_keV: float,
    feeder_energy_keV: float,
) -> float:
    if len(covariance) != 3 or any(len(row) != 3 for row in covariance):
        raise ValueError("PRD covariance must be 3 by 3 for parameters (a, b, c)")
    jacobian = prd_difference_jacobian(model, decay_energy_keV, feeder_energy_keV)
    variance = sum(
        jacobian[left] * covariance[left][right] * jacobian[right]
        for left in range(3)
        for right in range(3)
    )
    if variance < -1e-10:
        raise ValueError(f"PRD propagation produced a negative variance: {variance}")
    return math.sqrt(max(variance, 0.0))
