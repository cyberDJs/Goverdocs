from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from .constitutional import validate_constitutional_framework
from .frontmatter import ParsedDocument, parse_frontmatter
from .models import ValidationIssue
from .registry import governed_documents

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def _issue(severity: str, code: str, path: Path, root: Path, message: str) -> ValidationIssue:
    return ValidationIssue(severity, code, path.relative_to(root).as_posix(), message)


def validate_project(
    root: Path,
    policy_path: Path,
    schema_path: Path,
    change_gate_path: Path | None = None,
    change_gate_schema_path: Path | None = None,
) -> list[ValidationIssue]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema_validator = Draft202012Validator(schema, format_checker=FormatChecker())
    issues: list[ValidationIssue] = []
    parsed_documents: list[ParsedDocument] = []
    for path in governed_documents(root, policy_path):
        try:
            parsed = parse_frontmatter(path)
            parsed_documents.append(parsed)
        except ValueError as exc:
            issues.append(_issue("error", "FRONTMATTER", path, root, str(exc)))
            continue
        for error in sorted(schema_validator.iter_errors(parsed.metadata), key=lambda item: list(item.path)):
            location = ".".join(str(item) for item in error.path) or "metadata"
            issues.append(_issue("error", "SCHEMA", path, root, f"{location}: {error.message}"))
        created = parsed.metadata.get("created")
        updated = parsed.metadata.get("updated")
        if isinstance(created, str) and isinstance(updated, str):
            try:
                if date.fromisoformat(updated) < date.fromisoformat(created):
                    issues.append(_issue("error", "CHRONOLOGY", path, root, "updated is before created"))
            except ValueError:
                pass
    ids = [str(doc.metadata.get("id")) for doc in parsed_documents if doc.metadata.get("id")]
    for doc_id, count in Counter(ids).items():
        if count > 1:
            for doc in parsed_documents:
                if doc.metadata.get("id") == doc_id:
                    issues.append(_issue("error", "DUPLICATE_ID", doc.path, root, f"ID {doc_id} appears {count} times"))
    by_id = {str(doc.metadata.get("id")): doc for doc in parsed_documents if doc.metadata.get("id")}
    for doc in parsed_documents:
        meta = doc.metadata
        for related in meta.get("related", []) or []:
            if related not in by_id:
                issues.append(_issue("error", "MISSING_RELATION", doc.path, root, f"related ID does not exist: {related}"))
        supersedes = meta.get("supersedes")
        if supersedes:
            target = by_id.get(str(supersedes))
            if not target:
                issues.append(_issue("error", "MISSING_SUPERSEDED", doc.path, root, f"superseded ID does not exist: {supersedes}"))
            elif target.metadata.get("superseded_by") != meta.get("id"):
                issues.append(_issue("error", "SUPERSESSION_REVERSE", doc.path, root, f"{supersedes} does not point back"))
        superseded_by = meta.get("superseded_by")
        if superseded_by:
            successor = by_id.get(str(superseded_by))
            if not successor or successor.metadata.get("supersedes") != meta.get("id"):
                issues.append(_issue("error", "SUPERSESSION_FORWARD", doc.path, root, f"{superseded_by} does not point back"))
        for raw_link in LINK_RE.findall(doc.body):
            link = raw_link.split("#", 1)[0].strip()
            if not link or link.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target_path = (doc.path.parent / link).resolve()
            try:
                target_path.relative_to(root.resolve())
            except ValueError:
                issues.append(_issue("error", "LINK_ESCAPE", doc.path, root, f"link escapes root: {raw_link}"))
                continue
            if not target_path.exists():
                issues.append(_issue("error", "BROKEN_LINK", doc.path, root, f"missing local target: {raw_link}"))
    issues.extend(validate_constitutional_framework(root, change_gate_path, change_gate_schema_path))
    return sorted(issues, key=lambda item: (item.severity, item.path, item.code))
