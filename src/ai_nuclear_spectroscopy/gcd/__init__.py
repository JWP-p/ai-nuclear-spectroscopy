"""Generalized centroid-difference reference implementation."""

from .analysis import (
    FourRegionSpectrum,
    estimate_lifetime,
    four_region_subtract,
    iterative_centroid,
)
from .prd import PRDModel, build_prd_covariance, propagate_prd_difference_uncertainty

__all__ = [
    "FourRegionSpectrum",
    "PRDModel",
    "build_prd_covariance",
    "estimate_lifetime",
    "four_region_subtract",
    "iterative_centroid",
    "propagate_prd_difference_uncertainty",
]
