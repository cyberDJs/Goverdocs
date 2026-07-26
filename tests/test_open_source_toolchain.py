from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
MKDOCS = ROOT / "mkdocs.yml"
REUSE = ROOT / "REUSE.toml"
QUALITY = ROOT / ".github/workflows/quality.yml"
SCORECARD = ROOT / ".github/workflows/scorecard.yml"
TEMPLATE = ROOT / "templates/adr/MADR_GOVERDOCS_TEMPLATE.md"
NOTICES = ROOT / "THIRD_PARTY_NOTICES.md"
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


def test_optional_tooling_is_exactly_pinned_and_not_runtime() -> None:
    config = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    optional = config["project"]["optional-dependencies"]

    assert optional["docs"] == ["mkdocs==1.6.1", "mkdocs-material==9.7.7"]
    assert optional["compliance"] == ["reuse[charset-normalizer]==6.2.0"]
    assert all("mkdocs" not in item and "reuse" not in item for item in config["project"]["dependencies"])


def test_mkdocs_portal_has_explicit_presentation_boundary() -> None:
    config = yaml.safe_load(MKDOCS.read_text(encoding="utf-8"))

    assert config["docs_dir"] == "site-docs"
    assert config["site_dir"] == "site"
    assert config["strict"] is True
    assert config["theme"]["name"] == "material"
    assert {"index.md", "getting-started.md", "governance-model.md"} <= {
        path.name for path in (ROOT / "site-docs").glob("*.md")
    }
    portal = (ROOT / "site-docs/index.md").read_text(encoding="utf-8")
    assert "není automaticky publikován" in portal
    assert "Kanonickým zdrojem pravdy" in portal


def test_reuse_configuration_and_license_copy_are_consistent() -> None:
    config = tomllib.loads(REUSE.read_text(encoding="utf-8"))

    assert config["version"] == 1
    assert config["SPDX-PackageName"] == "GOVERDOCS"
    assert config["SPDX-PackageDownloadLocation"] == "https://github.com/nulleimy/Goverdocs"
    assert config["annotations"][0]["path"] == ["*", "**/*"]
    assert config["annotations"][0]["SPDX-License-Identifier"] == "Apache-2.0"
    assert config["annotations"][-1]["precedence"] == "override"
    assert (ROOT / "LICENSES/Apache-2.0.txt").read_bytes() == (ROOT / "LICENSE").read_bytes()


def test_scorecard_workflow_is_restricted_and_sha_pinned() -> None:
    text = SCORECARD.read_text(encoding="utf-8")

    assert "permissions: read-all" in text
    assert "security-events: write" in text
    assert "id-token: write" in text
    assert "publish_results: true" in text
    assert "persist-credentials: false" in text
    assert "pull_request:" not in text

    uses = re.findall(r"uses:\s+[^@\s]+@([0-9a-f]+)", text)
    assert len(uses) == 4
    assert all(FULL_SHA.fullmatch(value) for value in uses)


def test_quality_workflow_builds_docs_and_lints_reuse() -> None:
    text = QUALITY.read_text(encoding="utf-8")

    assert "python -m pip install --disable-pip-version-check -e '.[docs,compliance]'" in text
    assert "mkdocs build --strict" in text
    assert "reuse lint" in text
    assert "goverdocs-site-${{ github.sha }}" in text


def test_madr_adaptation_and_notices_record_provenance() -> None:
    template = TEMPLATE.read_text(encoding="utf-8")
    notices = NOTICES.read_text(encoding="utf-8")

    for heading in (
        "## Context and problem",
        "## Decision drivers",
        "## Considered options",
        "## Decision",
        "## Consequences",
        "## Verification and required evidence",
        "## Migration and rollback",
        "## Approval",
    ):
        assert heading in template

    assert "inspired by" in template
    assert "not a verbatim copy" in template
    for value in ("1.6.1", "9.7.7", "6.2.0", "v2.4.3", "2026-10-01"):
        assert value in notices


def test_governance_records_and_generated_artifacts_are_current() -> None:
    registry = yaml.safe_load((ROOT / "manifests/DOCUMENT_REGISTRY.yaml").read_text(encoding="utf-8"))
    documents = {item["id"]: item for item in registry["documents"]}
    status = json.loads((ROOT / "manifests/DOCUMENT_STATUS_SUMMARY.json").read_text(encoding="utf-8"))
    graph = json.loads((ROOT / "manifests/RELATIONSHIP_GRAPH.json").read_text(encoding="utf-8"))
    index = (ROOT / "DOCUMENTATION_INDEX.md").read_text(encoding="utf-8")

    assert documents["ADR-0003"]["status"] == "accepted"
    assert documents["REV-0002"]["status"] == "accepted"
    assert documents["WB-0002"]["status"] == "completed"
    assert documents["ADR-0004"]["status"] == "accepted"
    assert documents["WB-0003"]["status"] == "completed"
    assert documents["REV-0003"]["status"] == "accepted"
    assert documents["CONST-FRAMEWORK-GOVERDOCS"]["status"] == "active"
    assert documents["PRODUCT-MODE-GOVERDOCS"]["status"] == "active"
    assert documents["WB-0002"]["path"] == (
        "docs/work-blocks/completed/"
        "WB-0002-open-source-governance-toolchain.md"
    )
    assert documents["WB-0003"]["path"] == (
        "docs/work-blocks/completed/"
        "WB-0003-constitutional-framework.md"
    )
    assert status == {
        "generated_at": "2026-07-26T00:00:00+00:00",
        "document_count": 24,
        "status_counts": {
            "accepted": 7,
            "active": 15,
            "completed": 2,
        },
    }
    node_ids = {node["id"] for node in graph["nodes"]}
    assert {
        "ADR-0003",
        "WB-0002",
        "REV-0002",
        "ADR-0004",
        "WB-0003",
        "REV-0003",
        "CONST-FRAMEWORK-GOVERDOCS",
        "PRODUCT-MODE-GOVERDOCS",
    } <= node_ids
    assert "`ADR-0003`" in index
    assert "`REV-0002`" in index
    assert "`ADR-0004`" in index
    assert "`WB-0003`" in index
    assert "`REV-0003`" in index
    assert "`CONST-FRAMEWORK-GOVERDOCS`" in index
    assert "`PRODUCT-MODE-GOVERDOCS`" in index
    assert (
        "[docs/work-blocks/completed/"
        "WB-0002-open-source-governance-toolchain.md]"
    ) in index
    assert (
        "[docs/work-blocks/completed/"
        "WB-0003-constitutional-framework.md]"
    ) in index
    assert "docs/work-blocks/active/WB-0002-open-source-governance-toolchain.md" not in index
    assert "docs/work-blocks/active/WB-0003-constitutional-framework.md" not in index
