from __future__ import annotations

from pathlib import Path

from .models import Event
from .utils import path_matches, run_git

PATH_RULES: list[tuple[str, list[str], float]] = [
    ("security_boundary_change", ["docs/security/**", "**/security/**", "**/auth/**", "**/identity/**"], 0.92),
    ("secrets_handling_change", [".env*", "**/secrets/**", "**/secret*", "**/credentials/**"], 0.95),
    ("cicd_change", [".github/workflows/**", ".gitlab-ci.yml", "ci/**"], 0.95),
    ("infrastructure_change", ["infra/**", "terraform/**", "k8s/**", "Dockerfile", "docker-compose*.yml"], 0.92),
    ("dependency_change", ["pyproject.toml", "requirements*.txt", "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock", "uv.lock"], 0.98),
    ("governance_change", ["docs/governance/**", "automation/documentation_policy.yaml", "automation/documentation_decision_matrix.yaml"], 0.96),
    ("architecture_change", ["docs/architecture/**", "**/architecture/**"], 0.90),
    ("api_contract_change", ["openapi.*", "api/**", "**/routes/**", "**/endpoints/**"], 0.82),
    ("data_model_change", ["migrations/**", "schemas/**", "**/models/**"], 0.82),
    ("document_changed", ["**/*.md"], 0.99),
]

KEYWORD_RULES: list[tuple[str, tuple[str, ...], float]] = [
    ("breaking_change", ("breaking change", "backward incompatible", "remove public api"), 0.88),
    ("security_incident", ("security incident", "credential leak", "data breach"), 0.94),
    ("authentication_authorization_change", ("authentication", "authorization", "rbac", "oauth", "token signer"), 0.78),
    ("component_responsibility_change", ("responsibility moved", "component boundary", "ownership moved"), 0.75),
    ("integration_interface_change", ("integration interface", "adapter contract", "provider interface"), 0.77),
]

# The decision matrix is a multi-source event catalog. These sets declare the
# detection domains that the changeset classifier itself owns. Matrix-only
# validator, label, or external events must not be treated as classifier drift.
CLASSIFIER_PATH_EVENTS: frozenset[str] = frozenset(event for event, _, _ in PATH_RULES)
CLASSIFIER_SEMANTIC_EVENTS: frozenset[str] = frozenset(event for event, _, _ in KEYWORD_RULES)


def classify(changed_files: list[str], diff_text: str = "") -> list[Event]:
    detected: dict[str, Event] = {}
    for event, patterns, confidence in PATH_RULES:
        matches = [path for path in changed_files if path_matches(path, patterns)]
        if matches:
            detected[event] = Event(event, confidence, [f"matched path: {item}" for item in matches[:5]])
    lowered = diff_text.lower()
    for event, keywords, confidence in KEYWORD_RULES:
        hits = [word for word in keywords if word in lowered]
        if hits:
            detected[event] = Event(event, confidence, [f"matched semantic signal: {word}" for word in hits])
    if changed_files and not detected:
        detected["project_state_changed"] = Event(
            "project_state_changed", 0.55, ["repository changed without a specific classification"]
        )
    return sorted(detected.values(), key=lambda item: (-item.confidence, item.name))


def changed_from_git(root: Path, diff_spec: str) -> tuple[list[str], str]:
    names = run_git(root, ["diff", "--name-only", diff_spec])
    if names.returncode != 0:
        raise RuntimeError(names.stderr.strip() or "git diff --name-only failed")
    diff = run_git(root, ["diff", "--no-ext-diff", "--unified=1", diff_spec])
    if diff.returncode != 0:
        raise RuntimeError(diff.stderr.strip() or "git diff failed")
    return [line.strip() for line in names.stdout.splitlines() if line.strip()], diff.stdout
