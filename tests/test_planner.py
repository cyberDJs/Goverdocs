from pathlib import Path

from goverdocs.models import Event
from goverdocs.planner import plan


def test_architecture_plan() -> None:
    matrix = Path(__file__).parents[1] / "automation/documentation_decision_matrix.yaml"
    operations = plan([Event("architecture_change", 1.0)], matrix)
    targets = {operation.target for operation in operations}
    assert "docs/architecture/ARCH-*.md" in targets
    assert "docs/decisions/architecture/ADR-*.md" in targets
    assert all(operation.rule_id == "DOC-EVT-011" for operation in operations)
