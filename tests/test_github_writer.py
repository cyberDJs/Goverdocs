import base64
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from goverdocs.github_writer import GitHubBranchWriteError, execute_github_branch_write
from goverdocs.writer_boundary import issue_write_grant

HEAD = "a" * 40
OTHER = "b" * 40
CHANGE = "c" * 64
BRANCH = "feat/r13-2"


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
        "evaluation_date": "2026-08-22",
        "input": {
            "digest": "d" * 64,
            "change_digest": CHANGE,
            "changed_files": ["src/example.py"],
            "repository": "nulleimy/OATHDO",
            "pull_request": 80,
            "head_sha": HEAD,
        },
        "trust": {"trusted_verifiers": ["github-rest-source-v1"]},
        "policy_digests": {"decision_matrix": "e" * 64},
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


class FakeGitHubBranchWriter:
    def __init__(
        self,
        *,
        files: dict[str, bytes] | None = None,
        branch: str = BRANCH,
        default_branch: str = "main",
        head_repo: str = "nulleimy/OATHDO",
    ) -> None:
        self.branch = branch
        self.default_branch = default_branch
        self.head_repo = head_repo
        self.ref = HEAD
        self.pull_head = HEAD
        self.files_by_commit: dict[str, dict[str, bytes]] = {HEAD: dict(files or {})}
        self.blobs: dict[str, bytes] = {}
        self.trees: dict[str, tuple[str, str]] = {}
        self.commits: dict[str, dict[str, str]] = {}
        self.force_values: list[bool] = []
        self.advance_before_update = False

    def get_pull(self, repository: str, pull_request: int) -> object:
        return {
            "state": "open",
            "merged": False,
            "head": {
                "ref": self.branch,
                "sha": self.pull_head,
                "repo": {"full_name": self.head_repo},
            },
        }

    def get_repository(self, repository: str) -> object:
        return {"default_branch": self.default_branch}

    def get_ref(self, repository: str, branch: str) -> object:
        return {"object": {"sha": self.ref}}

    def get_content(self, repository: str, path: str, ref: str) -> object | None:
        content = self.files_by_commit.get(ref, {}).get(path)
        if content is None:
            return None
        return {
            "type": "file",
            "encoding": "base64",
            "content": base64.b64encode(content).decode("ascii"),
        }

    def get_commit(self, repository: str, commit_sha: str) -> object:
        return {"tree": {"sha": "1" * 40}}

    def create_blob(self, repository: str, content: bytes) -> object:
        sha = hashlib.sha1(b"blob\0" + content).hexdigest()
        self.blobs[sha] = content
        return {"sha": sha}

    def create_tree(
        self,
        repository: str,
        *,
        base_tree_sha: str,
        path: str,
        blob_sha: str,
    ) -> object:
        sha = hashlib.sha1(f"{base_tree_sha}:{path}:{blob_sha}".encode()).hexdigest()
        self.trees[sha] = (path, blob_sha)
        return {"sha": sha}

    def create_commit(
        self,
        repository: str,
        *,
        message: str,
        tree_sha: str,
        parent_sha: str,
    ) -> object:
        sha = hashlib.sha1(f"{message}:{tree_sha}:{parent_sha}".encode()).hexdigest()
        path, blob_sha = self.trees[tree_sha]
        files = dict(self.files_by_commit[parent_sha])
        files[path] = self.blobs[blob_sha]
        self.files_by_commit[sha] = files
        self.commits[sha] = {"parent": parent_sha, "tree": tree_sha}
        return {"sha": sha}

    def update_ref(
        self,
        repository: str,
        *,
        branch: str,
        new_sha: str,
        force: bool,
    ) -> object:
        self.force_values.append(force)
        if self.advance_before_update:
            self.ref = OTHER
            self.pull_head = OTHER
        parent = self.commits[new_sha]["parent"]
        if force or self.ref != parent:
            raise RuntimeError("non-fast-forward")
        self.ref = new_sha
        self.pull_head = new_sha
        return {"object": {"sha": new_sha}}


def _execute(
    writer: FakeGitHubBranchWriter,
    operation: dict[str, Any],
    *,
    content: str,
    expected_before_sha256: str | None = None,
    execution_operation: dict[str, Any] | None = None,
    branch: str = BRANCH,
    head_sha: str = HEAD,
) -> dict[str, Any]:
    report = _gate_report(operation)
    grant = issue_write_grant(report)
    return execute_github_branch_write(
        writer,
        grant,
        report,
        repository="nulleimy/OATHDO",
        pull_request=80,
        head_sha=head_sha,
        change_digest=CHANGE,
        branch=branch,
        operation=execution_operation or operation,
        content=content,
        expected_before_sha256=expected_before_sha256,
    )


def test_create_updates_only_pr_head_branch_and_receipt_is_schema_valid() -> None:
    writer = FakeGitHubBranchWriter()
    receipt = _execute(writer, _operation(), content="hello\n")

    assert writer.files_by_commit[writer.ref]["docs/output.md"] == b"hello\n"
    assert writer.force_values == [False]
    assert receipt["branch"] == BRANCH
    assert receipt["old_head_sha"] == HEAD
    assert receipt["new_head_sha"] == writer.ref
    assert receipt["pre_state"] == {"exists": False, "sha256": None}
    assert receipt["post_state"] == {
        "exists": True,
        "sha256": _sha256(b"hello\n"),
    }
    assert receipt["receipt_id"].startswith("github-branch-write-execution-v1:")

    schema = json.loads(
        Path("schemas/github-branch-write-execution-receipt.schema.json").read_text(
            encoding="utf-8"
        )
    )
    errors = sorted(
        Draft202012Validator(schema).iter_errors(receipt),
        key=lambda item: list(item.path),
    )
    assert errors == []


def test_update_requires_exact_before_state() -> None:
    writer = FakeGitHubBranchWriter(files={"docs/output.md": b"before\n"})
    receipt = _execute(
        writer,
        _operation(action="update"),
        content="after\n",
        expected_before_sha256=_sha256(b"before\n"),
    )

    assert writer.files_by_commit[writer.ref]["docs/output.md"] == b"after\n"
    assert receipt["pre_state"]["sha256"] == _sha256(b"before\n")


def test_append_preserves_existing_content() -> None:
    writer = FakeGitHubBranchWriter(files={"docs/output.md": b"first\n"})
    _execute(
        writer,
        _operation(action="append"),
        content="second\n",
        expected_before_sha256=_sha256(b"first\n"),
    )

    assert writer.files_by_commit[writer.ref]["docs/output.md"] == b"first\nsecond\n"


def test_update_or_create_supports_missing_and_existing_targets() -> None:
    missing = FakeGitHubBranchWriter()
    _execute(
        missing,
        _operation(action="update_or_create"),
        content="created\n",
    )
    assert missing.files_by_commit[missing.ref]["docs/output.md"] == b"created\n"

    existing = FakeGitHubBranchWriter(files={"docs/output.md": b"old\n"})
    _execute(
        existing,
        _operation(action="update_or_create"),
        content="new\n",
        expected_before_sha256=_sha256(b"old\n"),
    )
    assert existing.files_by_commit[existing.ref]["docs/output.md"] == b"new\n"


def test_default_branch_is_forbidden() -> None:
    writer = FakeGitHubBranchWriter(branch="main")
    with pytest.raises(GitHubBranchWriteError, match="default branch"):
        _execute(writer, _operation(), content="x\n", branch="main")


def test_arbitrary_branch_is_rejected() -> None:
    writer = FakeGitHubBranchWriter()
    with pytest.raises(GitHubBranchWriteError, match="does not match"):
        _execute(writer, _operation(), content="x\n", branch="other")


def test_fork_head_is_rejected() -> None:
    writer = FakeGitHubBranchWriter(head_repo="other/OATHDO")
    with pytest.raises(GitHubBranchWriteError, match="fork"):
        _execute(writer, _operation(), content="x\n")


def test_stale_pr_head_is_rejected() -> None:
    writer = FakeGitHubBranchWriter()
    writer.pull_head = OTHER
    with pytest.raises(GitHubBranchWriteError, match="PR head moved"):
        _execute(writer, _operation(), content="x\n")


def test_stale_branch_ref_is_rejected() -> None:
    writer = FakeGitHubBranchWriter()
    writer.ref = OTHER
    with pytest.raises(GitHubBranchWriteError, match="branch ref"):
        _execute(writer, _operation(), content="x\n")


def test_race_at_ref_update_fails_without_force() -> None:
    writer = FakeGitHubBranchWriter()
    writer.advance_before_update = True

    with pytest.raises(GitHubBranchWriteError, match="compare-and-swap"):
        _execute(writer, _operation(), content="x\n")

    assert writer.ref == OTHER
    assert writer.force_values == [False]


@pytest.mark.parametrize(
    "target",
    [
        "/absolute.md",
        "../escape.md",
        "docs/../escape.md",
        "docs/*.md",
        ".git/config",
        "docs\\windows.md",
    ],
)
def test_unsafe_targets_fail_closed(target: str) -> None:
    writer = FakeGitHubBranchWriter()
    with pytest.raises(GitHubBranchWriteError):
        _execute(writer, _operation(target=target), content="x\n")


def test_operation_widening_and_noncanonical_shape_are_rejected() -> None:
    writer = FakeGitHubBranchWriter()
    operation = _operation()
    widened = copy.deepcopy(operation)
    widened["target"] = "docs/other.md"
    with pytest.raises(GitHubBranchWriteError, match="outside the authorized grant scope"):
        _execute(
            writer,
            operation,
            content="x\n",
            execution_operation=widened,
        )

    extra = copy.deepcopy(operation)
    extra["extra"] = "not canonical"
    with pytest.raises(GitHubBranchWriteError, match="exact canonical operation shape"):
        _execute(
            FakeGitHubBranchWriter(),
            operation,
            content="x\n",
            execution_operation=extra,
        )


def test_wrong_pre_state_and_missing_pre_state_fail_closed() -> None:
    writer = FakeGitHubBranchWriter(files={"docs/output.md": b"before\n"})
    with pytest.raises(GitHubBranchWriteError, match="pre-state"):
        _execute(
            writer,
            _operation(action="update"),
            content="after\n",
            expected_before_sha256="f" * 64,
        )

    with pytest.raises(GitHubBranchWriteError, match="requires expected_before"):
        _execute(
            FakeGitHubBranchWriter(files={"docs/output.md": b"before\n"}),
            _operation(action="append"),
            content="after\n",
        )


def test_create_cannot_overwrite_and_update_requires_existing_target() -> None:
    with pytest.raises(GitHubBranchWriteError, match="cannot overwrite"):
        _execute(
            FakeGitHubBranchWriter(files={"docs/output.md": b"before\n"}),
            _operation(action="create"),
            content="after\n",
        )

    with pytest.raises(GitHubBranchWriteError, match="requires an existing"):
        _execute(
            FakeGitHubBranchWriter(),
            _operation(action="update"),
            content="after\n",
            expected_before_sha256="f" * 64,
        )


def test_unsupported_action_and_noop_update_fail_closed() -> None:
    with pytest.raises(GitHubBranchWriteError, match="unsupported"):
        _execute(
            FakeGitHubBranchWriter(),
            _operation(action="supersede"),
            content="x\n",
        )

    before = b"same\n"
    with pytest.raises(GitHubBranchWriteError, match="would not change"):
        _execute(
            FakeGitHubBranchWriter(files={"docs/output.md": before}),
            _operation(action="update"),
            content="same\n",
            expected_before_sha256=_sha256(before),
        )
