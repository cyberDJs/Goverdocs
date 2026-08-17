from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .github_source import GitHubReader, GitHubReadError

GOVERNANCE_CHECK_CONTEXT = "GOVERDOCS Governance Gate"
GITHUB_ACTIONS_APP_ID = 15368


@dataclass(frozen=True)
class RequiredStatusCheck:
    context: str
    integration_id: int | None


@dataclass(frozen=True)
class EnforcementObservation:
    repository: str
    branch: str
    rule_present: bool
    strict: bool
    checks: tuple[RequiredStatusCheck, ...]
    matching_ruleset_ids: tuple[int, ...]

    def is_enforced(
        self,
        *,
        required_context: str = GOVERNANCE_CHECK_CONTEXT,
        required_integration_id: int | None = GITHUB_ACTIONS_APP_ID,
    ) -> bool:
        if not self.rule_present or not self.strict:
            return False
        for check in self.checks:
            if check.context != required_context:
                continue
            if required_integration_id is None or check.integration_id == required_integration_id:
                return True
        return False

    def as_dict(
        self,
        *,
        required_context: str = GOVERNANCE_CHECK_CONTEXT,
        required_integration_id: int | None = GITHUB_ACTIONS_APP_ID,
    ) -> dict[str, object]:
        return {
            "schema_version": 1,
            "repository": self.repository,
            "branch": self.branch,
            "rule_present": self.rule_present,
            "strict": self.strict,
            "checks": [
                {"context": check.context, "integration_id": check.integration_id}
                for check in self.checks
            ],
            "matching_ruleset_ids": list(self.matching_ruleset_ids),
            "required_context": required_context,
            "required_integration_id": required_integration_id,
            "status": "PASS"
            if self.is_enforced(
                required_context=required_context,
                required_integration_id=required_integration_id,
            )
            else "BLOCKED",
        }


def _as_dict(value: object, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GitHubReadError(f"{context} must be a JSON object")
    return value


def _as_list(value: object, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise GitHubReadError(f"{context} must be a JSON array")
    return value


def _parse_check(value: object, context: str) -> RequiredStatusCheck:
    raw = _as_dict(value, context)
    name = raw.get("context")
    if not isinstance(name, str) or not name:
        raise GitHubReadError(f"{context}.context must be a non-empty string")
    integration = raw.get("integration_id")
    if integration is not None and not isinstance(integration, int):
        raise GitHubReadError(f"{context}.integration_id must be an integer or null")
    return RequiredStatusCheck(context=name, integration_id=integration)


def collect_effective_enforcement(
    reader: GitHubReader,
    *,
    repository: str,
    branch: str = "main",
) -> EnforcementObservation:
    if repository.count("/") != 1 or repository.startswith("/") or repository.endswith("/"):
        raise ValueError("repository must use owner/name form")
    if not branch or "/" in branch:
        raise ValueError("branch must be a simple branch name")

    path = f"/repos/{repository}/rules/branches/{branch}"
    raw_rules = _as_list(reader.get_json(path), path)

    checks: list[RequiredStatusCheck] = []
    matching_ruleset_ids: set[int] = set()
    strict = False
    rule_present = False

    for index, value in enumerate(raw_rules):
        rule = _as_dict(value, f"{path}[{index}]")
        if rule.get("type") != "required_status_checks":
            continue
        rule_present = True
        parameters = _as_dict(rule.get("parameters"), f"{path}[{index}].parameters")
        strict = strict or parameters.get("strict_required_status_checks_policy") is True
        raw_checks = _as_list(
            parameters.get("required_status_checks"),
            f"{path}[{index}].parameters.required_status_checks",
        )
        checks.extend(
            _parse_check(item, f"{path}[{index}].parameters.required_status_checks[{check_index}]")
            for check_index, item in enumerate(raw_checks)
        )
        ruleset_id = rule.get("ruleset_id")
        if isinstance(ruleset_id, int):
            matching_ruleset_ids.add(ruleset_id)

    unique_checks = sorted(
        set(checks),
        key=lambda item: (item.context, item.integration_id if item.integration_id is not None else -1),
    )
    return EnforcementObservation(
        repository=repository,
        branch=branch,
        rule_present=rule_present,
        strict=strict,
        checks=tuple(unique_checks),
        matching_ruleset_ids=tuple(sorted(matching_ruleset_ids)),
    )
