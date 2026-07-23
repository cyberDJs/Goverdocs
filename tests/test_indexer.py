from pathlib import Path

import pytest

from goverdocs import indexer


def test_rebuild_index_uses_registry_generation_date(
    monkeypatch,
    tmp_path: Path,
) -> None:
    registry = {
        "generated_at": "2026-07-23T15:00:00+00:00",
        "documents": [
            {
                "id": "ADR-0001",
                "type": "architecture-decision",
                "status": "accepted",
                "path": "docs/adr.md",
                "owner": "GOVERDOCS",
            },
            {
                "id": "ARCH-0001",
                "type": "architecture",
                "status": "active",
                "path": "docs/architecture.md",
                "owner": "GOVERDOCS",
            },
        ],
    }

    monkeypatch.setattr(
        indexer,
        "build_registry",
        lambda root, policy_path: registry,
    )

    target = indexer.rebuild_index(
        tmp_path,
        tmp_path / "policy.yaml",
    )
    text = target.read_text(encoding="utf-8")

    assert "updated: 2026-07-23" in text
    assert "last_verified: 2026-07-23" in text
    assert "ADR-0001" in text
    assert "ARCH-0001" in text


def test_rebuild_index_rejects_invalid_generation_time(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        indexer,
        "build_registry",
        lambda root, policy_path: {
            "generated_at": "not-an-iso-timestamp",
            "documents": [],
        },
    )

    with pytest.raises(
        ValueError,
        match="generated_at must be ISO 8601",
    ):
        indexer.rebuild_index(
            tmp_path,
            tmp_path / "policy.yaml",
        )

    assert not (tmp_path / "DOCUMENTATION_INDEX.md").exists()
