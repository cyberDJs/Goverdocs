from pathlib import Path

import pytest

from goverdocs.authority import (
    AuthorityPolicyError,
    apply_authority_policy,
    load_authority_policy,
)


POLICY_TEXT = """\
version: 1
roles:
  project-owner:
    capabilities:
      - approve:standard
      - approve:critical-owner
      - revoke:own
  independent-reviewer:
    capabilities:
      - approve:standard
      - approve:critical-independent
      - revoke:own
profiles:
  critical:
    min_distinct_actors: 2
    min_distinct_roles: 2
    forbid_author_approval: true
    required_capabilities:
      - approve:critical-owner
      - approve:critical-independent
"""


def _policy(tmp_path: Path) -> dict[str, object]:
    path = tmp_path / "authority.yaml"
    path.write_text(POLICY_TEXT, encoding="utf-8")
    return load_authority_policy(path)


def _approval(
    actor: str,
    role: str,
    *,
    rule_id: str = "DOC-EVT-025",
    status: str = "VERIFIED",
) -> dict[str, object]:
    return {
        "id": f"approval-{actor}-{role}",
        "rule_id": rule_id,
        "approval_type": "governance_change",
        "decision": "approved",
        "actor_id": f"github:{actor}",
        "actor_role": role,
        "status": status,
        "reasons": [],
    }


def _report(
    approvals: list[dict[str, object]],
    *,
    severity: str = "critical",
    rule_id: str = "DOC-EVT-025",
) -> dict[str, object]:
    return {
        "schema_version": 2,
        "status": "PASS",
        "obligations": [
            {
                "event": "governance_change",
                "rule_id": rule_id,
                "severity": severity,
                "priority": 100,
                "required_evidence": [],
                "approval_required": True,
                "approval_roles": ["project-owner"],
                "actions": [],
            }
        ],
        "approval_inputs": approvals,
        "evidence_gaps": [],
        "rationale": [
            "all detected obligations are satisfied for the declared evaluation scope"
        ],
    }


def _codes(report: dict[str, object]) -> list[str]:
    gaps = report["evidence_gaps"]
    assert isinstance(gaps, list)
    return sorted(
        str(item["code"])
        for item in gaps
        if isinstance(item, dict)
    )


def test_load_authority_policy_normalizes_roles_and_profile(tmp_path: Path) -> None:
    policy = _policy(tmp_path)

    assert policy["version"] == 1
    assert policy["profiles"]["critical"]["min_distinct_actors"] == 2
    assert policy["profiles"]["critical"]["min_distinct_roles"] == 2
    assert policy["profiles"]["critical"]["forbid_author_approval"] is True


def test_policy_fails_closed_when_required_capability_is_unowned(
    tmp_path: Path,
) -> None:
    path = tmp_path / "authority.yaml"
    path.write_text(
        POLICY_TEXT.replace(
            "      - approve:critical-independent\n",
            "",
            1,
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        AuthorityPolicyError,
        match="not granted by any role",
    ):
        load_authority_policy(path)


def test_critical_change_requires_two_distinct_authorized_actors(
    tmp_path: Path,
) -> None:
    policy = _policy(tmp_path)
    report = _report([
        _approval("owner", "project-owner"),
    ])

    result = apply_authority_policy(
        report,
        change_author="author",
        policy=policy,
    )

    assert result["status"] == "BLOCKED"
    assert "AUTHORITY_QUORUM_REQUIRED" in _codes(result)
    assert "AUTHORITY_SEPARATION_OF_DUTIES" in _codes(result)
    assert "AUTHORITY_CAPABILITY_REQUIRED" in _codes(result)


def test_pr_author_does_not_count_toward_critical_quorum(
    tmp_path: Path,
) -> None:
    policy = _policy(tmp_path)
    report = _report([
        _approval("author", "project-owner"),
        _approval("reviewer", "independent-reviewer"),
    ])

    result = apply_authority_policy(
        report,
        change_author="author",
        policy=policy,
    )

    assert result["status"] == "BLOCKED"
    assert "AUTHORITY_QUORUM_REQUIRED" in _codes(result)
    assert "AUTHORITY_CAPABILITY_REQUIRED" in _codes(result)


def test_same_actor_cannot_satisfy_two_roles(
    tmp_path: Path,
) -> None:
    policy = _policy(tmp_path)
    report = _report([
        _approval("alice", "project-owner"),
        _approval("alice", "independent-reviewer"),
    ])

    result = apply_authority_policy(
        report,
        change_author="author",
        policy=policy,
    )

    assert result["status"] == "BLOCKED"
    assert "AUTHORITY_ROLE_ALIAS_CONFLICT" in _codes(result)
    assert "AUTHORITY_QUORUM_REQUIRED" in _codes(result)


def test_unverified_or_revoked_records_do_not_count(
    tmp_path: Path,
) -> None:
    policy = _policy(tmp_path)
    report = _report([
        _approval("owner", "project-owner", status="REVOKED"),
        _approval(
            "reviewer",
            "independent-reviewer",
            status="UNTRUSTED",
        ),
    ])

    result = apply_authority_policy(
        report,
        change_author="author",
        policy=policy,
    )

    assert result["status"] == "BLOCKED"
    assert "AUTHORITY_QUORUM_REQUIRED" in _codes(result)
    assert _codes(result).count("AUTHORITY_CAPABILITY_REQUIRED") == 2


def test_missing_owner_capability_is_blocking(
    tmp_path: Path,
) -> None:
    policy = _policy(tmp_path)
    report = _report([
        _approval("reviewer-a", "independent-reviewer"),
        _approval("reviewer-b", "independent-reviewer"),
    ])

    result = apply_authority_policy(
        report,
        change_author="author",
        policy=policy,
    )

    assert result["status"] == "BLOCKED"
    assert "AUTHORITY_SEPARATION_OF_DUTIES" in _codes(result)
    assert "AUTHORITY_CAPABILITY_REQUIRED" in _codes(result)


def test_valid_two_actor_two_role_critical_quorum_passes(
    tmp_path: Path,
) -> None:
    policy = _policy(tmp_path)
    report = _report([
        _approval("owner", "project-owner"),
        _approval("reviewer", "independent-reviewer"),
    ])

    result = apply_authority_policy(
        report,
        change_author="author",
        policy=policy,
    )

    assert result["status"] == "PASS"
    assert result["evidence_gaps"] == []


def test_standard_approval_semantics_remain_backward_compatible(
    tmp_path: Path,
) -> None:
    policy = _policy(tmp_path)
    report = _report(
        [_approval("owner", "project-owner")],
        severity="high",
    )

    result = apply_authority_policy(
        report,
        change_author="author",
        policy=policy,
    )

    assert result["status"] == "PASS"
    assert result["evidence_gaps"] == []
