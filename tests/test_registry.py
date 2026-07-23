import json
from pathlib import Path

import pytest

from goverdocs.registry import (
    build_registry,
    build_status_summary,
    write_status_summary,
)


def test_registry_contains_canonical_docs() -> None:
    root = Path(__file__).parents[1]
    registry = build_registry(root, root / "automation/documentation_policy.yaml")
    ids = {item["id"] for item in registry["documents"]}
    assert {"ADR-0001", "PROJECT-STATE-GOVERDOCS"}.issubset(ids)

def test_status_summary_is_derived_from_registry(
    tmp_path: Path,
) -> None:
    registry = {
        "generated_at": "2026-07-23T15:00:00+00:00",
        "documents": [
            {"id": "A", "status": "active"},
            {"id": "B", "status": "accepted"},
            {"id": "C", "status": "active"},
        ],
    }

    summary = write_status_summary(tmp_path, registry)

    expected = {
        "generated_at": "2026-07-23T15:00:00+00:00",
        "document_count": 3,
        "status_counts": {
            "accepted": 1,
            "active": 2,
        },
    }

    assert summary == expected

    stored = json.loads(
        (
            tmp_path / "manifests/DOCUMENT_STATUS_SUMMARY.json"
        ).read_text(encoding="utf-8")
    )
    assert stored == expected

def test_status_summary_rejects_missing_document_status() -> None:
    registry = {
        "generated_at": "2026-07-23T15:00:00+00:00",
        "documents": [
            {"id": "A"},
        ],
    }

    with pytest.raises(
        ValueError,
        match="status must be a non-empty string",
    ):
        build_status_summary(registry)
