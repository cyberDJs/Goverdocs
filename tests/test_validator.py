import json
from pathlib import Path

from goverdocs.validator import validate_project


def _write_project(tmp_path: Path) -> None:
    (tmp_path / "docs/x").mkdir(parents=True)
    (tmp_path / "automation").mkdir()
    (tmp_path / "schemas").mkdir()
    (tmp_path / "automation/policy.yaml").write_text(
        "metadata_required:\n  - docs/**/*.md\nexcluded: []\n", encoding="utf-8"
    )
    schema = {
        "type": "object",
        "required": ["id", "type", "title", "status", "owner", "created", "updated", "version", "canonical", "managed_by", "write_policy", "related", "source_refs"],
        "properties": {"id": {"type": "string"}},
    }
    (tmp_path / "schemas/meta.json").write_text(json.dumps(schema), encoding="utf-8")


def _document(doc_id: str) -> str:
    return f"""---
id: {doc_id}
type: decision
title: Test
status: draft
owner: owner
created: 2026-07-19
updated: 2026-07-19
version: 0.1.0
canonical: false
managed_by: human
write_policy: approval-required
related: []
source_refs: []
---
# Test
"""


def test_duplicate_ids_are_rejected(tmp_path: Path) -> None:
    _write_project(tmp_path)
    (tmp_path / "docs/x/a.md").write_text(_document("ADR-1"), encoding="utf-8")
    (tmp_path / "docs/x/b.md").write_text(_document("ADR-1"), encoding="utf-8")
    issues = validate_project(tmp_path, tmp_path / "automation/policy.yaml", tmp_path / "schemas/meta.json")
    assert any(issue.code == "DUPLICATE_ID" for issue in issues)


def test_missing_frontmatter_is_rejected(tmp_path: Path) -> None:
    _write_project(tmp_path)
    (tmp_path / "docs/x/a.md").write_text("# No metadata\n", encoding="utf-8")
    issues = validate_project(tmp_path, tmp_path / "automation/policy.yaml", tmp_path / "schemas/meta.json")
    assert any(issue.code == "FRONTMATTER" for issue in issues)
