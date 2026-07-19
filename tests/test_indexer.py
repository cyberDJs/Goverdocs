from pathlib import Path

from goverdocs.indexer import rebuild_index


def test_rebuild_index() -> None:
    root = Path(__file__).parents[1]
    target = rebuild_index(root, root / "automation/documentation_policy.yaml")
    text = target.read_text(encoding="utf-8")
    assert "ADR-0001" in text
    assert "ARCH-0001" in text
