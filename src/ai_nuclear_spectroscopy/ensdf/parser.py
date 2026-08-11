"""A deliberately small, inspectable subset of the ENSDF fixed-width format.

The parser covers identification, level, and gamma records needed by the public
demonstration. It does not claim to replace the official ENSDF analysis tools.
Unsupported or ambiguous placements remain explicit instead of being guessed.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass

from ..models import Dataset, HalfLife, Level, Transition

NUMBER_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")
HALF_LIFE_RE = re.compile(
    r"(?P<rel>[<>])?\s*(?P<value>\d+(?:\.\d+)?)\s*"
    r"(?P<unit>AS|FS|PS|NS|US|MS|S|M|H|D|Y)\b",
    re.IGNORECASE,
)
UNIT_TO_PS = {
    "AS": 1e-6,
    "FS": 1e-3,
    "PS": 1.0,
    "NS": 1e3,
    "US": 1e6,
    "MS": 1e9,
    "S": 1e12,
    "M": 60e12,
    "H": 3600e12,
    "D": 86400e12,
    "Y": 365.25 * 86400e12,
}


class EnsdfParseError(ValueError):
    """Raised when an ENSDF record cannot satisfy the declared subset."""


@dataclass(frozen=True)
class _PendingGamma:
    initial_level_id: str
    energy_keV: float
    intensity: float | None
    multipolarity: str
    source_line: int


def _stable_id(prefix: str, *parts: object) -> str:
    material = "\x1f".join(str(part) for part in parts)
    return f"{prefix}_{hashlib.sha256(material.encode('utf-8')).hexdigest()[:14]}"


def _first_number(value: str) -> float | None:
    match = NUMBER_RE.search(value or "")
    return float(match.group()) if match else None


def _normalize_nucleus(value: str) -> str:
    match = re.match(r"\s*(\d+)\s*([A-Za-z]+)", value)
    if not match:
        stripped = value.strip()
        if not stripped:
            raise EnsdfParseError("Dataset identification record has no nucleus")
        return stripped
    return f"{int(match.group(1))}{match.group(2).title()}"


def parse_half_life(raw_value: str, raw_uncertainty: str = "") -> HalfLife:
    display = " ".join(part for part in (raw_value.strip(), raw_uncertainty.strip()) if part)
    if not display:
        return HalfLife(display="not listed", value_ps=None, relation="unknown")
    upper = display.upper()
    if "STABLE" in upper:
        return HalfLife(display=display, value_ps=None, relation="stable")
    match = HALF_LIFE_RE.search(upper)
    if not match:
        return HalfLife(display=display, value_ps=None, relation="unknown")
    relation = "measured"
    explicit = match.group("rel")
    if explicit == "<" or re.search(r"(?:^|\s)(?:LE|LT)(?:\s|$)", upper):
        relation = "upper_limit"
    elif explicit == ">" or re.search(r"(?:^|\s)(?:GE|GT)(?:\s|$)", upper):
        relation = "lower_limit"
    elif re.search(r"(?:^|\s)(?:AP|CA)(?:\s|$)", upper):
        relation = "approximate"
    return HalfLife(
        display=display,
        value_ps=float(match.group("value")) * UNIT_TO_PS[match.group("unit").upper()],
        relation=relation,
    )


def _split_blocks(text: str) -> list[list[tuple[int, str]]]:
    blocks: list[list[tuple[int, str]]] = []
    current: list[tuple[int, str]] = []
    for line_number, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip("\r\n")
        if not line.strip():
            if current:
                blocks.append(current)
                current = []
            continue
        current.append((line_number, line.ljust(80)))
    if current:
        blocks.append(current)
    return blocks


def _infer_final_level(
    *,
    initial: Level,
    gamma_energy_keV: float,
    levels: list[Level],
    tolerance_keV: float,
) -> tuple[str, str]:
    target = initial.energy_keV - gamma_energy_keV
    candidates = [
        (abs(level.energy_keV - target), level)
        for level in levels
        if level.level_id != initial.level_id and level.energy_keV <= initial.energy_keV + 0.1
    ]
    candidates = [item for item in candidates if item[0] <= tolerance_keV]
    if not candidates:
        return "", "unplaced_energy_mismatch"
    candidates.sort(key=lambda item: (item[0], item[1].level_id))
    if len(candidates) > 1 and math.isclose(candidates[0][0], candidates[1][0], abs_tol=0.12):
        return "", "ambiguous_final_level"
    return candidates[0][1].level_id, "placed_energy_closure"


def _parse_block(
    block: list[tuple[int, str]],
    *,
    source_id: str,
    block_index: int,
    placement_tolerance_keV: float,
) -> Dataset:
    first_line_number, first = block[0]
    nucleus = _normalize_nucleus(first[:5])
    title = first[9:39].strip() or "UNSPECIFIED DATASET"
    dataset_id = _stable_id("DATASET", source_id, nucleus, title, block_index)
    levels: list[Level] = []
    pending: list[_PendingGamma] = []
    current_level_id = ""

    for line_number, line in block[1:]:
        record_type = line[7]
        continuation = line[5]
        primary = continuation == " " and line[6] == " "
        if primary and record_type == "L":
            energy_raw = line[9:19].strip()
            energy = _first_number(energy_raw)
            if energy is None:
                current_level_id = ""
                continue
            level_id = _stable_id("LEVEL", dataset_id, len(levels), energy_raw, line_number)
            level = Level(
                level_id=level_id,
                nucleus=nucleus,
                energy_keV=energy,
                energy_raw=energy_raw,
                jpi=line[21:39].strip(),
                half_life=parse_half_life(line[39:49], line[49:55]),
                source_id=source_id,
                source_line=line_number,
            )
            levels.append(level)
            current_level_id = level_id
        elif primary and record_type == "G":
            energy = _first_number(line[9:19])
            if energy is None or not current_level_id:
                continue
            pending.append(
                _PendingGamma(
                    initial_level_id=current_level_id,
                    energy_keV=energy,
                    intensity=_first_number(line[21:29]),
                    multipolarity=line[31:41].strip(),
                    source_line=line_number,
                )
            )

    if not levels:
        raise EnsdfParseError(
            f"ENSDF block beginning at line {first_line_number} contains no numeric levels"
        )
    by_id = {level.level_id: level for level in levels}
    transitions: list[Transition] = []
    for index, gamma in enumerate(pending):
        initial = by_id[gamma.initial_level_id]
        final_level_id, status = _infer_final_level(
            initial=initial,
            gamma_energy_keV=gamma.energy_keV,
            levels=levels,
            tolerance_keV=placement_tolerance_keV,
        )
        transitions.append(
            Transition(
                transition_id=_stable_id(
                    "GAMMA", dataset_id, index, gamma.initial_level_id, gamma.energy_keV
                ),
                nucleus=nucleus,
                initial_level_id=gamma.initial_level_id,
                final_level_id=final_level_id,
                energy_keV=gamma.energy_keV,
                intensity=gamma.intensity,
                multipolarity=gamma.multipolarity,
                placement_status=status,
                source_id=source_id,
                source_line=gamma.source_line,
            )
        )
    return Dataset(
        dataset_id=dataset_id,
        nucleus=nucleus,
        title=title,
        levels=tuple(levels),
        transitions=tuple(transitions),
    )


def parse_ensdf(
    text: str,
    *,
    source_id: str,
    placement_tolerance_keV: float = 1.5,
) -> list[Dataset]:
    """Parse the supported ENSDF subset into source-preserving datasets."""
    if placement_tolerance_keV <= 0:
        raise ValueError("placement_tolerance_keV must be positive")
    blocks = _split_blocks(text)
    if not blocks:
        raise EnsdfParseError("ENSDF input is empty")
    return [
        _parse_block(
            block,
            source_id=source_id,
            block_index=index,
            placement_tolerance_keV=placement_tolerance_keV,
        )
        for index, block in enumerate(blocks, start=1)
    ]
