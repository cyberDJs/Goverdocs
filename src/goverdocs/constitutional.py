from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from yaml import YAMLError

from .models import ValidationIssue
from .utils import load_yaml

EXPECTED_WORLD_SHA256 = "ed44c6147049887d941b7497f1bce3b817f22b6ae00a5136a27365a2f688d918"
EXPECTED_DIMENSION_COUNT = 10
APPROVAL_GATE_REFERENCE = "GOVERDOCS_CONSTITUTIONAL_FRAMEWORK.md#approval-gates"
REQUIRED_REPORTING_FIELDS = (
    "verified_count",
    "not_applicable_count",
    "blocked_count",
    "declared_scope",
    "environment",
    "evidence_refs",
)
MOTTO = (
    "Nejsilnější vývojový model spojuje Jobsovu produktovou čistotu, unixovou "
    "jednoduchost, DevOps automatizaci, SRE spolehlivost, bezpečnostní princip nulové "
    "důvěry a úplnou auditovatelnost celého životního cyklu systému — nejen jeho Git "
    "historie."
)
CHANGE_PRINCIPLE = (
    "Každá změna musí být jednoduchá, účelná, automatizovaná, bezpečná, měřitelná, "
    "vratná a důkazně ověřitelná."
)


def _issue(root: Path, path: Path, code: str, message: str) -> ValidationIssue:
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError:
        relative = path.as_posix()
    return ValidationIssue("error", code, relative, message)


def _normalise(text: str) -> str:
    return " ".join(text.split())


def _validate_manifest_integrity(root: Path, required_paths: set[str]) -> list[ValidationIssue]:
    manifest_path = root / "manifests/GOVERNANCE_ARTIFACTS.yaml"
    if not manifest_path.is_file():
        return [_issue(root, manifest_path, "CONSTITUTION_MANIFEST", "missing governance artifacts manifest")]

    try:
        manifest = load_yaml(manifest_path)
    except (OSError, ValueError, YAMLError) as exc:
        return [_issue(root, manifest_path, "CONSTITUTION_MANIFEST", f"invalid governance artifacts manifest: {exc}")]

    raw_artifacts = manifest.get("artifacts", [])
    if not isinstance(raw_artifacts, list):
        return [_issue(root, manifest_path, "CONSTITUTION_MANIFEST", "artifacts must be a list")]

    artifacts = [item for item in raw_artifacts if isinstance(item, dict)]
    paths = [str(item.get("path")) for item in artifacts if item.get("path")]
    ids = [str(item.get("id")) for item in artifacts if item.get("id")]
    issues: list[ValidationIssue] = []
    for value, count in sorted(Counter(paths).items()):
        if count > 1:
            issues.append(_issue(root, manifest_path, "CONSTITUTION_MANIFEST_DUPLICATE_PATH", f"artifact path appears {count} times: {value}"))
    for value, count in sorted(Counter(ids).items()):
        if count > 1:
            issues.append(_issue(root, manifest_path, "CONSTITUTION_MANIFEST_DUPLICATE_ID", f"artifact ID appears {count} times: {value}"))

    by_path = {str(item.get("path")): item for item in artifacts if item.get("path")}
    for relative in sorted(required_paths):
        target = root / relative
        artifact = by_path.get(relative)
        if artifact is None:
            issues.append(_issue(root, manifest_path, "CONSTITUTION_MANIFEST", f"missing artifact entry: {relative}"))
            continue
        integrity = artifact.get("integrity")
        if not isinstance(integrity, dict) or integrity.get("algorithm") != "sha256":
            issues.append(_issue(root, manifest_path, "CONSTITUTION_MANIFEST", f"invalid integrity declaration: {relative}"))
            continue
        if not target.is_file():
            issues.append(_issue(root, target, "CONSTITUTION_FILE", "declared artifact is missing"))
            continue
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if integrity.get("digest") != actual:
            issues.append(_issue(root, target, "CONSTITUTION_CHECKSUM", f"checksum mismatch for {relative}"))
    return issues


def validate_constitutional_framework(
    root: Path,
    gate_path: Path | None,
    gate_schema_path: Path | None,
) -> list[ValidationIssue]:
    if gate_path is None and gate_schema_path is None:
        return []

    anchor = root / ".goverdocs.yaml"
    if gate_path is None or gate_schema_path is None:
        return [_issue(root, anchor, "CHANGE_GATE_CONFIG", "both change_gate_path and change_gate_schema_path are required")]

    framework_path = root / "GOVERDOCS_CONSTITUTIONAL_FRAMEWORK.md"
    product_path = root / "PRODUCT_DECISION_EXECUTION_OPERATING_MODE.md"
    world_path = root / "WORLD_CLASS_SOFTWARE_DEVOPS_OPERATING_MODE.md"
    resolved_root = root.resolve()
    for configured_path in (gate_path, gate_schema_path):
        try:
            configured_path.resolve().relative_to(resolved_root)
        except ValueError:
            return [_issue(root, configured_path, "CHANGE_GATE_PATH", "configured path escapes the project root")]

    required_files = {framework_path, product_path, world_path, gate_path, gate_schema_path}
    missing = [path for path in required_files if not path.is_file()]
    if missing:
        return [_issue(root, path, "CONSTITUTION_FILE", "required constitutional framework file is missing") for path in sorted(missing)]

    issues: list[ValidationIssue] = []
    world_digest = hashlib.sha256(world_path.read_bytes()).hexdigest()
    if world_digest != EXPECTED_WORLD_SHA256:
        issues.append(_issue(root, world_path, "WORLD_CHECKSUM", "canonical WORLD checksum changed"))

    try:
        schema = json.loads(gate_schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except (OSError, json.JSONDecodeError, SchemaError) as exc:
        issues.append(_issue(root, gate_schema_path, "CHANGE_GATE_SCHEMA_DEFINITION", f"invalid change-gate schema: {exc}"))
        return sorted(issues, key=lambda item: (item.path, item.code, item.message))

    try:
        gate = load_yaml(gate_path)
    except (OSError, ValueError, YAMLError) as exc:
        issues.append(_issue(root, gate_path, "CHANGE_GATE_DOCUMENT", f"invalid change-gate document: {exc}"))
        return sorted(issues, key=lambda item: (item.path, item.code, item.message))

    schema_validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for error in sorted(schema_validator.iter_errors(gate), key=lambda item: list(item.path)):
        location = ".".join(str(item) for item in error.path) or "gate"
        issues.append(_issue(root, gate_path, "CHANGE_GATE_SCHEMA", f"{location}: {error.message}"))

    dimensions = gate.get("dimensions", [])
    if isinstance(dimensions, list):
        dimension_ids = [str(item.get("id")) for item in dimensions if isinstance(item, dict)]
        if len(dimension_ids) != len(set(dimension_ids)):
            issues.append(_issue(root, gate_path, "CHANGE_GATE_DUPLICATE", "dimension IDs must be unique"))
        if len(dimension_ids) != EXPECTED_DIMENSION_COUNT:
            issues.append(_issue(root, gate_path, "CHANGE_GATE_DIMENSION_COUNT", f"exactly {EXPECTED_DIMENSION_COUNT} unique dimensions are required"))

    if gate.get("enforcement") != "warn-only":
        issues.append(_issue(root, gate_path, "CHANGE_GATE_ENFORCEMENT", "the experimental gate must remain warn-only"))

    if gate.get("approval_gate_reference") != APPROVAL_GATE_REFERENCE:
        issues.append(_issue(root, gate_path, "CHANGE_GATE_APPROVAL_REFERENCE", "change gate must reference the canonical approval-gate section"))

    if tuple(gate.get("reporting_requires", [])) != REQUIRED_REPORTING_FIELDS:
        issues.append(_issue(root, gate_path, "CHANGE_GATE_REPORTING", "change-gate reports must include exact scope, environment, counts and evidence references"))

    framework = framework_path.read_text(encoding="utf-8")
    product = product_path.read_text(encoding="utf-8")
    combined = _normalise(framework + "\n" + product)
    if combined.count(_normalise(MOTTO)) != 1:
        issues.append(_issue(root, framework_path, "CONSTITUTION_MOTTO", "the exact operational motto must appear once across the framework and product mode"))
    if combined.count(_normalise(CHANGE_PRINCIPLE)) != 1:
        issues.append(_issue(root, framework_path, "CONSTITUTION_CHANGE_PRINCIPLE", "the exact seven-property change principle must appear once across the framework and product mode"))

    for required in (
        "PROPOSED",
        "APPROVED",
        "IMPLEMENTED",
        "VERIFIED",
        "INFERRED",
        "UNKNOWN",
        "BLOCKED",
        "PARTIALLY VERIFIED",
    ):
        if required not in framework:
            issues.append(_issue(root, framework_path, "CONSTITUTION_STATUS", f"missing truth status: {required}"))

    if "WORLD_CLASS_SOFTWARE_DEVOPS_OPERATING_MODE.md" not in framework:
        issues.append(_issue(root, framework_path, "CONSTITUTION_AUTHORITY", "framework must explicitly preserve WORLD authority"))
    if '<a id="approval-gates"></a>' not in framework:
        issues.append(_issue(root, framework_path, "CONSTITUTION_APPROVAL_ANCHOR", "framework must expose the stable approval-gates anchor"))
    if "GOVERDOCS_CONSTITUTIONAL_FRAMEWORK.md" not in product:
        issues.append(_issue(root, product_path, "CONSTITUTION_PARENT", "product mode must reference its coordinating framework"))

    issues.extend(
        _validate_manifest_integrity(
            root,
            {
                "WORLD_CLASS_SOFTWARE_DEVOPS_OPERATING_MODE.md",
                "GOVERDOCS_CONSTITUTIONAL_FRAMEWORK.md",
                "PRODUCT_DECISION_EXECUTION_OPERATING_MODE.md",
                "policies/CHANGE_GATE_10_OF_10.yaml",
                "schemas/change-gate.schema.json",
            },
        )
    )
    return sorted(issues, key=lambda item: (item.path, item.code, item.message))
