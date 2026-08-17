from pathlib import Path

from goverdocs.authority import load_authority_policy


def test_canonical_authority_policy_is_valid() -> None:
    policy = load_authority_policy(Path("policies/AUTHORITY_POLICY.yaml"))

    assert policy["version"] == 1
    assert set(policy["roles"]) == {"independent-reviewer", "project-owner"}
    critical = policy["profiles"]["critical"]
    assert critical["min_distinct_actors"] == 2
    assert critical["min_distinct_roles"] == 2
    assert critical["forbid_author_approval"] is True
    assert critical["required_capabilities"] == [
        "approve:critical-independent",
        "approve:critical-owner",
    ]
