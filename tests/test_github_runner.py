from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

from goverdocs.config import load_config
from goverdocs.github_runner import GitHubGovernanceRunError, run_github_pr_governance

HEAD = "a" * 40
BASE = "b" * 40


def _pull(*, base: str = BASE) -> dict[str, Any]:
    return {
        "state": "open",
        "draft": False,
        "merged": False,
        "changed_files": 1,
        "head": {"sha": HEAD},
        "base": {"sha": base},
        "user": {"id": 10, "login": "author"},
    }


def _file() -> dict[str, Any]:
    return {
        "sha": "c" * 40,
        "filename": "docs/architecture/ARCH-RUNNER-PROBE.md",
        "status": "added",
        "additions": 2,
        "deletions": 0,
        "changes": 2,
        "patch": "@@ -0,0 +1,2 @@\n+# Architecture\n+composition boundary",
    }


class FakeReader:
    def __init__(self, *, approved: bool = True, r3_base: str = BASE) -> None:
        self.approved = approved
        self.r3_base = r3_base
        self.pull_reads = 0

    def get_json(self, path: str, params: dict[str, str | int] | None = None) -> object:
        if path == "/repos/cyberDJs/Goverdocs/pulls/11":
            self.pull_reads += 1
            base = BASE if self.pull_reads <= 2 else self.r3_base
            return _pull(base=base)
        if path == "/repos/cyberDJs/Goverdocs/pulls/11/files":
            assert params is not None
            return [_file()] if int(params["page"]) == 1 else []
        if path == "/repos/cyberDJs/Goverdocs/pulls/11/reviews":
            if not self.approved:
                return []
            return [
                {
                    "id": 21,
                    "user": {"id": 11, "login": "owner"},
                    "state": "APPROVED",
                    "commit_id": HEAD,
                    "submitted_at": "2026-08-17T01:00:00Z",
                    "author_association": "OWNER",
                    "html_url": "https://github.com/cyberDJs/Goverdocs/pull/11#pullrequestreview-21",
                }
            ]
        if path == f"/repos/cyberDJs/Goverdocs/commits/{HEAD}/check-runs":
            return {"total_count": 0, "check_runs": []}
        raise AssertionError(path)


class FakeWriter:
    def __init__(self) -> None:
        self.payload: dict[str, Any] | None = None

    def create_check_run(self, repository: str, payload: dict[str, Any]) -> object:
        assert repository == "cyberDJs/Goverdocs"
        self.payload = payload
        return {
            **payload,
            "id": 44,
            "html_url": "https://github.com/cyberDJs/Goverdocs/runs/44",
        }


def _config():
    return load_config(Path.cwd())


def test_explicit_trusted_role_bound_review_satisfies_blocking_approval() -> None:
    result = run_github_pr_governance(
        FakeReader(),
        config=_config(),
        repository="cyberDJs/Goverdocs",
        pull_request=11,
        as_of=date(2026, 8, 17),
        role_bindings={"owner": "project-owner"},
        trust_github_verifier=True,
    )

    assert result["gate_report"]["status"] != "BLOCKED"
    assert result["run_receipt"]["trusted_verifiers"] == ["github-rest-source-v1"]
    assert result["run_receipt"]["generated_approval_ids"]
    assert result["check_run_payload"]["head_sha"] == HEAD


def test_github_author_association_never_substitutes_for_explicit_role_binding() -> None:
    result = run_github_pr_governance(
        FakeReader(),
        config=_config(),
        repository="cyberDJs/Goverdocs",
        pull_request=11,
        as_of=date(2026, 8, 17),
        role_bindings={},
        trust_github_verifier=True,
    )
    assert result["gate_report"]["status"] == "BLOCKED"
    assert result["run_receipt"]["generated_approval_ids"] == []


def test_generated_github_records_remain_untrusted_without_explicit_trust_switch() -> None:
    result = run_github_pr_governance(
        FakeReader(),
        config=_config(),
        repository="cyberDJs/Goverdocs",
        pull_request=11,
        as_of=date(2026, 8, 17),
        role_bindings={"owner": "project-owner"},
        trust_github_verifier=False,
    )
    assert result["gate_report"]["status"] == "BLOCKED"
    assert "github-rest-source-v1" not in result["run_receipt"]["trusted_verifiers"]


def test_r3_and_r5_subject_mismatch_fails_closed() -> None:
    with pytest.raises(GitHubGovernanceRunError, match="disagree on base_sha"):
        run_github_pr_governance(
            FakeReader(r3_base="d" * 40),
            config=_config(),
            repository="cyberDJs/Goverdocs",
            pull_request=11,
            as_of=date(2026, 8, 17),
        )


def test_publish_uses_r4_and_returns_schema_valid_publication_receipt() -> None:
    writer = FakeWriter()
    result = run_github_pr_governance(
        FakeReader(),
        config=_config(),
        repository="cyberDJs/Goverdocs",
        pull_request=11,
        as_of=date(2026, 8, 17),
        role_bindings={"owner": "project-owner"},
        trust_github_verifier=True,
        writer=writer,
        publish=True,
    )

    assert result["run_receipt"]["published"] is True
    assert result["run_receipt"]["publication_receipt"]["check_run_id"] == 44
    assert writer.payload is not None
    assert writer.payload["head_sha"] == HEAD
    assert writer.payload["conclusion"] == result["run_receipt"]["check_conclusion"]
