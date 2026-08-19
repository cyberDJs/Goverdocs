from __future__ import annotations

import hashlib
import json
import re
from typing import Any


class WriteGrantError(ValueError):
    pass


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_HEAD_SHA = re.compile(r"^[0-9a-f]{40}$")
_NON_BLOCKING_GATE_STATUSES = {"PASS", "WARN"}


def _digest(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _non_empty_string(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WriteGrantError(f"{field} must be a non-empty string")
    return value.strip()


def _positive_int(value: object, *, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise WriteGrantError(f"{field} must be a positive integer")
    return value


def _validate_subject(gate_report: dict[str, Any]) -> dict[str, object]:
    raw_input = gate_report.get("input")
    if not isinstance(raw_input, dict):
        raise WriteGrantError("gate report input must be a mapping")

    repository = _non_empty_string(raw_input.get("repository"), field="input.repository")
    pull_request = _positive_int(raw_input.get("pull_request"), field="input.pull_request")
    head_sha = _non_empty_string(raw_input.get("head_sha"), field="input.head_sha")
    if _HEAD_SHA.fullmatch(head_sha) is None:
        raise WriteGrantError("input.head_sha must be a 40-character lowercase git SHA")
    change_digest = _non_empty_string(
        raw_input.get("change_digest"),
        field="input.change_digest",
    )
    if _SHA256.fullmatch(change_digest) is None:
        raise WriteGrantError("input.change_digest must be a lowercase SHA-256 digest")

    return {
        "repository": repository,
        "pull_request": pull_request,
        "head_sha": head_sha,
        "change_digest": change_digest,
    }


def _normalize_operation(raw: object, *, index: int) -> dict[str, object]:
    if not isinstance(raw, dict):
        raise WriteGrantError(f"operations[{index}] must be a mapping")

    required_strings = (
        "event",
        "rule_id",
        "document_type",
        "action",
        "target",
        "write_policy",
        "severity",
    )
    normalized: dict[str, object] = {
        field: _non_empty_string(raw.get(field), field=f"operations[{index}].{field}")
        for field in required_strings
    }

    approval_required = raw.get("approval_required")
    if not isinstance(approval_required, bool):
        raise WriteGrantError(f"operations[{index}].approval_required must be boolean")
    priority = raw.get("priority")
    if not isinstance(priority, int) or isinstance(priority, bool):
        raise WriteGrantError(f"operations[{index}].priority must be an integer")

    normalized["approval_required"] = approval_required
    normalized["priority"] = priority
    return normalized


def _operation_sort_key(item: dict[str, object]) -> tuple[int, str, str, str]:
    priority = item.get("priority")
    if not isinstance(priority, int) or isinstance(priority, bool):
        raise WriteGrantError("normalized operation priority must be an integer")
    return (
        -priority,
        str(item["rule_id"]),
        str(item["target"]),
        str(item["action"]),
    )


def _authorized_operations(gate_report: dict[str, Any]) -> list[dict[str, object]]:
    raw_obligations = gate_report.get("obligations")
    if not isinstance(raw_obligations, list):
        raise WriteGrantError("gate report obligations must be a list")

    operations: list[dict[str, object]] = []
    seen: set[str] = set()
    index = 0
    for obligation in raw_obligations:
        if not isinstance(obligation, dict):
            raise WriteGrantError("gate report obligation must be a mapping")
        raw_actions = obligation.get("actions")
        if not isinstance(raw_actions, list):
            raise WriteGrantError("gate report obligation actions must be a list")
        for raw_action in raw_actions:
            operation = _normalize_operation(raw_action, index=index)
            encoded = json.dumps(operation, sort_keys=True, separators=(",", ":"))
            if encoded in seen:
                raise WriteGrantError("gate report contains duplicate authorized operations")
            seen.add(encoded)
            operations.append(operation)
            index += 1

    if not operations:
        raise WriteGrantError("gate report contains no write operations to authorize")

    return sorted(operations, key=_operation_sort_key)


def issue_write_grant(gate_report: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(gate_report, dict):
        raise WriteGrantError("gate report must be a mapping")

    status = _non_empty_string(gate_report.get("status"), field="status")
    if status not in _NON_BLOCKING_GATE_STATUSES:
        raise WriteGrantError(f"gate status {status} cannot authorize writes")

    gaps = gate_report.get("evidence_gaps")
    if not isinstance(gaps, list):
        raise WriteGrantError("gate report evidence_gaps must be a list")
    if any(isinstance(item, dict) and item.get("blocking") is True for item in gaps):
        raise WriteGrantError("gate report contains a blocking governance gap")

    subject = _validate_subject(gate_report)
    operations = _authorized_operations(gate_report)
    gate_report_digest = _digest(gate_report)
    operations_digest = _digest(operations)
    grant_payload = {
        "schema_version": 1,
        "subject": subject,
        "gate_status": status,
        "gate_report_digest": gate_report_digest,
        "operations_digest": operations_digest,
        "operations": operations,
    }

    return {
        "grant_id": f"write-grant-v1:{_digest(grant_payload)}",
        **grant_payload,
    }


def validate_write_grant(grant: dict[str, Any], gate_report: dict[str, Any]) -> None:
    if not isinstance(grant, dict):
        raise WriteGrantError("write grant must be a mapping")
    expected = issue_write_grant(gate_report)
    if grant != expected:
        raise WriteGrantError("write grant does not match canonical gate-derived grant")


def authorize_operation(
    grant: dict[str, Any],
    gate_report: dict[str, Any],
    *,
    repository: str,
    pull_request: int,
    head_sha: str,
    change_digest: str,
    operation: dict[str, Any],
) -> None:
    validate_write_grant(grant, gate_report)

    subject = grant["subject"]
    expected_subject = {
        "repository": repository,
        "pull_request": pull_request,
        "head_sha": head_sha,
        "change_digest": change_digest,
    }
    if subject != expected_subject:
        raise WriteGrantError("write grant subject does not match requested execution subject")

    normalized = _normalize_operation(operation, index=0)
    if normalized not in grant["operations"]:
        raise WriteGrantError("requested write operation is outside the authorized grant scope")
