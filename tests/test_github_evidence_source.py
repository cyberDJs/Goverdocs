from __future__ import annotations

from typing import Any

from goverdocs.evidence import validate_record
from goverdocs.github_source import collect_pull_observation
from goverdocs.github_verifier import VERIFIER_ID, approved_review_records, source_reference_evidence, successful_check_evidence

HEAD = "a" * 40
BASE = "b" * 40
CHANGE = "c" * 64


class FakeReader:
    def get_json(self, path: str, params: dict[str, str | int] | None = None) -> object:
        del params
        if path == "/repos/cyberDJs/Goverdocs/pulls/7":
            return {
                "state": "open",
                "draft": False,
                "merged": False,
                "head": {"sha": HEAD},
                "base": {"sha": BASE},
                "user": {"id": 10, "login": "author"},
            }
        if path == "/repos/cyberDJs/Goverdocs/pulls/7/reviews":
            return [
                {
                    "id": 21,
                    "user": {"id": 11, "login": "owner"},
                    "state": "APPROVED",
                    "commit_id": HEAD,
                    "submitted_at": "2026-08-17T00:00:00Z",
                    "author_association": "OWNER",
                    "html_url": "https://github.com/cyberDJs/Goverdocs/pull/7#pullrequestreview-21",
                },
                {
                    "id": 22,
                    "user": {"id": 12, "login": "stale-reviewer"},
                    "state": "APPROVED",
                    "commit_id": "d" * 40,
                    "submitted_at": "2026-08-16T23:00:00Z",
                    "author_association": "MEMBER",
                    "html_url": "https://github.com/cyberDJs/Goverdocs/pull/7#pullrequestreview-22",
                },
            ]
        if path == f"/repos/cyberDJs/Goverdocs/commits/{HEAD}/check-runs":
            return {
                "total_count": 2,
                "check_runs": [
                    {
                        "id": 31,
                        "name": "quality",
                        "head_sha": HEAD,
                        "status": "completed",
                        "conclusion": "success",
                        "app": {"slug": "github-actions"},
                        "started_at": "2026-08-17T00:01:00Z",
                        "completed_at": "2026-08-17T00:02:00Z",
                        "details_url": "https://github.com/cyberDJs/Goverdocs/actions/runs/31",
                    },
                    {
                        "id": 32,
                        "name": "quality",
                        "head_sha": HEAD,
                        "status": "completed",
                        "conclusion": "failure",
                        "app": {"slug": "github-actions"},
                        "started_at": "2026-08-17T00:00:00Z",
                        "completed_at": "2026-08-17T00:01:00Z",
                        "details_url": "https://github.com/cyberDJs/Goverdocs/actions/runs/32",
                    },
                ],
            }
        raise AssertionError(path)


def _observation() -> dict[str, Any]:
    return collect_pull_observation(FakeReader(), repository="cyberDJs/Goverdocs", pull_request=7)


def test_github_observation_is_deterministic_and_schema_valid() -> None:
    first = _observation()
    second = _observation()
    assert first == second
    assert first["head_sha"] == HEAD
    assert [item["id"] for item in first["reviews"]] == [22, 21]
    assert validate_record(first, "github-observation.schema.json") == []


def test_source_reference_becomes_r2_evidence_but_trust_remains_explicit() -> None:
    record = source_reference_evidence(
        _observation(),
        rule_id="DOC-EVT-011",
        change_digest=CHANGE,
        verified_at="2026-08-17T00:03:00Z",
    )
    assert record["verification"]["verifier_id"] == VERIFIER_ID
    assert record["requirement"] == "source reference"
    assert validate_record(record, "evidence-item.schema.json") == []


def test_only_successful_exact_head_check_can_become_evidence() -> None:
    records = successful_check_evidence(
        _observation(),
        rule_id="DOC-EVT-011",
        requirement="quality gate",
        change_digest=CHANGE,
        check_name="quality",
        verified_at="2026-08-17T00:03:00Z",
    )
    assert [record["evidence_id"] for record in records] == ["github-check-31"]
    assert validate_record(records[0], "evidence-item.schema.json") == []


def test_review_requires_exact_head_and_explicit_role_binding() -> None:
    observation = _observation()
    assert (
        approved_review_records(
            observation,
            rule_id="DOC-EVT-011",
            approval_type="architecture-change",
            change_digest=CHANGE,
            role_bindings={},
            verified_at="2026-08-17T00:03:00Z",
        )
        == []
    )
    records = approved_review_records(
        observation,
        rule_id="DOC-EVT-011",
        approval_type="architecture-change",
        change_digest=CHANGE,
        role_bindings={"owner": "project-owner", "stale-reviewer": "project-owner"},
        verified_at="2026-08-17T00:03:00Z",
    )
    assert [record["approval_id"] for record in records] == ["github-review-21"]
    assert records[0]["actor"]["role"] == "project-owner"
    assert validate_record(records[0], "approval.schema.json") == []
