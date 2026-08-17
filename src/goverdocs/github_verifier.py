from __future__ import annotations

import hashlib
import json
from typing import Any

VERIFIER_ID = "github-rest-source-v1"


def _digest(value: dict[str, Any]) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _verification(*, verified_at: str, valid_until: str | None) -> dict[str, Any]:
    return {
        "status": "verified",
        "verifier_id": VERIFIER_ID,
        "method": "authenticated-github-rest-read-exact-subject-binding",
        "verified_at": verified_at,
        "valid_until": valid_until,
    }


def source_reference_evidence(
    observation: dict[str, Any],
    *,
    rule_id: str,
    change_digest: str,
    verified_at: str,
    valid_until: str | None = None,
) -> dict[str, Any]:
    repository = str(observation["repository"])
    pull_request = int(observation["pull_request"])
    head_sha = str(observation["head_sha"])
    source_ref = f"https://api.github.com/repos/{repository}/pulls/{pull_request}"
    return {
        "schema_version": 1,
        "evidence_id": f"github-pr-{repository.replace('/', '-')}-{pull_request}-{head_sha[:12]}",
        "rule_id": rule_id,
        "requirement": "source reference",
        "subject": {
            "change_digest": change_digest,
            "repository": repository,
            "pull_request": pull_request,
            "head_sha": head_sha,
        },
        "source": {
            "ref": source_ref,
            "digest": _digest(observation),
        },
        "producer": {
            "id": "github-rest-api",
            "type": "external-service",
        },
        "verification": _verification(verified_at=verified_at, valid_until=valid_until),
    }


def successful_check_evidence(
    observation: dict[str, Any],
    *,
    rule_id: str,
    requirement: str,
    change_digest: str,
    check_name: str,
    verified_at: str,
    valid_until: str | None = None,
) -> list[dict[str, Any]]:
    repository = str(observation["repository"])
    pull_request = int(observation["pull_request"])
    head_sha = str(observation["head_sha"])
    results: list[dict[str, Any]] = []
    for raw in observation.get("check_runs", []):
        if not isinstance(raw, dict):
            continue
        if raw.get("name") != check_name:
            continue
        if raw.get("head_sha") != head_sha:
            continue
        if raw.get("status") != "completed" or raw.get("conclusion") != "success":
            continue
        check_id = int(raw["id"])
        source_ref = str(raw.get("details_url") or f"https://api.github.com/repos/{repository}/check-runs/{check_id}")
        results.append(
            {
                "schema_version": 1,
                "evidence_id": f"github-check-{check_id}",
                "rule_id": rule_id,
                "requirement": requirement,
                "subject": {
                    "change_digest": change_digest,
                    "repository": repository,
                    "pull_request": pull_request,
                    "head_sha": head_sha,
                },
                "source": {"ref": source_ref, "digest": _digest(raw)},
                "producer": {"id": str(raw.get("app_slug") or "github-checks"), "type": "external-service"},
                "verification": _verification(verified_at=verified_at, valid_until=valid_until),
            }
        )
    return sorted(results, key=lambda item: str(item["evidence_id"]))


def approved_review_records(
    observation: dict[str, Any],
    *,
    rule_id: str,
    approval_type: str,
    change_digest: str,
    role_bindings: dict[str, str],
    verified_at: str,
    valid_until: str | None = None,
) -> list[dict[str, Any]]:
    repository = str(observation["repository"])
    pull_request = int(observation["pull_request"])
    head_sha = str(observation["head_sha"])
    results: list[dict[str, Any]] = []
    for raw in observation.get("reviews", []):
        if not isinstance(raw, dict):
            continue
        if raw.get("state") != "APPROVED" or raw.get("commit_id") != head_sha:
            continue
        actor = raw.get("actor")
        if not isinstance(actor, dict):
            continue
        login = str(actor.get("login") or "")
        role = role_bindings.get(login)
        if not role:
            continue
        review_id = int(raw["id"])
        results.append(
            {
                "schema_version": 1,
                "approval_id": f"github-review-{review_id}",
                "rule_id": rule_id,
                "approval_type": approval_type,
                "decision": "approved",
                "actor": {
                    "provider": "github",
                    "id": f"github:{login}",
                    "role": role,
                },
                "subject": {
                    "repository": repository,
                    "pull_request": pull_request,
                    "head_sha": head_sha,
                    "change_digest": change_digest,
                },
                "approved_at": str(raw["submitted_at"]),
                "source": {
                    "ref": str(raw.get("html_url") or f"https://api.github.com/repos/{repository}/pulls/{pull_request}/reviews/{review_id}"),
                    "external_id": review_id,
                },
                "verification": _verification(verified_at=verified_at, valid_until=valid_until),
            }
        )
    return sorted(results, key=lambda item: str(item["approval_id"]))
