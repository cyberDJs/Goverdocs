from pathlib import Path


def test_authority_cli_and_canonical_policies_are_present() -> None:
    assert Path("src/goverdocs/github_authority_cli.py").is_file()
    assert Path("policies/AUTHORITY_POLICY.yaml").is_file()
    assert Path("policies/AUTHORITY_BINDINGS.yaml").is_file()


def test_governance_workflow_sources_authority_from_registry() -> None:
    workflow = Path(".github/workflows/governance-gate.yml").read_text(encoding="utf-8")

    assert workflow.count("--authority-bindings policies/AUTHORITY_BINDINGS.yaml") == 2
    assert "nulleimy=project-owner" not in workflow
    assert "setarchitect=independent-reviewer" not in workflow
