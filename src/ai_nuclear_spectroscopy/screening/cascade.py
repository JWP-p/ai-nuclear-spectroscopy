"""Enumerate source-local F-D-G cascades without cross-source stitching."""

from __future__ import annotations

import hashlib
import math
import re
from collections import defaultdict
from collections.abc import Iterable

from ..models import CascadeCandidate, Dataset, HalfLife, Level, Transition

PURE_E0_RE = re.compile(r"^\[?\(?\s*E0\s*\)?\]?$", re.IGNORECASE)


def _stable_id(prefix: str, *parts: object) -> str:
    material = "\x1f".join(str(part) for part in parts)
    return f"{prefix}_{hashlib.sha256(material.encode('utf-8')).hexdigest()[:14]}"


def _lifetime_status(value: HalfLife) -> str:
    if value.relation == "stable":
        return "stable"
    if value.value_ps is None:
        return "unknown"
    if value.relation == "lower_limit" and value.value_ps > 3000.0:
        return "confirmed_gt_3ns"
    if value.relation in {"upper_limit", "lower_limit", "approximate"}:
        return "limit_or_approximate"
    if value.value_ps > 3000.0:
        return "measured_gt_3ns"
    return "measured"


def _intensity_score(
    transitions: tuple[Transition, Transition, Transition],
    maximum: float,
) -> float:
    ratios = [transition.intensity / maximum for transition in transitions if transition.intensity]
    return math.prod(ratios) ** (1.0 / len(ratios)) if ratios else 0.0


def _physics_score(target: Level, intensity_score: float) -> float:
    score = 20.0 * intensity_score
    status = _lifetime_status(target.half_life)
    if status == "unknown":
        score += 28.0
    elif status == "limit_or_approximate":
        score += 10.0
    if target.energy_keV <= 2000.0:
        score += 10.0
    return score


def _is_usable(transition: Transition) -> bool:
    return bool(
        transition.initial_level_id
        and transition.final_level_id
        and transition.placement_status == "placed_energy_closure"
        and not PURE_E0_RE.fullmatch(transition.multipolarity.strip())
    )


def enumerate_cascades(dataset: Dataset) -> list[CascadeCandidate]:
    """Return all three-transition source-local cascades in both gate orientations."""
    level_by_id = {level.level_id: level for level in dataset.levels}
    outgoing: dict[str, list[Transition]] = defaultdict(list)
    usable = [transition for transition in dataset.transitions if _is_usable(transition)]
    for transition in usable:
        outgoing[transition.initial_level_id].append(transition)
    maximum = max(
        (transition.intensity or 0.0 for transition in usable),
        default=0.0,
    )
    maximum = maximum or 1.0
    candidates: list[CascadeCandidate] = []
    for first in usable:
        for second in outgoing.get(first.final_level_id, []):
            for third in outgoing.get(second.final_level_id, []):
                level_ids = (
                    first.initial_level_id,
                    first.final_level_id,
                    second.final_level_id,
                    third.final_level_id,
                )
                if len(set(level_ids)) != 4:
                    continue
                chain = (first, second, third)
                intensity_score = _intensity_score(chain, maximum)
                orientations = (
                    (level_ids[1], first, second, third, "downstream"),
                    (level_ids[2], second, third, first, "upstream"),
                )
                for target_id, feeder, decay, gate, gate_position in orientations:
                    target = level_by_id[target_id]
                    candidate_id = _stable_id(
                        "CASCADE",
                        dataset.dataset_id,
                        target_id,
                        feeder.transition_id,
                        decay.transition_id,
                        gate.transition_id,
                        gate_position,
                    )
                    candidates.append(
                        CascadeCandidate(
                            candidate_id=candidate_id,
                            nucleus=dataset.nucleus,
                            target_level_id=target_id,
                            target_energy_keV=target.energy_keV,
                            target_jpi=target.jpi,
                            lifetime_status=_lifetime_status(target.half_life),
                            feeder_transition_id=feeder.transition_id,
                            decay_transition_id=decay.transition_id,
                            gate_transition_id=gate.transition_id,
                            feeder_energy_keV=feeder.energy_keV,
                            decay_energy_keV=decay.energy_keV,
                            gate_energy_keV=gate.energy_keV,
                            gate_position=gate_position,
                            intensity_score=intensity_score,
                            physics_score=_physics_score(target, intensity_score),
                            source_id=target.source_id,
                        )
                    )
    return rank_candidates(candidates)


def rank_candidates(candidates: Iterable[CascadeCandidate]) -> list[CascadeCandidate]:
    return sorted(
        candidates,
        key=lambda item: (-item.physics_score, item.target_energy_keV, item.candidate_id),
    )
