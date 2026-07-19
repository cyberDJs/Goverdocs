from pathlib import Path

from goverdocs.registry import build_registry


def test_registry_contains_canonical_docs() -> None:
    root = Path(__file__).parents[1]
    registry = build_registry(root, root / "automation/documentation_policy.yaml")
    ids = {item["id"] for item in registry["documents"]}
    assert {"ADR-0001", "PROJECT-STATE-GOVERDOCS"}.issubset(ids)
