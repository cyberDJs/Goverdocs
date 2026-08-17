from pathlib import Path


def test_governance_workflow_never_executes_pull_request_head_code() -> None:
    text = Path(".github/workflows/governance-gate.yml").read_text(encoding="utf-8")
    assert "pull_request_target:" in text
    assert "checks: write" in text
    assert "ref: ${{ github.event.pull_request.base.sha }}" in text
    assert "persist-credentials: false" in text
    assert "github.event.pull_request.head.sha" not in text
    assert "--trust-github-verifier" in text
    assert '--role-binding "nulleimy=project-owner"' in text
