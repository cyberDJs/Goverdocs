from __future__ import annotations

from goverdocs.evidence import validate_record
from goverdocs.github_project_owner_approval import (
    VERIFIER_ID,
    project_owner_comment_approval_records,
)

HEAD = "a" * 40
CHANGE = "c" * 64


def _review(
    *,
    review_id: int,
    body: str,
    submitted_at: str,
    commit_id: str = HEAD,
    state: str = "COMMENTED",
    login: str = "owner",
) -> dict[str, object]:
    return {
        "id": review_id,
        "actor": {"id": 1, "login": login},
        "state": state,
        "commit_id": commit_id,
        "submitted_at": submitted_at,
        "body": body,
        "author_association": "OWNER",
        "html_url": f"https://github.com/nulleimy/Goverdocs/pull/15#pullrequestreview-{review_id}",
    }


def _observation(*, body: str, commit_id: str = HEAD, state: str = "COMMENTED") -> dict[str, object]:
    return _observation_with_reviews(
        [
            _review(
                review_id=99,
                body=body,
                submitted_at="2026-08-17T03:05:58Z",
                commit_id=commit_id,
                state=state,
            )
        ]
    )


def _observation_with_reviews(reviews: list[dict[str, object]]) -> dict[str, object]:
    return {
        "repository": "nulleimy/Goverdocs",
        "pull_request": 15,
        "head_sha": HEAD,
        "reviews": reviews,
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


def test_later_exact_head_revocation_invalidates_earlier_approval() -> None:
    approved = f"GOVERDOCS-APPROVAL-V1 role=project-owner pr=15 head={HEAD} decision=approved"
    revoked = f"GOVERDOCS-APPROVAL-V1 role=project-owner pr=15 head={HEAD} decision=revoked"
    observation = _observation_with_reviews(
        [
            _review(review_id=99, body=approved, submitted_at="2026-08-17T03:05:58Z"),
            _review(review_id=100, body=revoked, submitted_at="2026-08-17T03:06:58Z"),
        ]
    )

    assert _records(observation, {"owner": "project-owner"}) == []


def test_later_exact_head_approval_can_reauthorize_after_revocation() -> None:
    approved = f"GOVERDOCS-APPROVAL-V1 role=project-owner pr=15 head={HEAD} decision=approved"
    revoked = f"GOVERDOCS-APPROVAL-V1 role=project-owner pr=15 head={HEAD} decision=revoked"
    observation = _observation_with_reviews(
        [
            _review(review_id=99, body=approved, submitted_at="2026-08-17T03:05:58Z"),
            _review(review_id=100, body=revoked, submitted_at="2026-08-17T03:06:58Z"),
            _review(review_id=101, body=approved, submitted_at="2026-08-17T03:07:58Z"),
        ]
    )

    records = _records(observation, {"owner": "project-owner"})
    assert [record["approval_id"] for record in records] == ["github-project-owner-comment-101"]


def test_revocation_is_actor_scoped_when_multiple_project_owners_exist() -> None:
    approved = f"GOVERDOCS-APPROVAL-V1 role=project-owner pr=15 head={HEAD} decision=approved"
    revoked = f"GOVERDOCS-APPROVAL-V1 role=project-owner pr=15 head={HEAD} decision=revoked"
    observation = _observation_with_reviews(
        [
            _review(review_id=99, body=approved, submitted_at="2026-08-17T03:05:58Z", login="owner"),
            _review(review_id=100, body=approved, submitted_at="2026-08-17T03:05:59Z", login="backup"),
            _review(review_id=101, body=revoked, submitted_at="2026-08-17T03:06:58Z", login="owner"),
        ]
    )

    records = _records(observation, {"owner": "project-owner", "backup": "project-owner"})
    assert [record["approval_id"] for record in records] == ["github-project-owner-comment-100"]
