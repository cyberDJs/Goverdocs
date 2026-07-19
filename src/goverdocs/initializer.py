from __future__ import annotations

from importlib.resources import files
from pathlib import Path

STARTER_DIRS = [
    "project-memory", "docs/architecture", "docs/decisions/architecture", "docs/decisions/product",
    "docs/decisions/security", "docs/decisions/infrastructure", "docs/decisions/governance",
    "docs/epics/active", "docs/epics/completed", "docs/epics/cancelled",
    "docs/work-blocks/active", "docs/work-blocks/completed", "docs/governance",
    "docs/security/incidents", "docs/product", "docs/operations", "docs/reviews",
    "manifests", "schemas", "automation", "generated", "evidence/receipts", "archive",
]


def initialize_project(target: Path, project_name: str, force: bool = False) -> list[Path]:
    target = target.resolve()
    target.mkdir(parents=True, exist_ok=True)
    for directory in STARTER_DIRS:
        (target / directory).mkdir(parents=True, exist_ok=True)
    resource_root = files("goverdocs").joinpath("resources")
    copies = {
        "documentation_decision_matrix.yaml": target / "automation/documentation_decision_matrix.yaml",
        "documentation_policy.yaml": target / "automation/documentation_policy.yaml",
        "document-metadata.schema.json": target / "schemas/document-metadata.schema.json",
        "documentation-decision-rule.schema.json": target / "schemas/documentation-decision-rule.schema.json",
    }
    written: list[Path] = []
    for source_name, destination in copies.items():
        if destination.exists() and not force:
            continue
        destination.write_text(resource_root.joinpath(source_name).read_text(encoding="utf-8"), encoding="utf-8")
        written.append(destination)
    config = target / ".goverdocs.yaml"
    if force or not config.exists():
        config.write_text(
            "version: 1\n" + f"project_name: {project_name}\n" +
            "policy_path: automation/documentation_policy.yaml\n" +
            "matrix_path: automation/documentation_decision_matrix.yaml\n" +
            "metadata_schema_path: schemas/document-metadata.schema.json\n",
            encoding="utf-8",
        )
        written.append(config)
    return written
