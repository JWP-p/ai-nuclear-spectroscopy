import json
from pathlib import Path

import pytest

from ai_nuclear_spectroscopy.workflow import run_demo


def test_complete_synthetic_workflow(tmp_path: Path) -> None:
    record = run_demo(Path("configs/demo_workflow.json"), tmp_path)
    assert record.stage == "GCD_ESTIMATED"
    assert record.dataset["classification"] == "SYNTHETIC_PUBLIC_FIXTURE"
    assert record.gcd["lifetime_estimate"]["scientific_status"] == (
        "SYNTHETIC_ESTIMATE_NOT_FORMAL_RELEASE"
    )
    assert [round_["role"] for round_ in record.agent_iteration_trace] == [
        "candidate_selector",
        "evidence_critic",
        "review_synthesizer",
    ]
    assert (tmp_path / "workflow_result.json").is_file()
    assert (tmp_path / "workflow_report.md").is_file()
    manifest = json.loads((tmp_path / "provenance_manifest.json").read_text())
    assert manifest["data_classification"] == "SYNTHETIC_PUBLIC_FIXTURE"
    assert len(manifest["inputs"]) == 2
    assert len(manifest["outputs"]) == 2


def test_workflow_result_contains_no_absolute_paths(tmp_path: Path) -> None:
    run_demo(Path("configs/demo_workflow.json"), tmp_path)
    result = (tmp_path / "workflow_result.json").read_text()
    macos_home_prefix = "/" + "Users" + "/"
    linux_home_prefix = "/" + "home" + "/"
    assert macos_home_prefix not in result
    assert linux_home_prefix not in result


def test_workflow_rejects_non_boolean_human_gate(tmp_path: Path) -> None:
    config = json.loads(Path("configs/demo_workflow.json").read_text())
    config["input"]["ensdf_path"] = str(
        Path("examples/synthetic_ensdf/fictional_999xx.ens").resolve()
    )
    config["human_gate"]["approved"] = "false"
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match="human_gate.approved"):
        run_demo(config_path, tmp_path / "output")
