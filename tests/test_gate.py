from __future__ import annotations

from datetime import date
from pathlib import Path

from goverdocs import gate
from goverdocs.models import Event, Operation


def _policy_files(tmp_path: Path) -> dict[str, Path]:
    paths = {
        "policy_path": tmp_path / "policy.yaml",
        "matrix_path": tmp_path / "matrix.yaml",
        "metadata_schema_path": tmp_path / "schema.json",
        "change_gate_path": tmp_path / "change-gate.yaml",
        "change_gate_schema_path": tmp_path / "change-gate-schema.json",
    }
    for path in paths.values():
        path.write_text("{}\n", encoding="utf-8")
    return paths


def test_gate_blocks_when_explicit_approval_is_required(monkeypatch, tmp_path: Path) -> None:
    paths = _policy_files(tmp_path)
    event = Event("architecture_change", 0.9, ["matched path"])
    operation = Operation(
        event="architecture_change",
        rule_id="DOC-EVT-ARCH",
        document_type="architecture-decision",
        action="update",
        target="docs/architecture/ARCH-*.md",
        write_policy="approval-required",
        approval_required=True,
        severity="high",
        priority=90,
    )

    monkeypatch.setattr(gate, "classify", lambda changed_files, diff_text: [event])
    monkeypatch.setattr(gate, "plan", lambda events, matrix_path: [operation])
    monkeypatch.setattr(
        gate,
        "load_matrix",
        lambda matrix_path: {
            "rules": [
                {
                    "id": "DOC-EVT-ARCH",
                    "event": "architecture_change",
                    "severity": "high",
                    "priority": 90,
                    "required_evidence": ["source reference"],
                    "approval": {"required": True, "roles": ["architect"]},
                }
            ]
        },
    )
    monkeypatch.setattr(gate, "validate_project", lambda *args, **kwargs: [])
    monkeypatch.setattr(gate, "governed_documents", lambda root, policy_path: [])

    report = gate.evaluate_gate(
        root=tmp_path,
        changed_files=["docs/architecture/ARCH-0002.md"],
        diff_text="architecture changed",
        as_of=date(2026, 8, 17),
        **paths,
    )

    assert report["status"] == "BLOCKED"
    assert report["obligations"][0]["approval_required"] is True
    assert any(item["code"] == "APPROVAL_REQUIRED" and item["blocking"] for item in report["evidence_gaps"])
    assert any(item["code"] == "EVIDENCE_UNVERIFIED" and not item["blocking"] for item in report["evidence_gaps"])


def test_gate_warns_when_matrix_detection_outpaces_classifier(monkeypatch, tmp_path: Path) -> None:
    paths = _policy_files(tmp_path)
    fallback = Event("project_state_changed", 0.55, ["fallback classification"])

    monkeypatch.setattr(gate, "classify", lambda changed_files, diff_text: [fallback])
    monkeypatch.setattr(gate, "plan", lambda events, matrix_path: [])
    monkeypatch.setattr(
        gate,
        "load_matrix",
        lambda matrix_path: {
            "rules": [
                {
                    "id": "DOC-EVT-011",
                    "event": "architecture_change",
                    "severity": "high",
                    "priority": 80,
                    "detection": {"any": [{"changed_paths": ["src/**"]}]},
                    "required_evidence": [],
                    "approval": {"required": True, "roles": ["project-owner"]},
                }
            ]
        },
    )
    monkeypatch.setattr(gate, "validate_project", lambda *args, **kwargs: [])
    monkeypatch.setattr(gate, "governed_documents", lambda root, policy_path: [])

    report = gate.evaluate_gate(
        root=tmp_path,
        changed_files=["src/goverdocs/gate.py"],
        diff_text="",
        as_of=date(2026, 8, 17),
        **paths,
    )

    drift = [item for item in report["evidence_gaps"] if item["code"] == "CLASSIFIER_MATRIX_DRIFT"]
    assert report["status"] == "WARN"
    assert len(drift) == 1
    assert drift[0]["subject"] == "DOC-EVT-011"
    assert "architecture_change" in drift[0]["message"]
    assert "src/goverdocs/gate.py" in drift[0]["message"]
    assert drift[0]["blocking"] is False


def test_gate_warns_for_overdue_governed_document(monkeypatch, tmp_path: Path) -> None:
    paths = _policy_files(tmp_path)
    document = tmp_path / "PROJECT_STATE.md"
    document.write_text(
        """---
id: PROJECT-STATE-TEST
type: project-state
title: Test state
status: active
owner: TEST
created: 2026-08-01
updated: 2026-08-01
version: 1.0.0
canonical: true
managed_by: human
write_policy: approval-required
related: []
source_refs: []
last_verified: 2026-08-01
review_due: 2026-08-15
---
# Test
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(gate, "classify", lambda changed_files, diff_text: [])
    monkeypatch.setattr(gate, "plan", lambda events, matrix_path: [])
    monkeypatch.setattr(gate, "load_matrix", lambda matrix_path: {"rules": []})
    monkeypatch.setattr(gate, "validate_project", lambda *args, **kwargs: [])
    monkeypatch.setattr(gate, "governed_documents", lambda root, policy_path: [document])

    report = gate.evaluate_gate(
        root=tmp_path,
        changed_files=[],
        diff_text="",
        as_of=date(2026, 8, 17),
        **paths,
    )

    assert report["status"] == "WARN"
    assert report["evaluation_date"] == "2026-08-17"
    assert report["evidence_gaps"] == [
        {
            "code": "REVIEW_OVERDUE",
            "severity": "warning",
            "blocking": False,
            "subject": "PROJECT_STATE.md",
            "message": "review_due 2026-08-15 is before evaluation date 2026-08-17",
        }
    ]


def test_gate_report_is_deterministic_for_explicit_evaluation_date(monkeypatch, tmp_path: Path) -> None:
    paths = _policy_files(tmp_path)
    monkeypatch.setattr(gate, "classify", lambda changed_files, diff_text: [])
    monkeypatch.setattr(gate, "plan", lambda events, matrix_path: [])
    monkeypatch.setattr(gate, "load_matrix", lambda matrix_path: {"rules": []})
    monkeypatch.setattr(gate, "validate_project", lambda *args, **kwargs: [])
    monkeypatch.setattr(gate, "governed_documents", lambda root, policy_path: [])

    kwargs = {
        "root": tmp_path,
        "changed_files": ["src/example.py"],
        "diff_text": "+example\n",
        "as_of": date(2026, 8, 17),
        **paths,
    }

    assert gate.evaluate_gate(**kwargs) == gate.evaluate_gate(**kwargs)
