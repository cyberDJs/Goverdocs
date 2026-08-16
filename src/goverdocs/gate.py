from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from .classifier import classify
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
) -> dict[str, Any]:
    events = classify(changed_files, diff_text)
    operations = plan(events, matrix_path)
    matrix = load_matrix(matrix_path)
    by_event = {str(rule["event"]): rule for rule in matrix["rules"]}

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
            gaps.append(
                {
                    "code": "EVIDENCE_UNVERIFIED",
                    "severity": "warning",
                    "blocking": False,
                    "subject": rule_id,
                    "message": f"required evidence not verified by Gate R1: {requirement}",
                }
            )
        if approval_required:
            roles = ", ".join(approval_roles) if approval_roles else "unspecified role"
            gaps.append(
                {
                    "code": "APPROVAL_REQUIRED",
                    "severity": "error",
                    "blocking": True,
                    "subject": rule_id,
                    "message": f"explicit approval is required from {roles}; Gate R1 does not infer approval",
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

    if any(bool(item["blocking"]) for item in gaps):
        status = "BLOCKED"
        rationale = ["one or more blocking governance conditions are unresolved"]
    elif gaps or obligations:
        status = "WARN"
        rationale = ["non-blocking obligations or evidence/freshness gaps require review"]
    else:
        status = "PASS"
        rationale = ["no blocking or warning governance conditions were detected"]

    return {
        "schema_version": 1,
        "status": status,
        "evaluation_date": as_of.isoformat(),
        "input": {
            "digest": _input_digest(changed_files, diff_text, as_of),
            "changed_files": sorted(changed_files),
        },
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
        "validation_issues": [issue.to_dict() for issue in validation_issues],
        "evidence_gaps": gaps,
        "rationale": rationale,
    }
