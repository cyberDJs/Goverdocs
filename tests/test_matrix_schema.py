import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


def test_decision_matrix_schema() -> None:
    root = Path(__file__).parents[1]
    matrix = yaml.safe_load((root / "automation/documentation_decision_matrix.yaml").read_text(encoding="utf-8"))
    schema = json.loads((root / "schemas/documentation-decision-rule.schema.json").read_text(encoding="utf-8"))
    assert list(Draft202012Validator(schema).iter_errors(matrix)) == []
    assert len(matrix["rules"]) == 45
