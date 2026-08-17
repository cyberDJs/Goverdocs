from __future__ import annotations

import json
from pathlib import Path

from goverdocs import gate
from goverdocs.planner import load_matrix


def _matrix_path(tmp_path: Path, rules: list[dict[str, object]]) -> Path:
    path = tmp_path / "matrix.yaml"
    path.write_text(json.dumps({"rules": rules}), encoding="utf-8")
    return path


def test_runtime_matrix_scopes_detection_to_classifier_owned_domains(tmp_path: Path) -> None:
    path = _matrix_path(
        tmp_path,
        [
            {
                "id": "DOC-EVT-039",
                "event": "duplicate_detected",
                "detection": {
                    "any": [
                        {"changed_paths": ["**/*.md"]},
                        {"semantic_signals": ["detekce duplicity"]},
                        {"labels": ["duplicate-detected"]},
                    ]
                },
            },
            {
                "id": "DOC-EVT-011",
                "event": "architecture_change",
                "detection": {
                    "any": [
                        {"changed_paths": ["src/**"]},
                        {"semantic_signals": ["změna architektury"]},
                    ]
                },
            },
            {
                "id": "DOC-EVT-012",
                "event": "component_responsibility_change",
                "detection": {
                    "any": [
                        {"changed_paths": ["src/**"]},
                        {"semantic_signals": ["responsibility moved"]},
                    ]
                },
            },
        ],
    )

    rules = {rule["event"]: rule for rule in load_matrix(path)["rules"]}

    duplicate_clauses = rules["duplicate_detected"]["detection"]["any"]
    assert duplicate_clauses == [{}, {}, {"labels": ["duplicate-detected"]}]

    architecture_clauses = rules["architecture_change"]["detection"]["any"]
    assert architecture_clauses == [{"changed_paths": ["src/**"]}, {}]

    component_clauses = rules["component_responsibility_change"]["detection"]["any"]
    assert component_clauses == [{}, {"semantic_signals": ["responsibility moved"]}]


def test_matrix_drift_ignores_matrix_only_markdown_validator_events(tmp_path: Path) -> None:
    path = _matrix_path(
        tmp_path,
        [
            {
                "id": rule_id,
                "event": event,
                "detection": {"any": [{"changed_paths": ["**/*.md"]}]},
            }
            for rule_id, event in (
                ("DOC-EVT-039", "duplicate_detected"),
                ("DOC-EVT-040", "broken_link_detected"),
                ("DOC-EVT-041", "metadata_missing"),
                ("DOC-EVT-042", "document_conflict_detected"),
            )
        ],
    )

    matrix = load_matrix(path)
    gaps = gate._matrix_detection_gaps(
        ["docs/probes/r7-pr-evidence-dogfood.md"],
        "",
        matrix,
        {"document_changed"},
    )

    assert gaps == []


def test_matrix_drift_still_detects_path_mismatch_inside_classifier_domain(tmp_path: Path) -> None:
    path = _matrix_path(
        tmp_path,
        [
            {
                "id": "DOC-EVT-011",
                "event": "architecture_change",
                "detection": {"any": [{"changed_paths": ["src/**"]}]},
            }
        ],
    )

    gaps = gate._matrix_detection_gaps(
        ["src/goverdocs/gate.py"],
        "",
        load_matrix(path),
        {"project_state_changed"},
    )

    assert len(gaps) == 1
    assert gaps[0]["code"] == "CLASSIFIER_MATRIX_DRIFT"
    assert gaps[0]["subject"] == "DOC-EVT-011"
    assert "architecture_change" in gaps[0]["message"]
