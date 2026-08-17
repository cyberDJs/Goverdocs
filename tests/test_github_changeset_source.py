from __future__ import annotations

from typing import Any

import pytest

from goverdocs.evidence import validate_record
from goverdocs.github_changeset import collect_pull_changeset_observation, gate_input_from_changeset_observation
from goverdocs.github_source import GitHubReadError

HEAD = "a" * 40
BASE = "b" * 40


def _pull(changed_files: int, *, head: str = HEAD, base: str = BASE) -> dict[str, Any]:
    return {
        "head": {"sha": head},
        "base": {"sha": base},
        "changed_files": changed_files,
    }


def _file(
    filename: str,
    *,
    patch: str | None = "@@ -1 +1 @@\n-old\n+new",
    status: str = "modified",
    previous_filename: str | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "sha": "c" * 40,
        "filename": filename,
        "status": status,
        "additions": 1,
        "deletions": 1,
        "changes": 2,
    }
    if patch is not None:
        item["patch"] = patch
    if previous_filename is not None:
        item["previous_filename"] = previous_filename
    return item


class FakeReader:
    def __init__(
        self,
        *,
        changed_files: int,
        pages: dict[int, list[dict[str, Any]]],
        after_head: str = HEAD,
    ) -> None:
        self.changed_files = changed_files
        self.pages = pages
        self.after_head = after_head
        self.pull_reads = 0

    def get_json(self, path: str, params: dict[str, str | int] | None = None) -> object:
        if path == "/repos/cyberDJs/Goverdocs/pulls/9":
            self.pull_reads += 1
            head = HEAD if self.pull_reads == 1 else self.after_head
            return _pull(self.changed_files, head=head)
        if path == "/repos/cyberDJs/Goverdocs/pulls/9/files":
            assert params is not None
            return self.pages.get(int(params["page"]), [])
        raise AssertionError(path)


def test_complete_observation_is_deterministic_schema_valid_and_gate_ready() -> None:
    pages = {
        1: [
            _file("src/z.py", patch="@@ -1 +1 @@\n-z\n+Z"),
            _file("src/a.py", patch="@@ -1 +1 @@\n-a\n+A"),
        ]
    }
    first = collect_pull_changeset_observation(
        FakeReader(changed_files=2, pages=pages),
        repository="cyberDJs/Goverdocs",
        pull_request=9,
    )
    second = collect_pull_changeset_observation(
        FakeReader(changed_files=2, pages=pages),
        repository="cyberDJs/Goverdocs",
        pull_request=9,
    )

    assert first == second
    assert first["complete"] is True
    assert first["changed_files"] == ["src/a.py", "src/z.py"]
    assert first["patch_unavailable_paths"] == []
    assert first["incomplete_reasons"] == []
    assert "### GOVERDOCS FILE: src/a.py" in first["diff_text"]
    assert validate_record(first, "github-changeset-observation.schema.json") == []

    gate_input = gate_input_from_changeset_observation(first)
    assert gate_input == {
        "changed_files": ["src/a.py", "src/z.py"],
        "diff_text": first["diff_text"],
        "repository": "cyberDJs/Goverdocs",
        "pull_request": 9,
        "head_sha": HEAD,
    }


def test_missing_patch_is_explicit_and_refused_as_gate_input() -> None:
    observation = collect_pull_changeset_observation(
        FakeReader(changed_files=2, pages={1: [_file("asset.bin", patch=None), _file("src/app.py")]}),
        repository="cyberDJs/Goverdocs",
        pull_request=9,
    )

    assert observation["complete"] is False
    assert observation["patch_unavailable_paths"] == ["asset.bin"]
    assert observation["incomplete_reasons"] == ["one_or_more_patches_unavailable"]
    assert validate_record(observation, "github-changeset-observation.schema.json") == []
    with pytest.raises(ValueError, match="incomplete"):
        gate_input_from_changeset_observation(observation)


def test_pagination_collects_more_than_one_page_without_silent_truncation() -> None:
    first_page = [_file(f"src/f{index:03d}.py") for index in range(100)]
    second_page = [_file("src/f100.py")]
    observation = collect_pull_changeset_observation(
        FakeReader(changed_files=101, pages={1: first_page, 2: second_page}),
        repository="cyberDJs/Goverdocs",
        pull_request=9,
    )

    assert observation["complete"] is True
    assert observation["fetched_changed_files"] == 101
    assert len(observation["changed_files"]) == 101


def test_file_count_mismatch_is_explicit_and_not_gate_ready() -> None:
    observation = collect_pull_changeset_observation(
        FakeReader(changed_files=2, pages={1: [_file("src/only.py")]}),
        repository="cyberDJs/Goverdocs",
        pull_request=9,
    )

    assert observation["complete"] is False
    assert observation["incomplete_reasons"] == ["changed_file_count_mismatch"]
    with pytest.raises(ValueError, match="changed_file_count_mismatch"):
        gate_input_from_changeset_observation(observation)


def test_head_change_during_acquisition_fails_closed() -> None:
    reader = FakeReader(
        changed_files=1,
        pages={1: [_file("src/app.py")]},
        after_head="d" * 40,
    )
    with pytest.raises(GitHubReadError, match="changed during ChangeSet acquisition"):
        collect_pull_changeset_observation(
            reader,
            repository="cyberDJs/Goverdocs",
            pull_request=9,
        )


def test_observation_contains_source_facts_not_governance_decisions() -> None:
    observation = collect_pull_changeset_observation(
        FakeReader(changed_files=1, pages={1: [_file("src/app.py")]}),
        repository="cyberDJs/Goverdocs",
        pull_request=9,
    )

    assert "status" not in observation
    assert "decision" not in observation
    assert "approval" not in observation
    assert "obligations" not in observation
