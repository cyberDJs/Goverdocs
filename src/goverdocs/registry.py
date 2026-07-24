from __future__ import annotations

from collections import Counter
from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Any

from .frontmatter import parse_frontmatter
from .utils import dump_yaml, load_yaml, path_matches, write_json


def governed_documents(root: Path, policy_path: Path) -> list[Path]:
    policy = load_yaml(policy_path)
    required = [str(item) for item in policy.get("metadata_required", [])]
    excluded = [str(item) for item in policy.get("excluded", [])]
    result: list[Path] = []
    for path in root.rglob("*.md"):
        rel = path.relative_to(root).as_posix()
        if path_matches(rel, excluded):
            continue
        if path_matches(rel, required):
            result.append(path)
    return sorted(result)


def _deterministic_generated_at(
    documents: list[dict[str, Any]],
) -> str:
    """Derive a stable UTC timestamp from governed source metadata."""
    if not documents:
        return "1970-01-01T00:00:00+00:00"

    updated_dates: list[date] = []
    for document in documents:
        raw_updated = document.get("updated")
        if not isinstance(raw_updated, str):
            raise ValueError(
                "registry document updated must be an ISO date string"
            )
        try:
            updated_dates.append(date.fromisoformat(raw_updated))
        except ValueError as exc:
            raise ValueError(
                "registry document updated must be an ISO date string"
            ) from exc

    latest = max(updated_dates)
    return datetime.combine(
        latest,
        time.min,
        tzinfo=UTC,
    ).isoformat(timespec="seconds")


def build_registry(root: Path, policy_path: Path) -> dict[str, Any]:
    documents: list[dict[str, Any]] = []
    for path in governed_documents(root, policy_path):
        try:
            parsed = parse_frontmatter(path)
        except ValueError:
            continue
        meta = parsed.metadata
        documents.append({
            "id": meta.get("id"), "path": path.relative_to(root).as_posix(),
            "type": meta.get("type"), "status": meta.get("status"),
            "canonical": meta.get("canonical", False), "owner": meta.get("owner"),
            "updated": meta.get("updated"), "related": meta.get("related", []),
            "supersedes": meta.get("supersedes"), "superseded_by": meta.get("superseded_by"),
        })
    return {
        "generated_at": _deterministic_generated_at(documents),
        "documents": documents,
    }


def write_registry(root: Path, policy_path: Path) -> dict[str, Any]:
    registry = build_registry(root, policy_path)
    target = root / "manifests/DOCUMENT_REGISTRY.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(dump_yaml(registry), encoding="utf-8")
    return registry


def build_status_summary(registry: dict[str, Any]) -> dict[str, Any]:
    raw_documents = registry.get("documents")
    generated_at = registry.get("generated_at")

    if not isinstance(raw_documents, list):
        raise ValueError("registry documents must be a list")

    if not isinstance(generated_at, str):
        raise ValueError("registry generated_at must be a string")

    documents: list[dict[str, Any]] = []
    statuses: list[str] = []

    for item in raw_documents:
        if not isinstance(item, dict):
            raise ValueError("registry document entries must be mappings")

        status = item.get("status")
        if not isinstance(status, str) or not status.strip():
            raise ValueError(
                "registry document status must be a non-empty string"
            )

        documents.append(item)
        statuses.append(status)

    status_counts = Counter(statuses)

    return {
        "generated_at": generated_at,
        "document_count": len(documents),
        "status_counts": dict(sorted(status_counts.items())),
    }


def write_status_summary(
    root: Path,
    registry: dict[str, Any],
) -> dict[str, Any]:
    summary = build_status_summary(registry)
    write_json(
        root / "manifests/DOCUMENT_STATUS_SUMMARY.json",
        summary,
    )
    return summary


def write_relationship_graph(root: Path, registry: dict[str, Any]) -> None:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []
    for document in registry["documents"]:
        doc_id = document.get("id")
        if not doc_id:
            continue
        nodes.append({"id": doc_id, "path": document["path"], "type": document.get("type")})
        for related in document.get("related") or []:
            edges.append({"from": doc_id, "to": related, "type": "related"})
        if document.get("supersedes"):
            edges.append({"from": doc_id, "to": document["supersedes"], "type": "supersedes"})
    write_json(root / "manifests/RELATIONSHIP_GRAPH.json", {"nodes": nodes, "edges": edges})
