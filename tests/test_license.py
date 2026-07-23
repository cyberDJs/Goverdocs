from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
LICENSE_PATH = ROOT / "LICENSE"
MANIFEST_PATH = ROOT / "manifests/GOVERNANCE_ARTIFACTS.yaml"
ADR_PATH = ROOT / "docs/decisions/governance/ADR-0002-apache-2-license.md"
SELECTION_PATH = ROOT / "LICENSE_SELECTION.md"
EXPECTED_SHA256 = "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"


def test_apache_2_license_integrity_and_governance_record() -> None:
    actual_digest = hashlib.sha256(LICENSE_PATH.read_bytes()).hexdigest()
    assert actual_digest == EXPECTED_SHA256

    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    artifacts = manifest["artifacts"]
    matches = [
        artifact
        for artifact in artifacts
        if artifact.get("id") == "GOVERDOCS-LICENSE"
    ]

    assert len(matches) == 1

    artifact = matches[0]
    assert artifact["path"] == "LICENSE"
    assert artifact["type"] == "legal-license"
    assert artifact["status"] == "active"
    assert artifact["canonical"] is True
    assert artifact["write_policy"] == "immutable"
    assert artifact["integrity"]["algorithm"] == "sha256"
    assert artifact["integrity"]["digest"] == EXPECTED_SHA256

    assert "Apache-2.0" in SELECTION_PATH.read_text(encoding="utf-8")
    assert "status: accepted" in ADR_PATH.read_text(encoding="utf-8")
