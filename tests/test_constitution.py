from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONSTITUTION_PATH = ROOT / "WORLD_CLASS_SOFTWARE_DEVOPS_OPERATING_MODE.md"
MANIFEST_PATH = ROOT / "manifests/GOVERNANCE_ARTIFACTS.yaml"
EXPECTED_SHA256 = "ed44c6147049887d941b7497f1bce3b817f22b6ae00a5136a27365a2f688d918"


def test_constitution_manifest_and_checksum() -> None:
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert isinstance(manifest, dict)
    assert manifest["version"] == 1

    artifacts = manifest["artifacts"]
    assert isinstance(artifacts, list)

    matches = [
        artifact
        for artifact in artifacts
        if artifact.get("id") == "GOVERDOCS-CONSTITUTION"
    ]
    assert len(matches) == 1

    artifact = matches[0]
    assert artifact["path"] == CONSTITUTION_PATH.name
    assert artifact["type"] == "normative-technical-constitution"
    assert artifact["status"] == "active"
    assert artifact["canonical"] is True
    assert artifact["write_policy"] == "immutable"
    assert artifact["integrity"]["algorithm"] == "sha256"

    declared_digest = artifact["integrity"]["digest"]
    actual_digest = hashlib.sha256(CONSTITUTION_PATH.read_bytes()).hexdigest()

    assert declared_digest == EXPECTED_SHA256
    assert actual_digest == EXPECTED_SHA256
