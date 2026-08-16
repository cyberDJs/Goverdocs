from __future__ import annotations

from datetime import date
from pathlib import Path

import goverdocs.gate as gate
from goverdocs.evidence import change_digest, validate_record
from goverdocs.models import Event, Operation


TRUSTED_VERIFIER = "github-api:cyberDJs/Goverdocs"
REPOSITORY = "cyberDJs/Goverdocs"
PR_NUMBER = 4
HEAD_SHA = "a" * 40


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


def _configure_rule(monkeypatch, *, approval_required: bool) -> None:
    event = Event("architecture_change", 0.9, ["matched path"])
    operation = Operation(
        event="architecture_change",
        rule_id="DOC-EVT-ARCH",
        document_type="architecture-decision",
        action="update",
        target="docs/architecture/ARCH-*.md",
        write_policy="approval-required" if approval_required else "automatic",
        approval_required=approval_required,
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
                    "approval": {"required": approval_required, "roles": ["architect"] if approval_required else []},
                }
            ]
        },
    )
    monkeypatch.setattr(gate, "validate_project", lambda *args, **kwargs: [])
    monkeypatch.setattr(gate, "governed_documents", lambda root, policy_path: [])


def _evidence(change: str, *, verifier: str = TRUSTED_VERIFIER, valid_until: str | None = "2026-08-31") -> dict[str, object]:
    return {
        "schema_version": 1,
        "evidence_id": "EVD-001",
        "rule_id": "DOC-EVT-ARCH",
        "requirement": "source reference",
        "subject": {
            "change_digest": change,
            "repository": REPOSITORY,
            "pull_request": PR_NUMBER,
            "head_sha": HEAD_SHA,
        },
        "source": {"ref": "github://cyberDJs/Goverdocs/pull/4/checks/1"},
        "producer": {"id": "github-actions", "type": "system"},
        "verification": {
            "status": "verified",
            "verifier_id": verifier,
            "method": "github-api-adapter",
            "verified_at": "2026-08-17T01:25:00+02:00",
            "valid_until": valid_until,
        },
    }


def _approval(change: str, *, verifier: str = TRUSTED_VERIFIER, head_sha: str = HEAD_SHA) -> dict[str, object]:
    return {
        "schema_version": 1,
        "approval_id": "APR-001",
        "rule_id": "DOC-EVT-ARCH",
        "approval_type": "architecture-change",
        "decision": "approved",
        "actor": {"provider": "github", "id": "reviewer", "role": "architect"},
        "subject": {
            "repository": REPOSITORY,
            "pull_request": PR_NUMBER,
            "head_sha": head_sha,
            "change_digest": change,
        },
        "approved_at": "2026-08-17T01:25:00+02:00",
        "source": {"ref": "github://cyberDJs/Goverdocs/pull/4/reviews/123", "external_id": 123},
        "verification": {
            "status": "verified",
            "verifier_id": verifier,
            "method": "github-api-adapter",
            "verified_at": "2026-08-17T01:25:10+02:00",
            "valid_until": "2026-08-31",
        },
    }


def test_verified_evidence_and_approval_clear_governance_gaps(monkeypatch, tmp_path: Path) -> None:
    paths = _policy_files(tmp_path)
    _configure_rule(monkeypatch, approval_required=True)
    changed_files = ["src/goverdocs/gate.py"]
    diff_text = "+trusted change\n"
    digest = change_digest(changed_files, diff_text)
    evidence = _evidence(digest)
    approval = _approval(digest)

    assert validate_record(evidence, "evidence-item.schema.json") == []
    assert validate_record(approval, "approval.schema.json") == []

    report = gate.evaluate_gate(
        root=tmp_path,
        changed_files=changed_files,
        diff_text=diff_text,
        as_of=date(2026, 8, 17),
        repository=REPOSITORY,
        pull_request=PR_NUMBER,
        head_sha=HEAD_SHA,
        evidence_items=[evidence],
        approvals=[approval],
        trusted_verifiers={TRUSTED_VERIFIER},
        **paths,
    )

    assert report["status"] == "PASS"
    assert report["evidence_gaps"] == []
    assert report["evidence_inputs"][0]["status"] == "VERIFIED"
    assert report["approval_inputs"][0]["status"] == "VERIFIED"


def test_untrusted_approval_cannot_satisfy_blocking_requirement(monkeypatch, tmp_path: Path) -> None:
    paths = _policy_files(tmp_path)
    _configure_rule(monkeypatch, approval_required=True)
    changed_files = ["src/goverdocs/gate.py"]
    diff_text = "+trusted change\n"
    digest = change_digest(changed_files, diff_text)

    report = gate.evaluate_gate(
        root=tmp_path,
        changed_files=changed_files,
        diff_text=diff_text,
        as_of=date(2026, 8, 17),
        repository=REPOSITORY,
        pull_request=PR_NUMBER,
        head_sha=HEAD_SHA,
        evidence_items=[_evidence(digest)],
        approvals=[_approval(digest, verifier="untrusted-adapter")],
        trusted_verifiers={TRUSTED_VERIFIER},
        **paths,
    )

    assert report["status"] == "BLOCKED"
    assert report["approval_inputs"][0]["status"] == "UNTRUSTED"
    assert any(item["code"] == "APPROVAL_UNVERIFIED" and item["blocking"] for item in report["evidence_gaps"])


def test_approval_for_different_head_is_rejected(monkeypatch, tmp_path: Path) -> None:
    paths = _policy_files(tmp_path)
    _configure_rule(monkeypatch, approval_required=True)
    changed_files = ["src/goverdocs/gate.py"]
    diff_text = "+trusted change\n"
    digest = change_digest(changed_files, diff_text)

    report = gate.evaluate_gate(
        root=tmp_path,
        changed_files=changed_files,
        diff_text=diff_text,
        as_of=date(2026, 8, 17),
        repository=REPOSITORY,
        pull_request=PR_NUMBER,
        head_sha=HEAD_SHA,
        evidence_items=[_evidence(digest)],
        approvals=[_approval(digest, head_sha="b" * 40)],
        trusted_verifiers={TRUSTED_VERIFIER},
        **paths,
    )

    assert report["status"] == "BLOCKED"
    assert report["approval_inputs"][0]["status"] == "SUBJECT_MISMATCH"
    assert any(item["code"] == "APPROVAL_UNVERIFIED" for item in report["evidence_gaps"])


def test_stale_evidence_remains_a_warning(monkeypatch, tmp_path: Path) -> None:
    paths = _policy_files(tmp_path)
    _configure_rule(monkeypatch, approval_required=False)
    changed_files = ["src/goverdocs/gate.py"]
    diff_text = "+trusted change\n"
    digest = change_digest(changed_files, diff_text)

    report = gate.evaluate_gate(
        root=tmp_path,
        changed_files=changed_files,
        diff_text=diff_text,
        as_of=date(2026, 8, 17),
        repository=REPOSITORY,
        pull_request=PR_NUMBER,
        head_sha=HEAD_SHA,
        evidence_items=[_evidence(digest, valid_until="2026-08-16")],
        trusted_verifiers={TRUSTED_VERIFIER},
        **paths,
    )

    assert report["status"] == "WARN"
    assert report["evidence_inputs"][0]["status"] == "STALE"
    assert any(item["code"] == "EVIDENCE_UNVERIFIED" and not item["blocking"] for item in report["evidence_gaps"])
