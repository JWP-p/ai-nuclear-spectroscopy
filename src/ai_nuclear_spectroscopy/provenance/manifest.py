"""Deterministic provenance manifests for workflow inputs and outputs."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_manifest(
    *,
    inputs: Iterable[Path],
    outputs: Iterable[Path],
    workflow_version: str,
    data_classification: str,
) -> dict[str, Any]:
    """Build a manifest without embedding machine-specific absolute paths."""

    def item(path: Path) -> dict[str, Any]:
        return {
            "name": path.name,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }

    return {
        "schema": "ai_nuclear_spectroscopy_provenance_v1",
        "created_utc": datetime.now(UTC).isoformat(),
        "workflow_version": workflow_version,
        "data_classification": data_classification,
        "runtime": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": sys.platform,
        },
        "inputs": [item(path) for path in inputs],
        "outputs": [item(path) for path in outputs],
    }
