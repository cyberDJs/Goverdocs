from __future__ import annotations

from typing import Any

import pytest

from goverdocs.github_enforcement import (
    GITHUB_ACTIONS_APP_ID,
    GOVERNANCE_CHECK_CONTEXT,
    collect_effective_enforcement,
)


class FakeReader:
    def __init__(self, payload: object) -> None:
        self.payload = payload
        self.requests: list[tuple[str, dict[str, str | int] | None]] = []

    def get_json(self, path: str, params: dict[str, str | int] | None = None) -> object:
        self.requests.append((path, params))
        return self.payload


def _rule(
    *,
    strict: bool,
    context: str = GOVERNANCE_CHECK_CONTEXT,
    integration_id: int | None = GITHUB_ACTIONS_APP_ID,
    ruleset_id: int = 42,
) -> dict[str, Any]:
    return {
        "type": "required_status_checks",
        "ruleset_source_type": "Repository",
        "ruleset_source": "nulleimy/Goverdocs",
        "ruleset_id": ruleset_id,
        "parameters": {
            "do_not_enforce_on_create": False,
            "required_status_checks": [
                {
                    "context": context,
                    "integration_id": integration_id,
                }
            ],
            "strict_required_status_checks_policy": strict,
        },
    }


def test_no_effective_rules_is_blocked() -> None:
    reader = FakeReader([])

    observation = collect_effective_enforcement(reader, repository="nulleimy/Goverdocs")

    assert observation.rule_present is False
    assert observation.strict is False
    assert observation.is_enforced() is False
    assert observation.as_dict()["status"] == "BLOCKED"
    assert reader.requests == [("/repos/nulleimy/Goverdocs/rules/branches/main", None)]


def test_strict_governance_check_bound_to_github_actions_passes() -> None:
    reader = FakeReader([_rule(strict=True)])

    observation = collect_effective_enforcement(reader, repository="nulleimy/Goverdocs")

    assert observation.rule_present is True
    assert observation.strict is True
    assert observation.matching_ruleset_ids == (42,)
    assert observation.is_enforced() is True
    assert observation.as_dict()["status"] == "PASS"


def test_loose_required_check_fails_closed() -> None:
    reader = FakeReader([_rule(strict=False)])

    observation = collect_effective_enforcement(reader, repository="nulleimy/Goverdocs")

    assert observation.is_enforced() is False
    assert observation.as_dict()["status"] == "BLOCKED"


def test_wrong_integration_fails_closed_but_any_source_can_be_explicitly_allowed() -> None:
    reader = FakeReader([_rule(strict=True, integration_id=None)])

    observation = collect_effective_enforcement(reader, repository="nulleimy/Goverdocs")

    assert observation.is_enforced() is False
    assert observation.is_enforced(required_integration_id=None) is True


def test_unrelated_required_check_does_not_satisfy_governance_requirement() -> None:
    reader = FakeReader([_rule(strict=True, context="quality")])

    observation = collect_effective_enforcement(reader, repository="nulleimy/Goverdocs")

    assert observation.is_enforced() is False


@pytest.mark.parametrize("repository", ["", "owner", "/repo", "owner/", "owner/repo/extra"])
def test_repository_must_use_owner_name_form(repository: str) -> None:
    with pytest.raises(ValueError, match="owner/name"):
        collect_effective_enforcement(FakeReader([]), repository=repository)


@pytest.mark.parametrize("branch", ["", "feature/test"])
def test_branch_must_be_simple_name(branch: str) -> None:
    with pytest.raises(ValueError, match="simple branch name"):
        collect_effective_enforcement(FakeReader([]), repository="nulleimy/Goverdocs", branch=branch)
