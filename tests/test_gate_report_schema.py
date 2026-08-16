from __future__ import annotations

import json
from datetime import date
from importlib import resources
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from goverdocs import gate


def test_gate_report_matches_packaged_json_schema(monkeypatch, tmp_path: Path) -> None:
    policy_path = tmp_path / "policy.yaml"
    matrix_path = tmp_path / "matrix.yaml"
    metadata_schema_path = tmp_path / "metadata-schema.json"
    change_gate_path = tmp_path / "change-gate.yaml"
    change_gate_schema_path = tmp_path / "change-gate-schema.json"

    for path in (
        policy_path,
        matrix_path,
        metadata_schema_path,
        change_gate_path,
        change_gate_schema_path,
    ):
        path.write_text("{}\n", encoding="utf-8")

    monkeypatch.setattr(gate, "classify", lambda changed_files, diff_text: [])
    monkeypatch.setattr(gate, "plan", lambda events, matrix_path: [])
    monkeypatch.setattr(gate, "load_matrix", lambda matrix_path: {"rules": []})
    monkeypatch.setattr(gate, "validate_project", lambda *args, **kwargs: [])
    monkeypatch.setattr(gate, "governed_documents", lambda root, policy_path: [])

    report = gate.evaluate_gate(
        root=tmp_path,
        policy_path=policy_path,
        matrix_path=matrix_path,
        metadata_schema_path=metadata_schema_path,
        change_gate_path=change_gate_path,
        change_gate_schema_path=change_gate_schema_path,
        changed_files=["README.md"],
        diff_text="documentation-only change",
        as_of=date(2026, 8, 17),
    )

    schema_path = resources.files("goverdocs").joinpath("resources/gate-report.schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    assert list(validator.iter_errors(report)) == []
    assert report["schema_version"] == 1
    assert report["status"] == "PASS"
