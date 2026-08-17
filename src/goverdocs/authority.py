from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml


class AuthorityPolicyError(ValueError):
    pass


def _string_list(value: object, *, field: str, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list):
        raise AuthorityPolicyError(f"{field} must be a list")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise AuthorityPolicyError(f"{field} must contain non-empty strings")
        items.append(item.strip())
    if not allow_empty and not items:
        raise AuthorityPolicyError(f"{field} must not be empty")
    if len(items) != len(set(items)):
        raise AuthorityPolicyError(f"{field} must not contain duplicates")
    return sorted(items)


def load_authority_policy(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise AuthorityPolicyError(f"authority policy does not exist: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise AuthorityPolicyError("authority policy root must be a mapping")
    if raw.get("version") != 1:
        raise AuthorityPolicyError("authority policy version must be 1")

    raw_roles = raw.get("roles")
    if not isinstance(raw_roles, dict) or not raw_roles:
        raise AuthorityPolicyError("authority policy roles must be a non-empty mapping")

    roles: dict[str, dict[str, list[str]]] = {}
    for raw_role, raw_config in raw_roles.items():
        if not isinstance(raw_role, str) or not raw_role.strip():
            raise AuthorityPolicyError("authority role names must be non-empty strings")
        role = raw_role.strip()
        if not isinstance(raw_config, dict):
            raise AuthorityPolicyError(f"roles.{role} must be a mapping")
        roles[role] = {
            "capabilities": _string_list(
                raw_config.get("capabilities"),
                field=f"roles.{role}.capabilities",
            )
        }

    raw_profiles = raw.get("profiles")
    if not isinstance(raw_profiles, dict):
        raise AuthorityPolicyError("authority policy profiles must be a mapping")
    raw_critical = raw_profiles.get("critical")
    if not isinstance(raw_critical, dict):
        raise AuthorityPolicyError("profiles.critical must be a mapping")

    min_actors = raw_critical.get("min_distinct_actors")
    min_roles = raw_critical.get("min_distinct_roles")
    forbid_author = raw_critical.get("forbid_author_approval")
    if not isinstance(min_actors, int) or isinstance(min_actors, bool) or min_actors < 2:
        raise AuthorityPolicyError("profiles.critical.min_distinct_actors must be an integer >= 2")
    if not isinstance(min_roles, int) or isinstance(min_roles, bool) or min_roles < 2:
        raise AuthorityPolicyError("profiles.critical.min_distinct_roles must be an integer >= 2")
    if not isinstance(forbid_author, bool):
        raise AuthorityPolicyError("profiles.critical.forbid_author_approval must be boolean")

    required_capabilities = _string_list(
        raw_critical.get("required_capabilities"),
        field="profiles.critical.required_capabilities",
    )
    granted = {
        capability
        for role_config in roles.values()
        for capability in role_config["capabilities"]
    }
    missing = sorted(set(required_capabilities) - granted)
    if missing:
        raise AuthorityPolicyError(
            "critical required capabilities are not granted by any role: "
            + ", ".join(missing)
        )
    candidate_roles = {
        role
        for role, role_config in roles.items()
        if set(role_config["capabilities"]) & set(required_capabilities)
    }
    if len(candidate_roles) < min_roles:
        raise AuthorityPolicyError(
            "critical profile requires more distinct authority roles than the policy can provide"
        )
    if min_actors < min_roles:
        raise AuthorityPolicyError(
            "critical min_distinct_actors must be >= min_distinct_roles"
        )

    return {
        "version": 1,
        "roles": dict(sorted(roles.items())),
        "profiles": {
            "critical": {
                "min_distinct_actors": min_actors,
                "min_distinct_roles": min_roles,
                "forbid_author_approval": forbid_author,
                "required_capabilities": required_capabilities,
            }
        },
    }


def _blocking_gap(*, code: str, subject: str, message: str) -> dict[str, Any]:
    return {
        "code": code,
        "severity": "error",
        "blocking": True,
        "subject": subject,
        "message": message,
    }


def _sort_gaps(gaps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        gaps,
        key=lambda item: (
            not bool(item["blocking"]),
            str(item["severity"]),
            str(item["code"]),
            str(item["subject"]),
            str(item["message"]),
        ),
    )


def _recompute_status(report: dict[str, Any]) -> None:
    raw_gaps = report.get("evidence_gaps")
    if not isinstance(raw_gaps, list):
        raise AuthorityPolicyError("GateReport evidence_gaps must be a list")
    gaps = [item for item in raw_gaps if isinstance(item, dict)]
    if any(bool(item.get("blocking")) for item in gaps):
        report["status"] = "BLOCKED"
        report["rationale"] = ["one or more blocking governance conditions are unresolved"]
    elif gaps:
        report["status"] = "WARN"
        report["rationale"] = ["non-blocking evidence, freshness or drift gaps require review"]
    else:
        report["status"] = "PASS"
        report["rationale"] = ["all detected obligations are satisfied for the declared evaluation scope"]


def apply_authority_policy(
    report: dict[str, Any],
    *,
    change_author: str,
    policy: dict[str, Any],
) -> dict[str, Any]:
    """Apply R11 authority constraints to already-assessed approval records.

    R10 remains authoritative for record validity, freshness, verifier trust,
    exact PR/head/change binding, and revocation. R11 only consumes approval
    inputs whose Gate assessment status is VERIFIED.
    """
    if not isinstance(change_author, str) or not change_author.strip():
        raise AuthorityPolicyError("change_author must be a non-empty GitHub login")

    result = copy.deepcopy(report)
    raw_obligations = result.get("obligations")
    raw_approvals = result.get("approval_inputs")
    raw_gaps = result.get("evidence_gaps")
    if not isinstance(raw_obligations, list):
        raise AuthorityPolicyError("GateReport obligations must be a list")
    if not isinstance(raw_approvals, list):
        raise AuthorityPolicyError("GateReport approval_inputs must be a list")
    if not isinstance(raw_gaps, list):
        raise AuthorityPolicyError("GateReport evidence_gaps must be a list")

    roles = policy.get("roles")
    profiles = policy.get("profiles")
    if not isinstance(roles, dict) or not isinstance(profiles, dict):
        raise AuthorityPolicyError("normalized authority policy is invalid")
    critical = profiles.get("critical")
    if not isinstance(critical, dict):
        raise AuthorityPolicyError("normalized critical authority profile is missing")

    required_capabilities = set(
        _string_list(
            critical.get("required_capabilities"),
            field="profiles.critical.required_capabilities",
        )
    )
    min_actors = critical.get("min_distinct_actors")
    min_roles = critical.get("min_distinct_roles")
    forbid_author = critical.get("forbid_author_approval")
    if not isinstance(min_actors, int) or isinstance(min_actors, bool):
        raise AuthorityPolicyError("normalized min_distinct_actors is invalid")
    if not isinstance(min_roles, int) or isinstance(min_roles, bool):
        raise AuthorityPolicyError("normalized min_distinct_roles is invalid")
    if not isinstance(forbid_author, bool):
        raise AuthorityPolicyError("normalized forbid_author_approval is invalid")

    authority_gaps: list[dict[str, Any]] = []
    for raw_obligation in raw_obligations:
        if not isinstance(raw_obligation, dict):
            continue
        if not bool(raw_obligation.get("approval_required")):
            continue
        if str(raw_obligation.get("severity") or "").lower() != "critical":
            continue

        rule_id = str(raw_obligation.get("rule_id") or "UNKNOWN")
        candidates = [
            item
            for item in raw_approvals
            if isinstance(item, dict)
            and item.get("status") == "VERIFIED"
            and str(item.get("rule_id") or "") == rule_id
        ]

        actor_roles: dict[str, set[str]] = {}
        for item in candidates:
            actor_id = str(item.get("actor_id") or "")
            role = str(item.get("actor_role") or "")
            if actor_id and role:
                actor_roles.setdefault(actor_id, set()).add(role)

        aliased = sorted(
            actor_id
            for actor_id, bound_roles in actor_roles.items()
            if len(bound_roles) > 1
        )
        if aliased:
            authority_gaps.append(
                _blocking_gap(
                    code="AUTHORITY_ROLE_ALIAS_CONFLICT",
                    subject=rule_id,
                    message=(
                        "one authority actor is represented under multiple roles for the "
                        f"same critical obligation: {', '.join(aliased)}"
                    ),
                )
            )

        eligible: dict[str, str] = {}
        self_actor_id = f"github:{change_author}"
        for actor_id, bound_roles in sorted(actor_roles.items()):
            if len(bound_roles) != 1:
                continue
            role = next(iter(bound_roles))
            if role not in roles:
                continue
            if forbid_author and actor_id == self_actor_id:
                continue
            eligible[actor_id] = role

        if len(eligible) < min_actors:
            excluded_self = (
                forbid_author
                and self_actor_id in actor_roles
                and len(actor_roles[self_actor_id]) == 1
            )
            suffix = "; PR-author approval is excluded" if excluded_self else ""
            authority_gaps.append(
                _blocking_gap(
                    code="AUTHORITY_QUORUM_REQUIRED",
                    subject=rule_id,
                    message=(
                        f"critical change requires {min_actors} distinct authorized non-author "
                        f"actors; observed {len(eligible)}{suffix}"
                    ),
                )
            )

        eligible_roles = set(eligible.values())
        if len(eligible_roles) < min_roles:
            authority_gaps.append(
                _blocking_gap(
                    code="AUTHORITY_SEPARATION_OF_DUTIES",
                    subject=rule_id,
                    message=(
                        f"critical change requires {min_roles} distinct authority roles; "
                        f"observed {len(eligible_roles)}"
                    ),
                )
            )

        observed_capabilities: set[str] = set()
        for role in eligible_roles:
            raw_role = roles.get(role)
            if not isinstance(raw_role, dict):
                continue
            raw_capabilities = raw_role.get("capabilities")
            if isinstance(raw_capabilities, list):
                observed_capabilities.update(
                    item for item in raw_capabilities if isinstance(item, str)
                )

        for capability in sorted(required_capabilities - observed_capabilities):
            authority_gaps.append(
                _blocking_gap(
                    code="AUTHORITY_CAPABILITY_REQUIRED",
                    subject=rule_id,
                    message=f"critical authority capability is missing: {capability}",
                )
            )

    gaps = [item for item in raw_gaps if isinstance(item, dict)]
    result["evidence_gaps"] = _sort_gaps([*gaps, *authority_gaps])
    _recompute_status(result)
    return result
