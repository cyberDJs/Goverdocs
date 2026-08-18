from pathlib import Path

from goverdocs.authority import apply_authority_policy, load_authority_policy
from goverdocs.github_project_owner_approval import (
    project_owner_comment_approval_records,
)
from goverdocs.github_verifier import approved_review_records

HEAD = "a" * 40
CHANGE = "c" * 64


def _observation(*, state: str, body: str = "") -> dict[str, object]:
    return {
        "repository": "nulleimy/OATHDO",
        "pull_request": 62,
        "head_sha": HEAD,
        "reviews": [
            {
                "id": 900,
                "actor": {"id": 268458602, "login": "nulleimy"},
                "state": state,
                "commit_id": HEAD,
                "submitted_at": "2026-08-18T20:00:00Z",
                "body": body,
                "author_association": "OWNER",
                "html_url": "https://github.com/nulleimy/OATHDO/pull/62#pullrequestreview-900",
            }
        ],
    }


def _identities(actor_id: str = "github-user:268458602") -> dict[str, dict[str, str]]:
    return {
        "nulleimy": {
            "actor_id": actor_id,
            "role": "project-owner",
        }
    }


def test_approved_review_uses_immutable_actor_id_when_identity_matches() -> None:
    records = approved_review_records(
        _observation(state="APPROVED"),
        rule_id="DOC-EVT-025",
        approval_type="cicd_change",
        change_digest=CHANGE,
        role_bindings={"nulleimy": "project-owner"},
        identity_bindings=_identities(),
        verified_at="2026-08-18T20:00:01Z",
    )

    assert len(records) == 1
    assert records[0]["actor"]["id"] == "github-user:268458602"


def test_matching_login_with_wrong_numeric_id_does_not_authorize() -> None:
    records = approved_review_records(
        _observation(state="APPROVED"),
        rule_id="DOC-EVT-025",
        approval_type="cicd_change",
        change_digest=CHANGE,
        role_bindings={"nulleimy": "project-owner"},
        identity_bindings=_identities("github-user:999"),
        verified_at="2026-08-18T20:00:01Z",
    )

    assert records == []


def test_project_owner_marker_uses_immutable_actor_id() -> None:
    marker = (
        "GOVERDOCS-APPROVAL-V1 role=project-owner pr=62 "
        f"head={HEAD} decision=approved"
    )
    records = project_owner_comment_approval_records(
        _observation(state="COMMENTED", body=marker),
        rule_id="DOC-EVT-025",
        approval_type="cicd_change",
        change_digest=CHANGE,
        role_bindings={"nulleimy": "project-owner"},
        identity_bindings=_identities(),
        verified_at="2026-08-18T20:00:01Z",
    )

    assert len(records) == 1
    assert records[0]["actor"]["id"] == "github-user:268458602"


def test_critical_self_approval_uses_immutable_pr_author_identity() -> None:
    policy = load_authority_policy(Path("policies/AUTHORITY_POLICY.yaml"))
    report = {
        "schema_version": 2,
        "status": "PASS",
        "obligations": [
            {
                "event": "governance_change",
                "rule_id": "DOC-EVT-009",
                "severity": "critical",
                "priority": 95,
                "required_evidence": [],
                "approval_required": True,
                "approval_roles": ["project-owner"],
                "actions": [],
            }
        ],
        "approval_inputs": [
            {
                "id": "owner",
                "rule_id": "DOC-EVT-009",
                "actor_id": "github-user:268458602",
                "actor_role": "project-owner",
                "status": "VERIFIED",
            },
            {
                "id": "independent",
                "rule_id": "DOC-EVT-009",
                "actor_id": "github-user:264658998",
                "actor_role": "independent-reviewer",
                "status": "VERIFIED",
            },
        ],
        "evidence_gaps": [],
        "rationale": [],
    }

    result = apply_authority_policy(
        report,
        change_author="renamed-login-does-not-matter",
        change_author_actor_id="github-user:268458602",
        policy=policy,
    )

    assert result["status"] == "BLOCKED"
    codes = {
        str(item["code"])
        for item in result["evidence_gaps"]
        if isinstance(item, dict)
    }
    assert "AUTHORITY_QUORUM_REQUIRED" in codes
    assert "AUTHORITY_CAPABILITY_REQUIRED" in codes
