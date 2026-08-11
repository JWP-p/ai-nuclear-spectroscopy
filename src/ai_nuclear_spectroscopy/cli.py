"""Command-line interface."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from . import __version__
from .data_sources import NndcEnsdfClient
from .ensdf import parse_ensdf
from .workflow import run_demo


def _demo(args: argparse.Namespace) -> int:
    record = run_demo(args.config, args.output)
    summary = {
        "stage": record.stage,
        "candidate_count": len(record.candidates),
        "selected_candidate_id": record.selected_candidate_id,
        "scientific_status": record.gcd["lifetime_estimate"]["scientific_status"],
        "output": str(args.output),
    }
    print(json.dumps(summary, indent=2))
    return 0


def _inspect_ensdf(args: argparse.Namespace) -> int:
    datasets = parse_ensdf(
        args.input.read_text(encoding="latin-1"),
        source_id=args.source_id,
    )
    result = [
        {
            "dataset_id": dataset.dataset_id,
            "nucleus": dataset.nucleus,
            "title": dataset.title,
            "levels": len(dataset.levels),
            "transitions": len(dataset.transitions),
            "placed_transitions": sum(
                transition.placement_status == "placed_energy_closure"
                for transition in dataset.transitions
            ),
        }
        for dataset in datasets
    ]
    print(json.dumps(result, indent=2))
    return 0


def _fetch_ensdf(args: argparse.Namespace) -> int:
    client = NndcEnsdfClient(timeout_seconds=args.timeout, retries=args.retries)
    references = client.search(args.nucleus, source=args.source)
    if args.limit:
        references = references[: args.limit]
    text, manifest = client.fetch_ensdf_text(references)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    data_path = args.output_dir / f"{args.nucleus}_{args.source}.ens"
    manifest_path = args.output_dir / f"{args.nucleus}_{args.source}.manifest.json"
    data_path.write_text(text, encoding="latin-1")
    manifest_path.write_text(
        json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"data": str(data_path), "manifest": str(manifest_path)}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="anspec",
        description="Auditable human-AI workflows for nuclear spectroscopy.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("demo", help="Run the deterministic synthetic workflow")
    demo.add_argument("--config", type=Path, required=True)
    demo.add_argument("--output", type=Path, required=True)
    demo.set_defaults(handler=_demo)

    inspect = subparsers.add_parser("inspect-ensdf", help="Inspect the supported ENSDF subset")
    inspect.add_argument("--input", type=Path, required=True)
    inspect.add_argument("--source-id", default="USER_SUPPLIED_PUBLIC_ENSDF")
    inspect.set_defaults(handler=_inspect_ensdf)

    fetch = subparsers.add_parser(
        "fetch-ensdf",
        help="Retrieve selected public ENSDF/XUNDL records from NNDC",
    )
    fetch.add_argument("--nucleus", required=True)
    fetch.add_argument("--source", choices=("ensdf", "xundl"), default="ensdf")
    fetch.add_argument("--output-dir", type=Path, required=True)
    fetch.add_argument("--limit", type=int, default=0)
    fetch.add_argument("--timeout", type=int, default=90)
    fetch.add_argument("--retries", type=int, default=3)
    fetch.set_defaults(handler=_fetch_ensdf)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.handler(args))
