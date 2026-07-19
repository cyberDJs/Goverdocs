from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .utils import load_yaml


@dataclass(frozen=True)
class GoverdocsConfig:
    root: Path
    project_name: str
    policy_path: Path
    matrix_path: Path
    metadata_schema_path: Path


def find_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".goverdocs.yaml").is_file():
            return candidate
    return current


def load_config(root: Path | None = None) -> GoverdocsConfig:
    resolved = find_root(root)
    path = resolved / ".goverdocs.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"Missing configuration: {path}")
    raw = load_yaml(path)
    return GoverdocsConfig(
        root=resolved,
        project_name=str(raw.get("project_name", resolved.name)),
        policy_path=resolved / str(raw.get("policy_path", "automation/documentation_policy.yaml")),
        matrix_path=resolved / str(raw.get("matrix_path", "automation/documentation_decision_matrix.yaml")),
        metadata_schema_path=resolved / str(raw.get("metadata_schema_path", "schemas/document-metadata.schema.json")),
    )
