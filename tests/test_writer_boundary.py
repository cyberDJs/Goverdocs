import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from goverdocs.writer_boundary import (
    WriteGrantError,
    authorize_operation,
    issue_write_grant,
    validate_write_grant,
)

HEAD = "a" * 40
CHANGE = "b" * 64


def _operation(*, target: str = "docs/architecture/target.md") -> dict[str, object]:
    return {
        "event": "architecture_change",
        "rule_id": "DOC-EVT-001",
        "document_type": "architecture",
        "action": "update",
        "target": target,
        "write_policy": "approval-required",
        "approval_required": True,
        "severity": "high",
        "priority": 90,
    }


def _gate_report(*, status: str = "PASS") -> dict[str, object]:
    return {
        "schema_version": 2,
        "status": status,
        "evaluation_date": "2026-08-19",
        "input": {
            "digest": "c" * 64,
            "change_digest": CHANGE,
            "changed_files": ["src/example.py"],
            "repository": "nulleimy/OATHDO",
            "pull_request": 68,
            "head_sha": HEAD,
        },
        "trust": {"trusted_verifiers": ["github-rest-source-v1"]},
        "policy_digests": {"decision_matrix": "d" * 64},
        "events": [],
        "obligations": [
            {
                "event": "architecture_change",
                "rule_id": "DOC-EVT-001",
                "severity": "high",
                "priority": 90,
                "required_evidence": [],
                "approval_required": True,
                "approval_roles": ["project-owner"],
                "actions": [_operation()],
            }
        ],
        "evidence_inputs": [],
        "approval_inputs": [],
        "validation_issues": [],
        "evidence_gaps": [],
        "rationale": ["all detected obligations are satisfied"],
    }


def test_write_grant_is_deterministic_and_schema_valid() -> None:
    report = _gate_report()

    first = issue_write_grant(report)
    second = issue_write_grant(copy.deepcopy(report))

    assert first == second
    assert first["grant_id"].startswith("write-grant-v1:")
    assert first["subject"] == {
        "repository": "nulleimy/OATHDO",
        "pull_request": 68,
        "head_sha": HEAD,
        "change_digest": CHANGE,
    }

    schema = json.loads(Path("schemas/write-grant.schema.json").read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(first), key=lambda item: list(item.path))
    assert errors == []


def test_blocked_gate_cannot_issue_write_grant() -> None:
    with pytest.raises(WriteGrantError, match="cannot authorize writes"):
        issue_write_grant(_gate_report(status="BLOCKED"))


def test_warn_gate_with_blocking_gap_fails_closed() -> None:
    report = _gate_report(status="WARN")
    report["evidence_gaps"] = [
        {
            "code": "AUTHORITY_QUORUM_REQUIRED",
            "severity": "error",
            "blocking": True,
            "subject": "DOC-EVT-001",
            "message": "quorum missing",
        }
    ]

    with pytest.raises(WriteGrantError, match="blocking governance gap"):
        issue_write_grant(report)


def test_missing_exact_scm_subject_cannot_issue_write_grant() -> None:
    report = _gate_report()
    assert isinstance(report["input"], dict)
    report["input"]["head_sha"] = None

    with pytest.raises(WriteGrantError, match="input.head_sha"):
        issue_write_grant(report)


def test_duplicate_authorized_operation_fails_closed() -> None:
    report = _gate_report()
    obligations = report["obligations"]
    assert isinstance(obligations, list)
    assert isinstance(obligations[0], dict)
    obligations[0]["actions"] = [_operation(), _operation()]

    with pytest.raises(WriteGrantError, match="duplicate authorized operations"):
        issue_write_grant(report)


def test_exact_authorized_operation_is_accepted() -> None:
    report = _gate_report()
    grant = issue_write_grant(report)

    authorize_operation(
        grant,
        report,
        repository="nulleimy/OATHDO",
        pull_request=68,
        head_sha=HEAD,
        change_digest=CHANGE,
        operation=_operation(),
    )


def test_operation_widening_is_rejected() -> None:
    report = _gate_report()
    grant = issue_write_grant(report)

    with pytest.raises(WriteGrantError, match="outside the authorized grant scope"):
        authorize_operation(
            grant,
            report,
            repository="nulleimy/OATHDO",
            pull_request=68,
            head_sha=HEAD,
            change_digest=CHANGE,
            operation=_operation(target="docs/architecture/unapproved.md"),
        )


def test_grant_cannot_be_reused_for_other_head() -> None:
    report = _gate_report()
    grant = issue_write_grant(report)

    with pytest.raises(WriteGrantError, match="subject does not match"):
        authorize_operation(
            grant,
            report,
            repository="nulleimy/OATHDO",
            pull_request=68,
            head_sha="e" * 40,
            change_digest=CHANGE,
            operation=_operation(),
        )


def test_tampered_grant_fails_canonical_derivation_check() -> None:
    report = _gate_report()
    grant = issue_write_grant(report)
    grant["operations"][0]["target"] = "docs/architecture/tampered.md"

    with pytest.raises(WriteGrantError, match="canonical gate-derived grant"):
        validate_write_grant(grant, report)


def test_gate_report_change_invalidates_existing_grant() -> None:
    report = _gate_report()
    grant = issue_write_grant(report)
    changed_report = copy.deepcopy(report)
    assert isinstance(changed_report["policy_digests"], dict)
    changed_report["policy_digests"]["decision_matrix"] = "f" * 64

    with pytest.raises(WriteGrantError, match="canonical gate-derived grant"):
        validate_write_grant(grant, changed_report)
