from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from .classifier import classify
from .evidence import change_digest, record_digest, subject_matches, validate_record, verification_is_fresh, verification_is_trusted
from .frontmatter import parse_frontmatter
from .planner import load_matrix, plan
from .registry import governed_documents
from .utils import path_matches
from .validator import validate_project


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _input_digest(changed_files: list[str], diff_text: str, as_of: date) -> str:
    payload = {
        "as_of": as_of.isoformat(),
        "changed_files": sorted(changed_files),
        "diff_text": diff_text,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _policy_digests(
    root: Path,
    policy_path: Path,
    matrix_path: Path,
    metadata_schema_path: Path,
    change_gate_path: Path | None,
    change_gate_schema_path: Path | None,
) -> dict[str, str]:
    paths: list[tuple[str, Path | None]] = [
        ("documentation_policy", policy_path),
        ("decision_matrix", matrix_path),
        ("metadata_schema", metadata_schema_path),
        ("change_gate", change_gate_path),
        ("change_gate_schema", change_gate_schema_path),
    ]
    result: dict[str, str] = {}
    for name, path in paths:
        if path is None:
            continue
        resolved = path if path.is_absolute() else root / path
        if resolved.exists():
            result[name] = _sha256(resolved)
    return dict(sorted(result.items()))


def _freshness_gaps(root: Path, policy_path: Path, as_of: date) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for path in governed_documents(root, policy_path):
        try:
            parsed = parse_frontmatter(path)
        except ValueError:
            continue
        raw_due = parsed.metadata.get("review_due")
        if not isinstance(raw_due, str):
            continue
        try:
            due = date.fromisoformat(raw_due)
        except ValueError:
            continue
        if due >= as_of:
            continue
        status = str(parsed.metadata.get("status") or "")
        if status in {"archived", "cancelled", "deprecated", "rejected", "superseded"}:
            continue
        gaps.append(
            {
                "code": "REVIEW_OVERDUE",
                "severity": "warning",
                "blocking": False,
                "subject": path.relative_to(root).as_posix(),
                "message": f"review_due {due.isoformat()} is before evaluation date {as_of.isoformat()}",
            }
        )
    return gaps


def _matrix_detection_gaps(
    changed_files: list[str],
    diff_text: str,
    matrix: dict[str, Any],
    emitted_events: set[str],
) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    lowered = diff_text.lower()
    for rule in matrix.get("rules", []):
        if not isinstance(rule, dict):
            continue
        event = str(rule.get("event") or "")
        rule_id = str(rule.get("id") or event or "UNKNOWN")
        if not event or event in emitted_events:
            continue
        detection = rule.get("detection") or {}
        if not isinstance(detection, dict):
            continue
        reasons: list[str] = []
        for clause in detection.get("any", []) or []:
            if not isinstance(clause, dict):
                continue
            patterns = [str(item) for item in clause.get("changed_paths", []) or []]
            if patterns:
                matches = sorted(path for path in changed_files if path_matches(path, patterns))
                reasons.extend(f"matched matrix path: {path}" for path in matches[:5])
            signals = [str(item).lower() for item in clause.get("semantic_signals", []) or []]
            if signals:
                hits = sorted(signal for signal in signals if signal and signal in lowered)
                reasons.extend(f"matched matrix semantic signal: {signal}" for signal in hits[:5])
        if not reasons:
            continue
        detail = "; ".join(sorted(set(reasons)))
        gaps.append(
            {
                "code": "CLASSIFIER_MATRIX_DRIFT",
                "severity": "warning",
                "blocking": False,
                "subject": rule_id,
                "message": f"matrix detection matched event {event}, but classifier did not emit it: {detail}",
            }
        )
    return gaps


def _assess_evidence(
    record: dict[str, Any],
    *,
    expected_change_digest: str,
    repository: str | None,
    pull_request: int | None,
    head_sha: str | None,
    as_of: date,
    trusted_verifiers: set[str],
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": str(record.get("evidence_id") or "UNKNOWN"),
        "record_digest": record_digest(record),
        "rule_id": str(record.get("rule_id") or ""),
        "requirement": str(record.get("requirement") or ""),
        "status": "INVALID",
        "reasons": [],
    }
    errors = validate_record(record, "evidence-item.schema.json")
    if errors:
        result["reasons"] = errors
        return result
    subject_ok, subject_reason = subject_matches(
        record,
        expected_change_digest=expected_change_digest,
        repository=repository,
        pull_request=pull_request,
        head_sha=head_sha,
        require_scm_context=False,
    )
    if not subject_ok:
        result["status"] = "SUBJECT_MISMATCH"
        result["reasons"] = [subject_reason]
        return result
    fresh, fresh_reason = verification_is_fresh(record, as_of)
    if not fresh:
        result["status"] = "STALE"
        result["reasons"] = [fresh_reason]
        return result
    trusted, trusted_reason = verification_is_trusted(record, trusted_verifiers)
    if not trusted:
        result["status"] = "UNTRUSTED"
        result["reasons"] = [trusted_reason]
        return result
    result["status"] = "VERIFIED"
    result["reasons"] = [subject_reason, fresh_reason, trusted_reason]
    return result


def _assess_approval(
    record: dict[str, Any],
    *,
    expected_change_digest: str,
    repository: str | None,
    pull_request: int | None,
    head_sha: str | None,
    as_of: date,
    trusted_verifiers: set[str],
) -> dict[str, Any]:
    actor = record.get("actor") if isinstance(record.get("actor"), dict) else {}
    result: dict[str, Any] = {
        "id": str(record.get("approval_id") or "UNKNOWN"),
        "record_digest": record_digest(record),
        "rule_id": str(record.get("rule_id") or ""),
        "approval_type": str(record.get("approval_type") or ""),
        "decision": str(record.get("decision") or ""),
        "actor_id": str(actor.get("id") or ""),
        "actor_role": str(actor.get("role") or ""),
        "status": "INVALID",
        "reasons": [],
    }
    errors = validate_record(record, "approval.schema.json")
    if errors:
        result["reasons"] = errors
        return result
    subject_ok, subject_reason = subject_matches(
        record,
        expected_change_digest=expected_change_digest,
        repository=repository,
        pull_request=pull_request,
        head_sha=head_sha,
        require_scm_context=True,
    )
    if not subject_ok:
        result["status"] = "SUBJECT_MISMATCH"
        result["reasons"] = [subject_reason]
        return result
    fresh, fresh_reason = verification_is_fresh(record, as_of)
    if not fresh:
        result["status"] = "STALE"
        result["reasons"] = [fresh_reason]
        return result
    trusted, trusted_reason = verification_is_trusted(record, trusted_verifiers)
    if not trusted:
        result["status"] = "UNTRUSTED"
        result["reasons"] = [trusted_reason]
        return result
    if record["decision"] != "approved":
        result["status"] = str(record["decision"]).upper()
        result["reasons"] = [subject_reason, fresh_reason, trusted_reason, f"approval decision is {record['decision']}"]
        return result
    result["status"] = "VERIFIED"
    result["reasons"] = [subject_reason, fresh_reason, trusted_reason]
    return result


def evaluate_gate(
    *,
    root: Path,
    policy_path: Path,
    matrix_path: Path,
    metadata_schema_path: Path,
    change_gate_path: Path | None,
    change_gate_schema_path: Path | None,
    changed_files: list[str],
    diff_text: str,
    as_of: date,
    repository: str | None = None,
    pull_request: int | None = None,
    head_sha: str | None = None,
    evidence_items: list[dict[str, Any]] | None = None,
    approvals: list[dict[str, Any]] | None = None,
    trusted_verifiers: set[str] | None = None,
) -> dict[str, Any]:
    evidence_items = evidence_items or []
    approvals = approvals or []
    trusted_verifiers = trusted_verifiers or set()
    current_change_digest = change_digest(changed_files, diff_text)

    events = classify(changed_files, diff_text)
    operations = plan(events, matrix_path)
    matrix = load_matrix(matrix_path)
    by_event = {str(rule["event"]): rule for rule in matrix["rules"]}

    evidence_results = [
        _assess_evidence(
            record,
            expected_change_digest=current_change_digest,
            repository=repository,
            pull_request=pull_request,
            head_sha=head_sha,
            as_of=as_of,
            trusted_verifiers=trusted_verifiers,
        )
        for record in evidence_items
    ]
    approval_results = [
        _assess_approval(
            record,
            expected_change_digest=current_change_digest,
            repository=repository,
            pull_request=pull_request,
            head_sha=head_sha,
            as_of=as_of,
            trusted_verifiers=trusted_verifiers,
        )
        for record in approvals
    ]

    obligations: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    emitted_events = {event.name for event in events}
    gaps.extend(_matrix_detection_gaps(changed_files, diff_text, matrix, emitted_events))

    for event in events:
        rule = by_event.get(event.name)
        if not rule:
            continue
        rule_id = str(rule["id"])
        approval = rule.get("approval", {}) or {}
        approval_required = bool(approval.get("required", False))
        approval_roles = sorted(str(role) for role in approval.get("roles", []) or [])
        required_evidence = sorted(str(item) for item in rule.get("required_evidence", []) or [])
        rule_operations = [operation.to_dict() for operation in operations if operation.rule_id == rule_id]
        obligations.append(
            {
                "event": event.name,
                "rule_id": rule_id,
                "severity": str(rule.get("severity", "unknown")),
                "priority": int(rule.get("priority", 0)),
                "required_evidence": required_evidence,
                "approval_required": approval_required,
                "approval_roles": approval_roles,
                "actions": rule_operations,
            }
        )

        for requirement in required_evidence:
            candidates = [item for item in evidence_results if item["rule_id"] == rule_id and item["requirement"] == requirement]
            if any(item["status"] == "VERIFIED" for item in candidates):
                continue
            if not candidates:
                message = f"required evidence is missing: {requirement}"
                code = "EVIDENCE_MISSING"
            else:
                states = ", ".join(sorted({str(item["status"]) for item in candidates}))
                message = f"required evidence is present but not verified for this exact change: {requirement} ({states})"
                code = "EVIDENCE_UNVERIFIED"
            gaps.append(
                {
                    "code": code,
                    "severity": "warning",
                    "blocking": False,
                    "subject": rule_id,
                    "message": message,
                }
            )

        if approval_required:
            candidates = [item for item in approval_results if item["rule_id"] == rule_id]
            verified = [
                item
                for item in candidates
                if item["status"] == "VERIFIED" and (not approval_roles or item["actor_role"] in approval_roles)
            ]
            if verified:
                continue
            if repository is None or pull_request is None or head_sha is None:
                code = "APPROVAL_CONTEXT_INCOMPLETE"
                message = "approval requires repository, pull_request and head_sha evaluation context"
            elif not candidates:
                roles = ", ".join(approval_roles) if approval_roles else "unspecified role"
                code = "APPROVAL_REQUIRED"
                message = f"explicit approval is required from {roles}; no bound approval record was provided"
            else:
                states = ", ".join(sorted({str(item["status"]) for item in candidates}))
                code = "APPROVAL_UNVERIFIED"
                message = f"approval records exist but none is verified, fresh, trusted, role-authorized and bound to this exact change ({states})"
            gaps.append(
                {
                    "code": code,
                    "severity": "error",
                    "blocking": True,
                    "subject": rule_id,
                    "message": message,
                }
            )

    validation_issues = validate_project(
        root,
        policy_path,
        metadata_schema_path,
        change_gate_path,
        change_gate_schema_path,
    )
    for issue in validation_issues:
        blocking = issue.severity.lower() == "error"
        gaps.append(
            {
                "code": f"VALIDATION_{issue.code}",
                "severity": issue.severity,
                "blocking": blocking,
                "subject": issue.path,
                "message": issue.message,
            }
        )

    gaps.extend(_freshness_gaps(root, policy_path, as_of))
    gaps = sorted(
        gaps,
        key=lambda item: (
            not bool(item["blocking"]),
            str(item["severity"]),
            str(item["code"]),
            str(item["subject"]),
            str(item["message"]),
        ),
    )
    obligations = sorted(obligations, key=lambda item: (-int(item["priority"]), str(item["rule_id"])))
    evidence_results = sorted(evidence_results, key=lambda item: (str(item["rule_id"]), str(item["requirement"]), str(item["id"])))
    approval_results = sorted(approval_results, key=lambda item: (str(item["rule_id"]), str(item["actor_role"]), str(item["id"])))

    if any(bool(item["blocking"]) for item in gaps):
        status = "BLOCKED"
        rationale = ["one or more blocking governance conditions are unresolved"]
    elif gaps:
        status = "WARN"
        rationale = ["non-blocking evidence, freshness or drift gaps require review"]
    else:
        status = "PASS"
        rationale = ["all detected obligations are satisfied for the declared evaluation scope"]

    return {
        "schema_version": 2,
        "status": status,
        "evaluation_date": as_of.isoformat(),
        "input": {
            "digest": _input_digest(changed_files, diff_text, as_of),
            "change_digest": current_change_digest,
            "changed_files": sorted(changed_files),
            "repository": repository,
            "pull_request": pull_request,
            "head_sha": head_sha,
        },
        "trust": {"trusted_verifiers": sorted(trusted_verifiers)},
        "policy_digests": _policy_digests(
            root,
            policy_path,
            matrix_path,
            metadata_schema_path,
            change_gate_path,
            change_gate_schema_path,
        ),
        "events": [event.to_dict() for event in events],
        "obligations": obligations,
        "evidence_inputs": evidence_results,
        "approval_inputs": approval_results,
        "validation_issues": [issue.to_dict() for issue in validation_issues],
        "evidence_gaps": gaps,
        "rationale": rationale,
    }
