"""Shared, serializable domain models.

The models deliberately keep source identity separate from canonical display
identity. This makes conflicts and provenance visible instead of silently
collapsing different nuclear-data records into one value.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class HalfLife:
    display: str
    value_ps: float | None
    relation: str


@dataclass(frozen=True)
class Level:
    level_id: str
    nucleus: str
    energy_keV: float
    energy_raw: str
    jpi: str
    half_life: HalfLife
    source_id: str
    source_line: int


@dataclass(frozen=True)
class Transition:
    transition_id: str
    nucleus: str
    initial_level_id: str
    final_level_id: str
    energy_keV: float
    intensity: float | None
    multipolarity: str
    placement_status: str
    source_id: str
    source_line: int


@dataclass(frozen=True)
class Dataset:
    dataset_id: str
    nucleus: str
    title: str
    levels: tuple[Level, ...]
    transitions: tuple[Transition, ...]


@dataclass(frozen=True)
class CascadeCandidate:
    candidate_id: str
    nucleus: str
    target_level_id: str
    target_energy_keV: float
    target_jpi: str
    lifetime_status: str
    feeder_transition_id: str
    decay_transition_id: str
    gate_transition_id: str
    feeder_energy_keV: float
    decay_energy_keV: float
    gate_energy_keV: float
    gate_position: str
    intensity_score: float
    physics_score: float
    source_id: str


@dataclass(frozen=True)
class CountAssessment:
    transition_energy_keV: float
    signal_counts: float
    background_counts: float
    background_scale: float
    net_counts: float
    net_uncertainty: float
    significance: float
    status: str


@dataclass(frozen=True)
class CandidateAssessment:
    candidate_id: str
    transition_assessments: tuple[CountAssessment, ...]
    bottleneck_significance: float
    total_net_counts: float
    status: str


@dataclass(frozen=True)
class AgentReview:
    candidate_id: str
    claim: str
    supporting_evidence: tuple[str, ...]
    counterevidence: tuple[str, ...]
    recommendation: str
    confidence: str
    required_next_action: str


@dataclass(frozen=True)
class AgentRound:
    round_index: int
    role: str
    candidate_id: str
    verdict: str
    evidence: tuple[str, ...]
    unresolved: tuple[str, ...]
    required_next_action: str


@dataclass(frozen=True)
class Centroid:
    mean_ps: float
    uncertainty_ps: float
    sum_weights: float
    absolute_sum_weights: float
    iterations: int
    converged: bool
    two_cycle_resolved: bool
    window_low_ps: float
    window_high_ps: float


@dataclass(frozen=True)
class LifetimeEstimate:
    delay_centroid_ps: float
    anti_centroid_ps: float
    delta_c_ps: float
    delta_c_uncertainty_ps: float
    delta_r_ps: float
    delta_r_uncertainty_ps: float
    mean_life_ps: float
    mean_life_uncertainty_ps: float
    half_life_ps: float
    half_life_uncertainty_ps: float
    prd_status: str
    scientific_status: str
    uncertainty_scope: tuple[str, ...]


@dataclass
class WorkflowRecord:
    schema: str
    stage: str
    dataset: dict[str, Any]
    candidates: list[dict[str, Any]]
    assessments: list[dict[str, Any]]
    agent_reviews: list[dict[str, Any]]
    agent_iteration_trace: list[dict[str, Any]]
    selected_candidate_id: str
    human_approval: dict[str, Any]
    gcd: dict[str, Any]
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def as_serializable(value: Any) -> Any:
    """Convert dataclasses and tuples into JSON-compatible values."""
    if hasattr(value, "__dataclass_fields__"):
        return {key: as_serializable(item) for key, item in asdict(value).items()}
    if isinstance(value, tuple):
        return [as_serializable(item) for item in value]
    if isinstance(value, list):
        return [as_serializable(item) for item in value]
    if isinstance(value, dict):
        return {key: as_serializable(item) for key, item in value.items()}
    return value
