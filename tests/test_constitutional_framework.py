from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from goverdocs.config import load_config
from goverdocs.constitutional import (
    APPROVAL_GATE_REFERENCE,
    CHANGE_PRINCIPLE,
    EXPECTED_DIMENSION_COUNT,
    EXPECTED_WORLD_SHA256,
    MOTTO,
    REQUIRED_REPORTING_FIELDS,
    _validate_manifest_integrity,
    validate_constitutional_framework,
)

ROOT = Path(__file__).resolve().parents[1]


def test_world_bytes_remain_unchanged() -> None:
    path = ROOT / "WORLD_CLASS_SOFTWARE_DEVOPS_OPERATING_MODE.md"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == EXPECTED_WORLD_SHA256


def test_optional_gate_configuration_is_loaded() -> None:
    config = load_config(ROOT)
    assert config.change_gate_path == ROOT / "policies/CHANGE_GATE_10_OF_10.yaml"
    assert config.change_gate_schema_path == ROOT / "schemas/change-gate.schema.json"


def test_change_gate_schema_and_contract() -> None:
    gate = yaml.safe_load((ROOT / "policies/CHANGE_GATE_10_OF_10.yaml").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "schemas/change-gate.schema.json").read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(gate))
    assert errors == []

    dimension_ids = [item["id"] for item in gate["dimensions"]]
    assert len(dimension_ids) == EXPECTED_DIMENSION_COUNT
    assert len(dimension_ids) == len(set(dimension_ids))
    assert gate["approval_gate_reference"] == APPROVAL_GATE_REFERENCE
    assert tuple(gate["reporting_requires"]) == REQUIRED_REPORTING_FIELDS
    assert gate["status"] == "active"
    assert gate["enforcement"] == "warn-only"


def test_framework_has_both_exact_invariants_and_truth_statuses() -> None:
    framework = (ROOT / "GOVERDOCS_CONSTITUTIONAL_FRAMEWORK.md").read_text(encoding="utf-8")
    product = (ROOT / "PRODUCT_DECISION_EXECUTION_OPERATING_MODE.md").read_text(encoding="utf-8")
    normalised = " ".join((framework + "\n" + product).split())
    assert normalised.count(MOTTO) == 1
    assert normalised.count(CHANGE_PRINCIPLE) == 1
    assert '<a id="approval-gates"></a>' in framework
    for status in (
        "PROPOSED",
        "APPROVED",
        "IMPLEMENTED",
        "VERIFIED",
        "INFERRED",
        "UNKNOWN",
        "BLOCKED",
        "PARTIALLY VERIFIED",
    ):
        assert status in framework


def test_framework_validation_passes_for_repository_artifacts() -> None:
    config = load_config(ROOT)
    issues = validate_constitutional_framework(
        ROOT,
        config.change_gate_path,
        config.change_gate_schema_path,
    )
    assert issues == []


def test_manifest_checksums_match_all_framework_artifacts() -> None:
    manifest = yaml.safe_load((ROOT / "manifests/GOVERNANCE_ARTIFACTS.yaml").read_text(encoding="utf-8"))
    by_path = {item["path"]: item for item in manifest["artifacts"]}
    expected = {
        "GOVERDOCS_CONSTITUTIONAL_FRAMEWORK.md",
        "PRODUCT_DECISION_EXECUTION_OPERATING_MODE.md",
        "policies/CHANGE_GATE_10_OF_10.yaml",
        "schemas/change-gate.schema.json",
    }
    assert expected <= set(by_path)
    for relative in expected:
        artifact = by_path[relative]
        assert artifact["status"] == "active"
        assert artifact["write_policy"] == "approval-required"
        assert artifact["integrity"]["algorithm"] == "sha256"
        assert artifact["integrity"]["digest"] == hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def test_manifest_duplicate_paths_and_ids_are_rejected(tmp_path: Path) -> None:
    target = tmp_path / "artifact.txt"
    target.write_text("same\n", encoding="utf-8")
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    manifest = tmp_path / "manifests/GOVERNANCE_ARTIFACTS.yaml"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "artifacts": [
                    {"id": "DUP", "path": "artifact.txt", "integrity": {"algorithm": "sha256", "digest": digest}},
                    {"id": "DUP", "path": "artifact.txt", "integrity": {"algorithm": "sha256", "digest": digest}},
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    codes = {issue.code for issue in _validate_manifest_integrity(tmp_path, {"artifact.txt"})}
    assert "CONSTITUTION_MANIFEST_DUPLICATE_PATH" in codes
    assert "CONSTITUTION_MANIFEST_DUPLICATE_ID" in codes


def test_optional_configuration_does_not_break_projects_without_gate() -> None:
    config_path = ROOT / ".goverdocs.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config.pop("change_gate_path")
    config.pop("change_gate_schema_path")
    assert "change_gate_path" not in config
    assert validate_constitutional_framework(ROOT, None, None) == []


def test_gate_configuration_cannot_escape_project_root(tmp_path: Path) -> None:
    issues = validate_constitutional_framework(
        ROOT,
        tmp_path / "outside.yaml",
        ROOT / "schemas/change-gate.schema.json",
    )
    assert len(issues) == 1
    assert issues[0].code == "CHANGE_GATE_PATH"
