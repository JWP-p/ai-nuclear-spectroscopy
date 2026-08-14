"""End-to-end synthetic workflow used by the public reference implementation."""

from __future__ import annotations

import json
import math
from dataclasses import asdict
from pathlib import Path
from typing import Any

from . import __version__
from .agents import (
    ScientificStage,
    build_agent_iteration_trace,
    build_agent_reviews,
    require_human_approval,
    select_review_candidate,
)
from .ensdf import parse_ensdf
from .gcd import (
    PRDModel,
    build_prd_covariance,
    estimate_lifetime,
    four_region_subtract,
    iterative_centroid,
)
from .models import WorkflowRecord, as_serializable
from .provenance import build_manifest, write_json
from .screening import enumerate_cascades
from .statistics import CountObservation, assess_candidate


def _load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("schema") != "ai_nuclear_spectroscopy_demo_v1":
        raise ValueError("Unsupported or missing demo configuration schema")
    return config


def _resolve_relative(config_path: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (config_path.parent / path).resolve()


def _synthetic_regions(
    *,
    center_ps: float,
    amplitude: float,
    sigma_ps: float,
    time_min_ps: float,
    time_max_ps: float,
    bin_width_ps: float,
    scales: tuple[float, float, float],
) -> tuple[list[float], dict[str, list[float]]]:
    count = int(round((time_max_ps - time_min_ps) / bin_width_ps)) + 1
    times = [time_min_ps + index * bin_width_ps for index in range(count)]
    signal = [
        amplitude * math.exp(-0.5 * ((time - center_ps) / sigma_ps) ** 2)
        for time in times
    ]
    background_x = [16.0 + 1.5 * math.cos(index / 21.0) for index in range(count)]
    background_y = [14.0 + 1.0 * math.sin(index / 17.0) for index in range(count)]
    background_xy = [9.0 + 0.7 * math.cos(index / 13.0) for index in range(count)]
    scale_x, scale_y, scale_xy = scales
    peak = [
        max(
            0.0,
            s + scale_x * x + scale_y * y - scale_xy * xy,
        )
        for s, x, y, xy in zip(
            signal,
            background_x,
            background_y,
            background_xy,
            strict=True,
        )
    ]
    return times, {
        "peak": peak,
        "background_x": background_x,
        "background_y": background_y,
        "background_xy": background_xy,
    }


def _markdown_report(record: WorkflowRecord) -> str:
    gcd = record.gcd["lifetime_estimate"]
    selected = next(
        candidate
        for candidate in record.candidates
        if candidate["candidate_id"] == record.selected_candidate_id
    )
    lines = [
        "# Synthetic Human-AI Nuclear-Spectroscopy Workflow Report",
        "",
        "> This report is generated from fictional nuclear levels and deterministic "
        "synthetic spectra. ",
        "> It is a software demonstration, not an experimental lifetime result.",
        "",
        "## Evidence chain",
        "",
        f"- Parsed source: `{record.dataset['title']}`",
        f"- Candidate count: `{len(record.candidates)}`",
        f"- Selected review candidate: `{record.selected_candidate_id}`",
        f"- Human approval scope: `{record.human_approval['scope']}`",
        f"- Workflow stage: `{record.stage}`",
        "",
        "## Selected F-D-G path",
        "",
        f"- Synthetic nucleus: `{selected['nucleus']}`",
        f"- Target excitation energy: `{selected['target_energy_keV']:.1f} keV`",
        f"- Feeder transition: `{selected['feeder_energy_keV']:.1f} keV`",
        f"- Decay transition: `{selected['decay_energy_keV']:.1f} keV`",
        f"- Remote gate: `{selected['gate_energy_keV']:.1f} keV`",
        f"- Gate position: `{selected['gate_position']}`",
        "",
        "## Synthetic GCD estimate",
        "",
        f"- Delay centroid: `{gcd['delay_centroid_ps']:.3f} ps`",
        f"- Anti-delay centroid: `{gcd['anti_centroid_ps']:.3f} ps`",
        f"- Delta C: `{gcd['delta_c_ps']:.3f} ± {gcd['delta_c_uncertainty_ps']:.3f} ps`",
        f"- Delta R: `{gcd['delta_r_ps']:.3f} ± {gcd['delta_r_uncertainty_ps']:.3f} ps`",
        f"- Mean life: `{gcd['mean_life_ps']:.3f} ± {gcd['mean_life_uncertainty_ps']:.3f} ps`",
        f"- Half-life: `{gcd['half_life_ps']:.3f} ± {gcd['half_life_uncertainty_ps']:.3f} ps`",
        f"- Scientific status: `{gcd['scientific_status']}`",
        "",
        "## Boundaries",
        "",
    ]
    lines.extend(f"- {item}" for item in record.limitations)
    lines.extend(
        [
            "",
            "The AI review is a structured recommendation. It does not replace source validation, ",
            "detector-response validation, systematics, or an authorised formal analysis.",
            "",
        ]
    )
    return "\n".join(lines)


def run_demo(config_path: Path, output_dir: Path) -> WorkflowRecord:
    """Run the complete deterministic synthetic demonstration."""
    config_path = config_path.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    config = _load_config(config_path)
    ensdf_path = _resolve_relative(config_path, config["input"]["ensdf_path"])
    datasets = parse_ensdf(
        ensdf_path.read_text(encoding="latin-1"),
        source_id=config["input"]["source_id"],
    )
    if len(datasets) != 1:
        raise ValueError("The synthetic demonstration expects exactly one ENSDF dataset")
    dataset = datasets[0]
    candidates = enumerate_cascades(dataset)
    if not candidates:
        raise ValueError("No source-local three-transition cascades were found")

    observations = [CountObservation(**row) for row in config["statistics"]["observations"]]
    assessments = [assess_candidate(candidate, observations) for candidate in candidates]
    reviews = build_agent_reviews(candidates, assessments)
    selected_id = select_review_candidate(candidates, assessments)
    iteration_trace = build_agent_iteration_trace(
        candidates,
        assessments,
        reviews,
        selected_candidate_id=selected_id,
    )
    if iteration_trace[-1].verdict != "READY_FOR_HUMAN_DECISION":
        raise PermissionError(
            "The iterative evidence review is on hold; human approval cannot bypass "
            "incomplete prerequisite evidence"
        )
    selected = next(candidate for candidate in candidates if candidate.candidate_id == selected_id)
    human_gate = config["human_gate"]
    approved = human_gate["approved"]
    if not isinstance(approved, bool):
        raise ValueError("human_gate.approved must be a JSON boolean")
    approval = require_human_approval(
        candidate_id=selected_id,
        approved=approved,
        reviewer=human_gate["reviewer"],
        scope=human_gate["scope"],
        approved_utc=human_gate["approved_utc"],
    )

    prd_config = config["gcd"]["prd_model"]
    model = PRDModel(**prd_config)
    fit_points = [tuple(float(value) for value in row) for row in config["gcd"]["fit_points"]]
    covariance = build_prd_covariance(model, fit_points)
    delta_r = model.difference_ps(selected.decay_energy_keV, selected.feeder_energy_keV)
    true_mean_life = float(config["gcd"]["synthetic_mean_life_ps"])
    anti_center = float(config["gcd"]["anti_center_ps"])
    delay_center = anti_center + 2.0 * true_mean_life + delta_r
    spectrum = config["gcd"]["spectrum"]
    scales = (
        float(spectrum["scale_x"]),
        float(spectrum["scale_y"]),
        float(spectrum["scale_xy"]),
    )
    common = {
        "amplitude": float(spectrum["amplitude"]),
        "sigma_ps": float(spectrum["sigma_ps"]),
        "time_min_ps": float(spectrum["time_min_ps"]),
        "time_max_ps": float(spectrum["time_max_ps"]),
        "bin_width_ps": float(spectrum["bin_width_ps"]),
        "scales": scales,
    }
    delay_times, delay_regions = _synthetic_regions(center_ps=delay_center, **common)
    anti_times, anti_regions = _synthetic_regions(center_ps=anti_center, **common)
    delay_net = four_region_subtract(
        **delay_regions,
        scale_x=scales[0],
        scale_y=scales[1],
        scale_xy=scales[2],
    )
    anti_net = four_region_subtract(
        **anti_regions,
        scale_x=scales[0],
        scale_y=scales[1],
        scale_xy=scales[2],
    )
    centroid_settings = config["gcd"]["centroid"]
    delay_centroid = iterative_centroid(
        delay_times,
        delay_net.values,
        delay_net.variances,
        half_width_ps=float(centroid_settings["half_width_ps"]),
        max_iterations=int(centroid_settings["max_iterations"]),
        tolerance_ps=float(centroid_settings["tolerance_ps"]),
    )
    anti_centroid = iterative_centroid(
        anti_times,
        anti_net.values,
        anti_net.variances,
        half_width_ps=float(centroid_settings["half_width_ps"]),
        max_iterations=int(centroid_settings["max_iterations"]),
        tolerance_ps=float(centroid_settings["tolerance_ps"]),
    )
    lifetime = estimate_lifetime(
        delay=delay_centroid,
        anti=anti_centroid,
        decay_energy_keV=selected.decay_energy_keV,
        feeder_energy_keV=selected.feeder_energy_keV,
        prd_model=model,
        prd_covariance=covariance,
    )

    record = WorkflowRecord(
        schema="ai_nuclear_spectroscopy_workflow_record_v1",
        stage=ScientificStage.GCD_ESTIMATED,
        dataset={
            "dataset_id": dataset.dataset_id,
            "nucleus": dataset.nucleus,
            "title": dataset.title,
            "source_id": config["input"]["source_id"],
            "level_count": len(dataset.levels),
            "transition_count": len(dataset.transitions),
            "classification": "SYNTHETIC_PUBLIC_FIXTURE",
        },
        candidates=[as_serializable(row) for row in candidates],
        assessments=[as_serializable(row) for row in assessments],
        agent_reviews=[as_serializable(row) for row in reviews],
        agent_iteration_trace=[as_serializable(row) for row in iteration_trace],
        selected_candidate_id=selected_id,
        human_approval=approval,
        gcd={
            "four_region_formula": delay_net.formula,
            "delay_centroid": as_serializable(delay_centroid),
            "anti_centroid": as_serializable(anti_centroid),
            "prd_model": asdict(model),
            "prd_covariance_abc": covariance,
            "lifetime_estimate": as_serializable(lifetime),
        },
        limitations=[
            "All levels, transitions, counts, spectra, and calibration points are synthetic.",
            "The ENSDF parser implements a documented subset and is not an evaluator tool.",
            "No detector geometry, gate-width, time-walk model, or calibration "
            "systematic is validated.",
            "The result is an initial synthetic estimate and cannot be promoted "
            "to a formal lifetime.",
            "A model recommendation and a software test pass are not scientific acceptance.",
        ],
    )
    result_path = output_dir / "workflow_result.json"
    report_path = output_dir / "workflow_report.md"
    write_json(result_path, record.to_dict())
    report_path.write_text(_markdown_report(record), encoding="utf-8")
    manifest = build_manifest(
        inputs=(config_path, ensdf_path),
        outputs=(result_path, report_path),
        workflow_version=__version__,
        data_classification="SYNTHETIC_PUBLIC_FIXTURE",
    )
    write_json(output_dir / "provenance_manifest.json", manifest)
    return record
