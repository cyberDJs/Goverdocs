from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

from goverdocs.config import load_config
from goverdocs.github_pr_evidence import (
    GitHubPREvidenceContractError,
    collect_pull_evidence_contract,
    parse_pr_evidence_sections,
)
from goverdocs.github_runner import run_github_pr_governance

HEAD = "a" * 40
BASE = "b" * 40

BODY = """## Change rationale

Make PR intent machine-readable for the Gate.

## Affected scope

R6 PR governance composition only.

## Risk

Low.

## Rollback

Revert the R7 commit.

## Governance approvals

Project owner when required.
"""


def _pull(body: str = BODY) -> dict[str, Any]:
    return {
        "state": "open",
        "draft": False,
        "merged": False,
        "changed_files": 1,
        "updated_at": "2026-08-17T02:00:00Z",
        "body": body,
        "head": {"sha": HEAD},
        "base": {"sha": BASE},
        "user": {"id": 10, "login": "author"},
    }


def _file() -> dict[str, Any]:
    return {
        "sha": "c" * 40,
        "filename": "docs/architecture/ARCH-R7-PROBE.md",
        "status": "added",
        "additions": 2,
        "deletions": 0,
        "changes": 2,
        "patch": "@@ -0,0 +1,2 @@\n+# Architecture\n+R7 evidence contract",
    }


class ContractReader:
    def __init__(self, *, body: str = BODY, mutate_body: bool = False) -> None:
        self.body = body
        self.mutate_body = mutate_body
        self.pull_reads = 0

    def get_json(self, path: str, params: dict[str, str | int] | None = None) -> object:
        if path == "/repos/cyberDJs/Goverdocs/pulls/13":
            self.pull_reads += 1
            body = self.body
            if self.mutate_body and self.pull_reads >= 5:
                body += "\nchanged during acquisition"
            return _pull(body)
        if path == "/repos/cyberDJs/Goverdocs/pulls/13/files":
            assert params is not None
            return [_file()] if int(params["page"]) == 1 else []
        if path == "/repos/cyberDJs/Goverdocs/pulls/13/reviews":
            return [
                {
                    "id": 21,
                    "user": {"id": 11, "login": "owner"},
                    "state": "APPROVED",
                    "commit_id": HEAD,
                    "submitted_at": "2026-08-17T01:00:00Z",
                    "author_association": "OWNER",
                    "html_url": "https://github.com/cyberDJs/Goverdocs/pull/13#pullrequestreview-21",
                }
            ]
        if path == f"/repos/cyberDJs/Goverdocs/commits/{HEAD}/check-runs":
            return {"total_count": 0, "check_runs": []}
        raise AssertionError(path)


def test_template_comments_do_not_count_as_declared_evidence() -> None:
    sections = parse_pr_evidence_sections(
        """## Change rationale
<!-- Explain why. -->

## Affected scope
<!-- Explain scope. -->
"""
    )
    assert sections == {}


def test_parser_extracts_declared_contract_sections() -> None:
    sections = parse_pr_evidence_sections(BODY)
    assert sections["change rationale"] == "Make PR intent machine-readable for the Gate."
    assert sections["affected scope"] == "R6 PR governance composition only."
    assert sections["rollback"] == "Revert the R7 commit."


def test_contract_acquisition_fails_closed_when_body_changes_mid_read() -> None:
    reader = ContractReader(mutate_body=True)
    reader.pull_reads = 3
    with pytest.raises(GitHubPREvidenceContractError, match="changed during acquisition"):
        collect_pull_evidence_contract(
            reader,
            repository="cyberDJs/Goverdocs",
            pull_request=13,
            expected_head_sha=HEAD,
            expected_base_sha=BASE,
        )


def test_trusted_pr_contract_satisfies_declaration_evidence() -> None:
    result = run_github_pr_governance(
        ContractReader(),
        config=load_config(Path.cwd()),
        repository="cyberDJs/Goverdocs",
        pull_request=13,
        as_of=date(2026, 8, 17),
        role_bindings={"owner": "project-owner"},
        trust_github_verifier=True,
        trust_pr_evidence_contract=True,
    )

    receipt = result["run_receipt"]
    assert "github-pr-evidence-contract-v1" in receipt["trusted_verifiers"]
    assert receipt["generated_pr_contract_evidence_ids"]
    assert len(receipt["pr_evidence_contract_digest"]) == 64

    declaration_gaps = [
        gap
        for gap in result["gate_report"]["evidence_gaps"]
        if gap["code"] in {"EVIDENCE_MISSING", "EVIDENCE_UNVERIFIED"}
        and ("change rationale" in gap["message"] or "affected scope" in gap["message"])
    ]
    assert declaration_gaps == []

    contract_ids = set(receipt["generated_pr_contract_evidence_ids"])
    assert contract_ids.issubset(set(receipt["generated_evidence_ids"]))

    for item in result["gate_report"]["evidence_inputs"]:
        if item["id"] in contract_ids:
            assert item["status"] == "VERIFIED"


def test_pr_contract_records_are_verified_by_gate_schema_assessment() -> None:
    result = run_github_pr_governance(
        ContractReader(),
        config=load_config(Path.cwd()),
        repository="cyberDJs/Goverdocs",
        pull_request=13,
        as_of=date(2026, 8, 17),
        role_bindings={"owner": "project-owner"},
        trust_github_verifier=True,
        trust_pr_evidence_contract=True,
    )
    contract_ids = set(result["run_receipt"]["generated_pr_contract_evidence_ids"])
    assert contract_ids
    for item in result["gate_report"]["evidence_inputs"]:
        if item["id"] in contract_ids:
            assert item["status"] == "VERIFIED"
            assert item["reasons"]
