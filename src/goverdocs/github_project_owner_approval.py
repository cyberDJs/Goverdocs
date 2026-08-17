from __future__ import annotations

import re
from typing import Any

VERIFIER_ID = "github-project-owner-comment-approval-v1"

_MARKER = re.compile(
    r"^GOVERDOCS-APPROVAL-V1 role=project-owner pr=([1-9][0-9]*) "
    r"head=([0-9a-f]{40}) decision=approved$"
)


def _verification(*, verified_at: str, valid_until: str | None) -> dict[str, Any]:
    return {
        "status": "verified",
        "verifier_id": VERIFIER_ID,
        "method": "authenticated-github-comment-marker-exact-subject-binding",
        "verified_at": verified_at,
        "valid_until": valid_until,
    }


def project_owner_comment_approval_records(
    observation: dict[str, Any],
    *,
    rule_id: str,
    approval_type: str,
    change_digest: str,
    role_bindings: dict[str, str],
    verified_at: str,
    valid_until: str | None = None,
) -> list[dict[str, Any]]:
    """Convert only strict, exact-head project-owner COMMENT reviews into approvals.

    A normal COMMENT review is never sufficient. The review body must consist
    solely of the machine-readable GOVERDOCS-APPROVAL-V1 marker, the actor must
    have an explicit project-owner role binding, and the marker, review commit,
    PR number, and current observation HEAD must all agree exactly.
    """
    repository = str(observation["repository"])
    pull_request = int(observation["pull_request"])
    head_sha = str(observation["head_sha"])
    results: list[dict[str, Any]] = []

    for raw in observation.get("reviews", []):
        if not isinstance(raw, dict):
            continue
        if raw.get("state") != "COMMENTED" or raw.get("commit_id") != head_sha:
            continue
        actor = raw.get("actor")
        if not isinstance(actor, dict):
            continue
        login = str(actor.get("login") or "")
        if role_bindings.get(login) != "project-owner":
            continue

        body = str(raw.get("body") or "").strip()
        match = _MARKER.fullmatch(body)
        if match is None:
            continue
        if int(match.group(1)) != pull_request or match.group(2) != head_sha:
            continue

        review_id = int(raw["id"])
        results.append(
            {
                "schema_version": 1,
                "approval_id": f"github-project-owner-comment-{review_id}",
                "rule_id": rule_id,
                "approval_type": approval_type,
                "decision": "approved",
                "actor": {
                    "provider": "github",
                    "id": f"github:{login}",
                    "role": "project-owner",
                },
                "subject": {
                    "repository": repository,
                    "pull_request": pull_request,
                    "head_sha": head_sha,
                    "change_digest": change_digest,
                },
                "approved_at": str(raw["submitted_at"]),
                "source": {
                    "ref": str(
                        raw.get("html_url")
                        or f"https://api.github.com/repos/{repository}/pulls/{pull_request}/reviews/{review_id}"
                    ),
                    "external_id": review_id,
                },
                "verification": _verification(verified_at=verified_at, valid_until=valid_until),
            }
        )

    return sorted(results, key=lambda item: str(item["approval_id"]))
