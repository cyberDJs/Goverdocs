from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .utils import StringSafeLoader


@dataclass(frozen=True)
class ParsedDocument:
    path: Path
    metadata: dict[str, Any]
    body: str


def parse_frontmatter(path: Path) -> ParsedDocument:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("missing YAML front matter")
    marker = text.find("\n---\n", 4)
    if marker == -1:
        raise ValueError("unterminated YAML front matter")
    raw = text[4:marker]
    metadata = yaml.load(raw, Loader=StringSafeLoader) or {}
    if not isinstance(metadata, dict):
        raise ValueError("front matter must be a mapping")
    return ParsedDocument(path=path, metadata=metadata, body=text[marker + 5 :])
