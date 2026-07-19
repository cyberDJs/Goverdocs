from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import Event, Operation
from .utils import load_yaml


def load_matrix(path: Path) -> dict[str, Any]:
    matrix = load_yaml(path)
    if not isinstance(matrix.get("rules"), list):
        raise ValueError("decision matrix must contain a rules list")
    return matrix


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
