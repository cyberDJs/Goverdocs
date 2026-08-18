from pathlib import Path


def test_governance_workflow_never_executes_pull_request_head_code() -> None:
    text = Path(".github/workflows/governance-gate.yml").read_text(encoding="utf-8")
    assert "pull_request_target:" in text
    assert "checks: write" in text
    assert "ref: ${{ github.event.pull_request.base.sha }}" in text
    assert "persist-credentials: false" in text
    assert "github.event.pull_request.head.sha" not in text
    assert "--trust-github-verifier" in text
    assert "--trust-pr-evidence-contract" in text
    assert '--role-binding "nulleimy=project-owner"' in text
    assert "python -m goverdocs.github_authority_cli" in text
    assert "--authority-policy policies/AUTHORITY_POLICY.yaml" in text


def test_governance_workflow_has_bounded_manual_reevaluation() -> None:
    text = Path(".github/workflows/governance-gate.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "governance-dispatch:" in text
    assert "PR_NUMBER: ${{ inputs.pull_request }}" in text
    assert 'gh api "repos/$GITHUB_REPOSITORY/pulls/$PR_NUMBER"' in text
    assert 'if [ "$base_ref" != "main" ]' in text
    assert "ref: ${{ steps.subject.outputs.base_sha }}" in text
    assert "Reevaluation and publish GOVERDOCS Check" in text
    assert "github.event.pull_request.head.sha" not in text
