from __future__ import annotations

from pathlib import Path
from typing import Any

from .classifier import CLASSIFIER_PATH_EVENTS, CLASSIFIER_SEMANTIC_EVENTS
from .models import Event, Operation
from .utils import load_yaml


def _scope_detection_to_classifier(matrix: dict[str, Any]) -> dict[str, Any]:
    """Return the runtime matrix view owned by the changeset classifier.

    The canonical decision matrix is a multi-source event catalog. A rule can
    be triggered by changed paths, semantic signals, labels, validators, or
    other adapters. The Gate's classifier/matrix drift check must compare only
    the path and semantic domains the changeset classifier explicitly owns;
    otherwise validator-only events such as duplicate or broken-link findings
    become false classifier drift on every Markdown change.
    """
    for raw_rule in matrix.get("rules", []):
        if not isinstance(raw_rule, dict):
            continue
        event = str(raw_rule.get("event") or "")
        detection = raw_rule.get("detection")
        if not isinstance(detection, dict):
            continue
        clauses = detection.get("any")
        if not isinstance(clauses, list):
            continue
        for clause in clauses:
            if not isinstance(clause, dict):
                continue
            if event not in CLASSIFIER_PATH_EVENTS:
                clause.pop("changed_paths", None)
            if event not in CLASSIFIER_SEMANTIC_EVENTS:
                clause.pop("semantic_signals", None)
    return matrix


def load_matrix(path: Path) -> dict[str, Any]:
    matrix = load_yaml(path)
    if not isinstance(matrix.get("rules"), list):
        raise ValueError("decision matrix must contain a rules list")
    return _scope_detection_to_classifier(matrix)


def plan(events: list[Event], matrix_path: Path) -> list[Operation]:
    matrix = load_matrix(matrix_path)
    by_event = {str(rule["event"]): rule for rule in matrix["rules"]}
    operations: list[Operation] = []
    for event in events:
        rule = by_event.get(event.name)
        if not rule:
            continue
        approval = bool(rule.get("approval", {}).get("required", False))
        for action in rule.get("actions", []):
            operations.append(Operation(
                event=event.name,
                rule_id=str(rule["id"]),
                document_type=str(action["document_type"]),
                action=str(action["action"]),
                target=str(action["target"]),
                write_policy=str(action["write_policy"]),
                approval_required=approval,
                severity=str(rule["severity"]),
                priority=int(rule["priority"]),
            ))
    return sorted(operations, key=lambda item: (-item.priority, item.rule_id, item.target))
