from pathlib import Path


def test_authority_cli_is_importable_and_policy_is_present() -> None:
    assert Path("src/goverdocs/github_authority_cli.py").is_file()
    assert Path("policies/AUTHORITY_POLICY.yaml").is_file()
