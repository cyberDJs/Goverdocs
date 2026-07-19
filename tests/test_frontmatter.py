from pathlib import Path

from goverdocs.frontmatter import parse_frontmatter


def test_parse_frontmatter(tmp_path: Path) -> None:
    path = tmp_path / "doc.md"
    path.write_text("---\nid: ADR-0001\ncreated: 2026-07-19\n---\n# Body\n", encoding="utf-8")
    parsed = parse_frontmatter(path)
    assert parsed.metadata["id"] == "ADR-0001"
    assert parsed.metadata["created"] == "2026-07-19"
    assert "# Body" in parsed.body
