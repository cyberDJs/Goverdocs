from __future__ import annotations

from goverdocs.evidence import validate_record
from goverdocs.github_project_owner_approval import (
    VERIFIER_ID,
    project_owner_comment_approval_records,
)

HEAD = "a" * 40
CHANGE = "c" * 64


def _observation(*, body: str, commit_id: str = HEAD, state: str = "COMMENTED") -> dict[str, object]:
    return {
        "repository": "nulleimy/Goverdocs",
        "pull_request": 15,
        "head_sha": HEAD,
        "reviews": [
            {
                "id": 99,
                "actor": {"id": 1, "login": "owner"},
                "state": state,
                "commit_id": commit_id,
                "submitted_at": "2026-08-17T03:05:58Z",
                "body": body,
                "author_association": "OWNER",
                "html_url": "https://github.com/nulleimy/Goverdocs/pull/15#pullrequestreview-99",
            }
        ],
    }


def _records(observation: dict[str, object], bindings: dict[str, str]) -> list[dict[str, object]]:
    return project_owner_comment_approval_records(
        observation,
        rule_id="DOC-EVT-011",
        approval_type="architecture_change",
        change_digest=CHANGE,
        role_bindings=bindings,
        verified_at="2026-08-17T03:06:00Z",
    )


def test_strict_exact_head_project_owner_marker_becomes_valid_approval() -> None:
    marker = f"GOVERDOCS-APPROVAL-V1 role=project-owner pr=15 head={HEAD} decision=approved"
    records = _records(_observation(body=marker), {"owner": "project-owner"})

    assert [record["approval_id"] for record in records] == ["github-project-owner-comment-99"]
    assert records[0]["verification"]["verifier_id"] == VERIFIER_ID
    assert records[0]["actor"]["role"] == "project-owner"
    assert validate_record(records[0], "approval.schema.json") == []


def test_normal_comment_never_becomes_approval() -> None:
    assert _records(_observation(body="LGTM"), {"owner": "project-owner"}) == []


def test_author_association_never_substitutes_for_role_binding() -> None:
    marker = f"GOVERDOCS-APPROVAL-V1 role=project-owner pr=15 head={HEAD} decision=approved"
    assert _records(_observation(body=marker), {}) == []


def test_wrong_role_wrong_pr_or_stale_head_fail_closed() -> None:
    valid = f"GOVERDOCS-APPROVAL-V1 role=project-owner pr=15 head={HEAD} decision=approved"
    wrong_pr = f"GOVERDOCS-APPROVAL-V1 role=project-owner pr=16 head={HEAD} decision=approved"
    stale = "d" * 40
    wrong_head = f"GOVERDOCS-APPROVAL-V1 role=project-owner pr=15 head={stale} decision=approved"

    assert _records(_observation(body=valid), {"owner": "security-owner"}) == []
    assert _records(_observation(body=wrong_pr), {"owner": "project-owner"}) == []
    assert _records(_observation(body=wrong_head), {"owner": "project-owner"}) == []
    assert _records(_observation(body=valid, commit_id=stale), {"owner": "project-owner"}) == []


def test_marker_must_be_the_entire_comment_body() -> None:
    marker = f"GOVERDOCS-APPROVAL-V1 role=project-owner pr=15 head={HEAD} decision=approved"
    assert _records(_observation(body=f"approved\n{marker}"), {"owner": "project-owner"}) == []
