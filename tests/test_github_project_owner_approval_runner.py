from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from goverdocs.config import load_config
from goverdocs.github_runner import run_github_pr_governance

HEAD = "a" * 40
BASE = "b" * 40
MARKER = f"GOVERDOCS-APPROVAL-V1 role=project-owner pr=11 head={HEAD} decision=approved"


def _pull() -> dict[str, Any]:
    return {
        "state": "open",
        "draft": False,
        "merged": False,
        "changed_files": 1,
        "head": {"sha": HEAD},
        "base": {"sha": BASE},
        "user": {"id": 10, "login": "owner"},
    }


def _file() -> dict[str, Any]:
    return {
        "sha": "c" * 40,
        "filename": "docs/architecture/ARCH-OWNER-BRIDGE.md",
        "status": "added",
        "additions": 2,
        "deletions": 0,
        "changes": 2,
        "patch": "@@ -0,0 +1,2 @@\n+# Architecture\nproject-owner approval bridge",
    }


class FakeReader:
    def get_json(self, path: str, params: dict[str, str | int] | None = None) -> object:
        if path == "/repos/cyberDJs/Goverdocs/pulls/11":
            return _pull()
        if path == "/repos/cyberDJs/Goverdocs/pulls/11/files":
            assert params is not None
            return [_file()] if int(params["page"]) == 1 else []
        if path == "/repos/cyberDJs/Goverdocs/pulls/11/reviews":
            return [
                {
                    "id": 31,
                    "user": {"id": 11, "login": "owner"},
                    "state": "COMMENTED",
                    "commit_id": HEAD,
                    "submitted_at": "2026-08-17T03:05:58Z",
                    "body": MARKER,
                    "author_association": "OWNER",
                    "html_url": "https://github.com/cyberDJs/Goverdocs/pull/11#pullrequestreview-31",
                }
            ]
        if path == f"/repos/cyberDJs/Goverdocs/commits/{HEAD}/check-runs":
            return {"total_count": 0, "check_runs": []}
        raise AssertionError(path)


def _config():
    return load_config(Path.cwd())


def test_explicit_trust_switch_allows_exact_project_owner_marker() -> None:
    result = run_github_pr_governance(
        FakeReader(),
        config=_config(),
        repository="cyberDJs/Goverdocs",
        pull_request=11,
        as_of=date(2026, 8, 17),
        role_bindings={"owner": "project-owner"},
        trust_github_verifier=True,
        trust_project_owner_comment_approval=True,
    )

    assert result["gate_report"]["status"] != "BLOCKED"
    assert "github-project-owner-comment-approval-v1" in result["run_receipt"]["trusted_verifiers"]
    assert any(
        approval_id.startswith("github-project-owner-comment-31-")
        for approval_id in result["run_receipt"]["generated_approval_ids"]
    )


def test_marker_is_not_trusted_without_explicit_bridge_switch() -> None:
    result = run_github_pr_governance(
        FakeReader(),
        config=_config(),
        repository="cyberDJs/Goverdocs",
        pull_request=11,
        as_of=date(2026, 8, 17),
        role_bindings={"owner": "project-owner"},
        trust_github_verifier=True,
        trust_project_owner_comment_approval=False,
    )

    assert result["gate_report"]["status"] == "BLOCKED"
    assert "github-project-owner-comment-approval-v1" not in result["run_receipt"]["trusted_verifiers"]
    assert not any(
        approval_id.startswith("github-project-owner-comment-")
        for approval_id in result["run_receipt"]["generated_approval_ids"]
    )
