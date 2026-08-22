from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

from .writer_boundary import WriteGrantError, authorize_operation


class LocalWriteExecutionError(ValueError):
    pass


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SUPPORTED_ACTIONS = {"create", "update", "append", "update_or_create"}
_WILDCARD_CHARS = frozenset("*?[]")


def _json_digest(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _bytes_digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _workspace_root(path: Path) -> Path:
    candidate = path.expanduser()
    if candidate.is_symlink():
        raise LocalWriteExecutionError("workspace root must not be a symlink")
    if not candidate.exists() or not candidate.is_dir():
        raise LocalWriteExecutionError("workspace root must be an existing directory")
    return candidate.resolve(strict=True)


def _relative_target(value: object) -> PurePosixPath:
    if not isinstance(value, str) or not value.strip():
        raise LocalWriteExecutionError("authorized target must be a non-empty string")
    target = value.strip()
    if "\\" in target:
        raise LocalWriteExecutionError("authorized target must use POSIX separators")
    if any(character in target for character in _WILDCARD_CHARS):
        raise LocalWriteExecutionError("wildcard targets are not executable in R13.1")

    relative = PurePosixPath(target)
    if relative.is_absolute():
        raise LocalWriteExecutionError("authorized target must be relative to workspace root")
    if not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        raise LocalWriteExecutionError("authorized target contains an unsafe path segment")
    if ".git" in relative.parts:
        raise LocalWriteExecutionError("writes to .git control paths are forbidden")
    return relative


def _assert_inside_workspace(root: Path, candidate: Path) -> None:
    resolved = candidate.resolve(strict=False)
    if resolved != root and root not in resolved.parents:
        raise LocalWriteExecutionError("authorized target escapes workspace root")


def _assert_no_symlink_chain(root: Path, relative: PurePosixPath) -> Path:
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise LocalWriteExecutionError("authorized target crosses a symlink")
        if current.exists() and current != root / Path(*relative.parts) and not current.is_dir():
            raise LocalWriteExecutionError("authorized target has a non-directory ancestor")
    _assert_inside_workspace(root, current.parent)
    _assert_inside_workspace(root, current)
    return current


def _expected_digest(value: str | None, *, required: bool) -> str | None:
    if value is None:
        if required:
            raise LocalWriteExecutionError(
                "existing target requires expected_before_sha256 pre-state binding"
            )
        return None
    if _SHA256.fullmatch(value) is None:
        raise LocalWriteExecutionError(
            "expected_before_sha256 must be a lowercase SHA-256 digest"
        )
    return value


def _read_existing_target(target: Path) -> tuple[bytes, int]:
    if target.is_symlink():
        raise LocalWriteExecutionError("authorized target must not be a symlink")
    if not target.is_file():
        raise LocalWriteExecutionError("authorized target exists but is not a regular file")
    return target.read_bytes(), stat.S_IMODE(target.stat().st_mode)


def _atomic_replace(target: Path, payload: bytes, *, mode: int | None) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=target.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        if mode is not None:
            os.chmod(temporary, mode)
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()


def _atomic_create(target: Path, payload: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=target.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, target)
        except FileExistsError as exc:
            raise LocalWriteExecutionError(
                "create target appeared before atomic commit"
            ) from exc
    finally:
        if temporary.exists():
            temporary.unlink()


def execute_local_write(
    workspace_root: Path,
    grant: dict[str, Any],
    gate_report: dict[str, Any],
    *,
    repository: str,
    pull_request: int,
    head_sha: str,
    change_digest: str,
    operation: dict[str, Any],
    content: str,
    expected_before_sha256: str | None = None,
) -> dict[str, Any]:
    """Execute one grant-authorized UTF-8 text mutation inside a local workspace."""

    try:
        authorize_operation(
            grant,
            gate_report,
            repository=repository,
            pull_request=pull_request,
            head_sha=head_sha,
            change_digest=change_digest,
            operation=operation,
        )
    except WriteGrantError as exc:
        raise LocalWriteExecutionError(f"write grant authorization failed: {exc}") from exc

    raw_operations = grant.get("operations")
    if not isinstance(raw_operations, list) or operation not in raw_operations:
        raise LocalWriteExecutionError(
            "executor requires the exact canonical operation shape from the write grant"
        )

    action = operation.get("action")
    if not isinstance(action, str) or action not in _SUPPORTED_ACTIONS:
        raise LocalWriteExecutionError(f"unsupported local write action: {action}")
    relative = _relative_target(operation.get("target"))
    root = _workspace_root(workspace_root)
    target = _assert_no_symlink_chain(root, relative)

    if not isinstance(content, str):
        raise LocalWriteExecutionError("local writer content must be UTF-8 text")
    try:
        payload = content.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise LocalWriteExecutionError("local writer content is not valid UTF-8 text") from exc

    existed = target.exists() or target.is_symlink()
    before = b""
    before_mode: int | None = None
    before_digest: str | None = None

    if existed:
        before, before_mode = _read_existing_target(target)
        before_digest = _bytes_digest(before)

    if action == "create":
        if existed:
            raise LocalWriteExecutionError("create action cannot overwrite an existing target")
        if expected_before_sha256 is not None:
            raise LocalWriteExecutionError("create action must not declare a pre-state digest")
    elif action in {"update", "append"}:
        if not existed:
            raise LocalWriteExecutionError(f"{action} action requires an existing target")
        expected = _expected_digest(expected_before_sha256, required=True)
        if expected != before_digest:
            raise LocalWriteExecutionError("target pre-state digest does not match expected_before_sha256")
    else:
        expected = _expected_digest(expected_before_sha256, required=existed)
        if existed and expected != before_digest:
            raise LocalWriteExecutionError("target pre-state digest does not match expected_before_sha256")
        if not existed and expected is not None:
            raise LocalWriteExecutionError(
                "update_or_create on a missing target must not declare a pre-state digest"
            )

    after = before + payload if action == "append" else payload
    if existed and after == before:
        raise LocalWriteExecutionError("authorized local write would not change target state")

    target.parent.mkdir(parents=True, exist_ok=True)
    target = _assert_no_symlink_chain(root, relative)

    if existed:
        current, current_mode = _read_existing_target(target)
        if _bytes_digest(current) != before_digest:
            raise LocalWriteExecutionError("target changed after pre-state verification")
        if current_mode != before_mode:
            raise LocalWriteExecutionError("target mode changed after pre-state verification")
        _atomic_replace(target, after, mode=before_mode)
    else:
        if target.exists() or target.is_symlink():
            raise LocalWriteExecutionError("target appeared after pre-state verification")
        _atomic_create(target, after)

    written = target.read_bytes()
    after_digest = _bytes_digest(written)
    if written != after:
        raise LocalWriteExecutionError("post-write verification does not match intended payload")

    subject = grant.get("subject")
    if not isinstance(subject, dict):
        raise LocalWriteExecutionError("canonical write grant is missing subject")
    grant_id = grant.get("grant_id")
    if not isinstance(grant_id, str) or not grant_id:
        raise LocalWriteExecutionError("canonical write grant is missing grant_id")

    receipt_payload: dict[str, Any] = {
        "schema_version": 1,
        "executor": "local-workspace-v1",
        "grant_id": grant_id,
        "subject": dict(subject),
        "operation_digest": _json_digest(operation),
        "action": action,
        "target": relative.as_posix(),
        "pre_state": {
            "exists": existed,
            "sha256": before_digest,
        },
        "payload_sha256": _bytes_digest(payload),
        "payload_bytes": len(payload),
        "post_state": {
            "exists": True,
            "sha256": after_digest,
        },
        "result_bytes": len(written),
    }
    return {
        "receipt_id": f"local-write-execution-v1:{_json_digest(receipt_payload)}",
        **receipt_payload,
    }
