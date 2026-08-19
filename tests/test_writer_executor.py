import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from goverdocs.writer_boundary import issue_write_grant
from goverdocs.writer_executor import LocalWriteExecutionError, execute_local_write


HEAD = "a" * 40
CHANGE = "b" * 64


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _operation(
    *,
    action: str = "create",
    target: str = "docs/output.md",
) -> dict[str, Any]:
    return {
        "event": "architecture_change",
        "rule_id": "DOC-EVT-011",
        "document_type": "architecture",
        "action": action,
        "target": target,
        "write_policy": "append-only" if action == "append" else "approval-required",
        "approval_required": True,
        "severity": "high",
        "priority": 80,
    }


def _gate_report(operation: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "status": "PASS",
        "evaluation_date": "2026-08-19",
        "input": {
            "digest": "c" * 64,
            "change_digest": CHANGE,
            "changed_files": ["src/example.py"],
            "repository": "nulleimy/OATHDO",
            "pull_request": 71,
            "head_sha": HEAD,
        },
        "trust": {"trusted_verifiers": ["github-rest-source-v1"]},
        "policy_digests": {"decision_matrix": "d" * 64},
        "events": [],
        "obligations": [
            {
                "event": "architecture_change",
                "rule_id": "DOC-EVT-011",
                "severity": "high",
                "priority": 80,
                "required_evidence": [],
                "approval_required": True,
                "approval_roles": ["project-owner"],
                "actions": [operation],
            }
        ],
        "evidence_inputs": [],
        "approval_inputs": [],
        "validation_issues": [],
        "evidence_gaps": [],
        "rationale": ["all detected obligations are satisfied"],
    }


def _execute(
    workspace: Path,
    operation: dict[str, Any],
    *,
    content: str,
    expected_before_sha256: str | None = None,
    execution_operation: dict[str, Any] | None = None,
    head_sha: str = HEAD,
) -> dict[str, Any]:
    report = _gate_report(operation)
    grant = issue_write_grant(report)
    return execute_local_write(
        workspace,
        grant,
        report,
        repository="nulleimy/OATHDO",
        pull_request=71,
        head_sha=head_sha,
        change_digest=CHANGE,
        operation=execution_operation or operation,
        content=content,
        expected_before_sha256=expected_before_sha256,
    )


def test_create_executes_atomically_and_receipt_is_schema_valid(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    operation = _operation(action="create", target="docs/output.md")

    receipt = _execute(workspace, operation, content="hello\n")

    assert (workspace / "docs/output.md").read_text(encoding="utf-8") == "hello\n"
    assert receipt["pre_state"] == {"exists": False, "sha256": None}
    assert receipt["post_state"] == {
        "exists": True,
        "sha256": _sha256(b"hello\n"),
    }
    assert receipt["receipt_id"].startswith("local-write-execution-v1:")

    schema = json.loads(
        Path("schemas/local-write-execution-receipt.schema.json").read_text(
            encoding="utf-8"
        )
    )
    errors = sorted(
        Draft202012Validator(schema).iter_errors(receipt),
        key=lambda item: list(item.path),
    )
    assert errors == []


def test_update_requires_and_matches_exact_pre_state(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "docs/output.md"
    target.parent.mkdir()
    target.write_text("before\n", encoding="utf-8")
    before = _sha256(b"before\n")

    receipt = _execute(
        workspace,
        _operation(action="update"),
        content="after\n",
        expected_before_sha256=before,
    )

    assert target.read_text(encoding="utf-8") == "after\n"
    assert receipt["pre_state"]["sha256"] == before
    assert receipt["post_state"]["sha256"] == _sha256(b"after\n")


def test_append_preserves_existing_content_and_binds_pre_state(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "docs/output.md"
    target.parent.mkdir()
    target.write_text("first\n", encoding="utf-8")

    _execute(
        workspace,
        _operation(action="append"),
        content="second\n",
        expected_before_sha256=_sha256(b"first\n"),
    )

    assert target.read_text(encoding="utf-8") == "first\nsecond\n"


def test_update_or_create_can_create_nested_target(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    _execute(
        workspace,
        _operation(action="update_or_create", target="nested/docs/output.md"),
        content="created\n",
    )

    assert (workspace / "nested/docs/output.md").read_text(encoding="utf-8") == "created\n"


def test_update_or_create_existing_target_requires_pre_state(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "docs/output.md"
    target.parent.mkdir()
    target.write_text("old\n", encoding="utf-8")

    _execute(
        workspace,
        _operation(action="update_or_create"),
        content="new\n",
        expected_before_sha256=_sha256(b"old\n"),
    )

    assert target.read_text(encoding="utf-8") == "new\n"


def test_operation_widening_is_rejected_before_filesystem_write(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    approved = _operation(action="create", target="docs/approved.md")
    widened = _operation(action="create", target="docs/unapproved.md")

    with pytest.raises(LocalWriteExecutionError, match="authorization failed"):
        _execute(
            workspace,
            approved,
            content="no\n",
            execution_operation=widened,
        )

    assert not (workspace / "docs/unapproved.md").exists()


def test_executor_requires_exact_canonical_operation_shape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    approved = _operation(action="create")
    expanded = copy.deepcopy(approved)
    expanded["executor_hint"] = "ignored-by-grant-normalizer"

    with pytest.raises(LocalWriteExecutionError, match="exact canonical operation shape"):
        _execute(
            workspace,
            approved,
            content="no\n",
            execution_operation=expanded,
        )


def test_grant_cannot_be_reused_for_other_head(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with pytest.raises(LocalWriteExecutionError, match="authorization failed"):
        _execute(
            workspace,
            _operation(action="create"),
            content="no\n",
            head_sha="e" * 40,
        )


def test_path_traversal_target_fails_closed(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with pytest.raises(LocalWriteExecutionError, match="unsafe path segment"):
        _execute(
            workspace,
            _operation(action="create", target="../escape.md"),
            content="no\n",
        )

    assert not (tmp_path / "escape.md").exists()


def test_absolute_target_fails_closed(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with pytest.raises(LocalWriteExecutionError, match="must be relative"):
        _execute(
            workspace,
            _operation(action="create", target="/tmp/oathdo-escape.md"),
            content="no\n",
        )


def test_wildcard_target_fails_closed(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with pytest.raises(LocalWriteExecutionError, match="wildcard targets"):
        _execute(
            workspace,
            _operation(action="create", target="docs/ARCH-*.md"),
            content="no\n",
        )


def test_git_control_path_fails_closed(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with pytest.raises(LocalWriteExecutionError, match=".git control paths"):
        _execute(
            workspace,
            _operation(action="create", target=".git/config"),
            content="no\n",
        )


def test_symlink_ancestor_cannot_escape_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (workspace / "linked").symlink_to(outside, target_is_directory=True)

    with pytest.raises(LocalWriteExecutionError, match="crosses a symlink"):
        _execute(
            workspace,
            _operation(action="create", target="linked/escape.md"),
            content="no\n",
        )

    assert not (outside / "escape.md").exists()


def test_stale_pre_state_digest_fails_closed(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "docs/output.md"
    target.parent.mkdir()
    target.write_text("current\n", encoding="utf-8")

    with pytest.raises(LocalWriteExecutionError, match="pre-state digest does not match"):
        _execute(
            workspace,
            _operation(action="update"),
            content="new\n",
            expected_before_sha256="0" * 64,
        )

    assert target.read_text(encoding="utf-8") == "current\n"


def test_update_without_pre_state_digest_fails_closed(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "docs/output.md"
    target.parent.mkdir()
    target.write_text("current\n", encoding="utf-8")

    with pytest.raises(LocalWriteExecutionError, match="requires expected_before_sha256"):
        _execute(
            workspace,
            _operation(action="update"),
            content="new\n",
        )


def test_create_cannot_overwrite_existing_target(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "docs/output.md"
    target.parent.mkdir()
    target.write_text("keep\n", encoding="utf-8")

    with pytest.raises(LocalWriteExecutionError, match="cannot overwrite"):
        _execute(
            workspace,
            _operation(action="create"),
            content="replace\n",
        )

    assert target.read_text(encoding="utf-8") == "keep\n"


def test_update_requires_existing_target(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with pytest.raises(LocalWriteExecutionError, match="requires an existing target"):
        _execute(
            workspace,
            _operation(action="update"),
            content="new\n",
            expected_before_sha256="0" * 64,
        )


def test_unsupported_supersede_action_fails_closed(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with pytest.raises(LocalWriteExecutionError, match="unsupported local write action"):
        _execute(
            workspace,
            _operation(action="supersede", target="docs/decisions/ADR-001.md"),
            content="new\n",
        )


def test_noop_update_is_rejected(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "docs/output.md"
    target.parent.mkdir()
    target.write_text("same\n", encoding="utf-8")
    before = _sha256(b"same\n")

    with pytest.raises(LocalWriteExecutionError, match="would not change target state"):
        _execute(
            workspace,
            _operation(action="update"),
            content="same\n",
            expected_before_sha256=before,
        )
