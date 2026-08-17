from __future__ import annotations

import hashlib
import json
from typing import Any

from .github_source import GitHubReadError, GitHubReader

_MAX_FILES = 3000
_PAGE_SIZE = 100
_MAX_PAGES = _MAX_FILES // _PAGE_SIZE


def _as_dict(value: object, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GitHubReadError(f"{context} must be a JSON object")
    return value


def _as_list(value: object, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise GitHubReadError(f"{context} must be a JSON array")
    return value


def _nested_dict(value: dict[str, Any], key: str, context: str) -> dict[str, Any]:
    nested = value.get(key)
    if not isinstance(nested, dict):
        raise GitHubReadError(f"{context}.{key} must be an object")
    return nested


def _required_str(value: dict[str, Any], key: str, context: str) -> str:
    raw = value.get(key)
    if not isinstance(raw, str) or not raw:
        raise GitHubReadError(f"{context}.{key} must be a non-empty string")
    return raw


def _required_nonnegative_int(value: dict[str, Any], key: str, context: str) -> int:
    raw = value.get(key)
    if not isinstance(raw, int) or isinstance(raw, bool) or raw < 0:
        raise GitHubReadError(f"{context}.{key} must be a non-negative integer")
    return raw


def _digest(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _pull_snapshot(reader: GitHubReader, path: str) -> dict[str, Any]:
    pull = _as_dict(reader.get_json(path), path)
    head = _nested_dict(pull, "head", path)
    base = _nested_dict(pull, "base", path)
    head_sha = _required_str(head, "sha", f"{path}.head")
    base_sha = _required_str(base, "sha", f"{path}.base")
    if len(head_sha) != 40 or len(base_sha) != 40:
        raise GitHubReadError("GitHub pull request head/base SHA must be 40 characters")
    return {
        "head_sha": head_sha,
        "base_sha": base_sha,
        "changed_files": _required_nonnegative_int(pull, "changed_files", path),
    }


def _collect_file_pages(reader: GitHubReader, path: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for page in range(1, _MAX_PAGES + 1):
        payload = reader.get_json(path, {"per_page": _PAGE_SIZE, "page": page})
        raw_items = _as_list(payload, path)
        for index, item in enumerate(raw_items):
            items.append(_as_dict(item, f"{path}[{index}]"))
        if len(raw_items) < _PAGE_SIZE:
            return items
    return items[:_MAX_FILES]


def _normalize_file(item: dict[str, Any]) -> dict[str, Any]:
    filename = _required_str(item, "filename", "pull_file")
    blob_sha = _required_str(item, "sha", "pull_file")
    if len(blob_sha) != 40:
        raise GitHubReadError(f"pull_file.sha must be a 40-character SHA for {filename}")

    patch_value = item.get("patch")
    patch = patch_value if isinstance(patch_value, str) else None
    previous_value = item.get("previous_filename")
    previous_filename = previous_value if isinstance(previous_value, str) and previous_value else None

    return {
        "filename": filename,
        "previous_filename": previous_filename,
        "status": _required_str(item, "status", "pull_file"),
        "blob_sha": blob_sha,
        "additions": _required_nonnegative_int(item, "additions", "pull_file"),
        "deletions": _required_nonnegative_int(item, "deletions", "pull_file"),
        "changes": _required_nonnegative_int(item, "changes", "pull_file"),
        "patch_available": patch is not None,
        "patch": patch,
        "patch_digest": hashlib.sha256(patch.encode("utf-8")).hexdigest() if patch is not None else None,
    }


def _normalized_diff_text(files: list[dict[str, Any]]) -> str:
    chunks: list[str] = []
    for item in files:
        patch = item["patch"]
        if not isinstance(patch, str):
            continue
        chunks.append(f"### GOVERDOCS FILE: {item['filename']}\n{patch}")
    return "\n\n".join(chunks)


def collect_pull_changeset_observation(
    reader: GitHubReader,
    *,
    repository: str,
    pull_request: int,
) -> dict[str, Any]:
    if repository.count("/") != 1 or repository.startswith("/") or repository.endswith("/"):
        raise ValueError("repository must use owner/name form")
    if pull_request < 1:
        raise ValueError("pull_request must be positive")

    pull_path = f"/repos/{repository}/pulls/{pull_request}"
    before = _pull_snapshot(reader, pull_path)
    raw_files = _collect_file_pages(reader, f"{pull_path}/files")
    after = _pull_snapshot(reader, pull_path)

    if before != after:
        raise GitHubReadError("GitHub pull request changed during ChangeSet acquisition")

    files = sorted(
        (_normalize_file(item) for item in raw_files),
        key=lambda item: (str(item["filename"]), str(item["previous_filename"] or ""), str(item["status"])),
    )
    changed_files = [str(item["filename"]) for item in files]
    patch_unavailable_paths = sorted(str(item["filename"]) for item in files if not bool(item["patch_available"]))

    incomplete_reasons: list[str] = []
    expected_changed_files = int(before["changed_files"])
    fetched_changed_files = len(files)
    if fetched_changed_files != expected_changed_files:
        if expected_changed_files > _MAX_FILES and fetched_changed_files == _MAX_FILES:
            incomplete_reasons.append("github_file_list_limit_exceeded")
        else:
            incomplete_reasons.append("changed_file_count_mismatch")
    if patch_unavailable_paths:
        incomplete_reasons.append("one_or_more_patches_unavailable")

    source_facts: dict[str, Any] = {
        "schema_version": 1,
        "source": {
            "provider": "github",
            "api": "rest",
            "endpoint": "list-pull-request-files",
            "repository": repository,
            "pull_request": pull_request,
        },
        "repository": repository,
        "pull_request": pull_request,
        "head_sha": str(before["head_sha"]),
        "base_sha": str(before["base_sha"]),
        "expected_changed_files": expected_changed_files,
        "fetched_changed_files": fetched_changed_files,
        "complete": not incomplete_reasons,
        "incomplete_reasons": sorted(incomplete_reasons),
        "changed_files": changed_files,
        "patch_unavailable_paths": patch_unavailable_paths,
        "files": files,
        "diff_text": _normalized_diff_text(files),
    }
    return {**source_facts, "source_digest": _digest(source_facts)}


def gate_input_from_changeset_observation(observation: dict[str, Any]) -> dict[str, Any]:
    if observation.get("schema_version") != 1:
        raise ValueError("unsupported GitHub ChangeSet observation schema_version")
    if observation.get("complete") is not True:
        reasons = observation.get("incomplete_reasons")
        detail = ", ".join(str(item) for item in reasons) if isinstance(reasons, list) else "unknown reason"
        raise ValueError(f"GitHub ChangeSet observation is incomplete: {detail}")

    repository = observation.get("repository")
    pull_request = observation.get("pull_request")
    head_sha = observation.get("head_sha")
    changed_files = observation.get("changed_files")
    diff_text = observation.get("diff_text")
    if not isinstance(repository, str) or repository.count("/") != 1:
        raise ValueError("observation.repository must use owner/name form")
    if not isinstance(pull_request, int) or isinstance(pull_request, bool) or pull_request < 1:
        raise ValueError("observation.pull_request must be positive")
    if not isinstance(head_sha, str) or len(head_sha) != 40:
        raise ValueError("observation.head_sha must be a 40-character SHA")
    if not isinstance(changed_files, list) or not all(isinstance(item, str) and item for item in changed_files):
        raise ValueError("observation.changed_files must be a list of non-empty strings")
    if not isinstance(diff_text, str):
        raise ValueError("observation.diff_text must be a string")

    return {
        "changed_files": list(changed_files),
        "diff_text": diff_text,
        "repository": repository,
        "pull_request": pull_request,
        "head_sha": head_sha,
    }
