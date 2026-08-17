from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from goverdocs.evidence import validate_record
from goverdocs.github_check import (
    DEFAULT_CHECK_NAME,
    GitHubCheckPublicationError,
    GitHubChecksRESTClient,
    build_check_run_payload,
    publish_gate_check,
)
from goverdocs.github_check_cli import main

REPOSITORY = "cyberDJs/Goverdocs"
HEAD = "a" * 40


def _report(status: str = "PASS") -> dict[str, Any]:
    gaps: list[dict[str, Any]]
    rationale: list[str]
    if status == "PASS":
        gaps = []
        rationale = ["all detected obligations are satisfied"]
    elif status == "WARN":
        gaps = [
            {
                "code": "EVIDENCE_MISSING",
                "severity": "warning",
                "blocking": False,
                "subject": "DOC-EVT-011",
                "message": "required evidence is missing",
            }
        ]
        rationale = ["non-blocking evidence gaps require review"]
    else:
        gaps = [
            {
                "code": "APPROVAL_REQUIRED",
                "severity": "error",
                "blocking": True,
                "subject": "DOC-EVT-011",
                "message": "explicit approval is required",
            }
        ]
        rationale = ["one or more blocking governance conditions are unresolved"]

    return {
        "schema_version": 2,
        "status": status,
        "evaluation_date": "2026-08-17",
        "input": {
            "digest": "d" * 64,
            "change_digest": "c" * 64,
            "changed_files": ["src/goverdocs/example.py"],
            "repository": REPOSITORY,
            "pull_request": 8,
            "head_sha": HEAD,
        },
        "trust": {"trusted_verifiers": []},
        "policy_digests": {},
        "events": [],
        "obligations": [],
        "evidence_inputs": [],
        "approval_inputs": [],
        "validation_issues": [],
        "evidence_gaps": gaps,
        "rationale": rationale,
    }


class FakeWriter:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def create_check_run(self, repository: str, payload: dict[str, Any]) -> object:
        self.calls.append((repository, payload))
        return {
            "id": 42,
            "name": payload["name"],
            "head_sha": payload["head_sha"],
            "status": "completed",
            "conclusion": payload["conclusion"],
            "external_id": payload["external_id"],
            "html_url": "https://github.com/cyberDJs/Goverdocs/runs/42",
        }


@pytest.mark.parametrize(
    ("status", "conclusion"),
    [("PASS", "success"), ("WARN", "neutral"), ("BLOCKED", "failure")],
)
def test_gate_status_maps_to_non_escalating_check_conclusion(status: str, conclusion: str) -> None:
    payload = build_check_run_payload(
        _report(status),
        expected_repository=REPOSITORY,
        expected_head_sha=HEAD,
    )
    assert payload["name"] == DEFAULT_CHECK_NAME
    assert payload["head_sha"] == HEAD
    assert payload["status"] == "completed"
    assert payload["conclusion"] == conclusion
    assert str(payload["external_id"]).startswith("goverdocs-gate-v2:")


def test_payload_requires_explicit_exact_subject_binding() -> None:
    with pytest.raises(ValueError, match="repository does not match"):
        build_check_run_payload(
            _report(),
            expected_repository="cyberDJs/Other",
            expected_head_sha=HEAD,
        )
    with pytest.raises(ValueError, match="head_sha does not match"):
        build_check_run_payload(
            _report(),
            expected_repository=REPOSITORY,
            expected_head_sha="b" * 40,
        )


def test_payload_rejects_schema_valid_but_semantically_inconsistent_status() -> None:
    report = _report()
    report["evidence_gaps"] = [
        {
            "code": "EVIDENCE_MISSING",
            "severity": "warning",
            "blocking": False,
            "subject": "DOC-EVT-011",
            "message": "gap",
        }
    ]
    with pytest.raises(ValueError, match="PASS GateReport cannot contain evidence gaps"):
        build_check_run_payload(
            report,
            expected_repository=REPOSITORY,
            expected_head_sha=HEAD,
        )


def test_publish_returns_schema_valid_receipt_bound_to_response() -> None:
    writer = FakeWriter()
    receipt = publish_gate_check(
        writer,
        _report("BLOCKED"),
        expected_repository=REPOSITORY,
        expected_head_sha=HEAD,
    )
    assert writer.calls[0][0] == REPOSITORY
    assert receipt["gate_status"] == "BLOCKED"
    assert receipt["conclusion"] == "failure"
    assert validate_record(receipt, "github-check-publication.schema.json") == []


def test_publish_fails_closed_on_response_subject_mismatch() -> None:
    class WrongHeadWriter:
        def create_check_run(self, repository: str, payload: dict[str, Any]) -> object:
            del repository
            return {
                "id": 42,
                "name": payload["name"],
                "head_sha": "b" * 40,
                "status": "completed",
                "conclusion": payload["conclusion"],
                "external_id": payload["external_id"],
                "html_url": "https://github.com/cyberDJs/Goverdocs/runs/42",
            }

    with pytest.raises(GitHubCheckPublicationError, match="head_sha"):
        publish_gate_check(
            WrongHeadWriter(),
            _report(),
            expected_repository=REPOSITORY,
            expected_head_sha=HEAD,
        )


def test_checks_client_refuses_publish_without_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("R4_TEST_TOKEN", raising=False)
    with pytest.raises(GitHubCheckPublicationError, match="R4_TEST_TOKEN"):
        GitHubChecksRESTClient.from_env("R4_TEST_TOKEN")


def test_cli_is_dry_run_by_default(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    report_path = tmp_path / "gate.json"
    report_path.write_text(json.dumps(_report()), encoding="utf-8")
    result = main(
        [
            "--gate-report",
            str(report_path),
            "--repository",
            REPOSITORY,
            "--head-sha",
            HEAD,
        ]
    )
    assert result == 0
    output = json.loads(capsys.readouterr().out)
    assert output["mode"] == "dry-run"
    assert output["payload"]["conclusion"] == "success"
