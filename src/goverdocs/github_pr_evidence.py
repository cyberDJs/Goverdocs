from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .github_source import GitHubReadError, GitHubReader

VERIFIER_ID = "github-pr-evidence-contract-v1"

_DECLARATION_REQUIREMENTS = {
    "change rationale": "change rationale",
    "affected scope": "affected scope",
}
_KNOWN_HEADINGS = {
    "change rationale",
    "affected scope",
    "risk",
    "rollback",
    "governance approvals",
}
_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")


class GitHubPREvidenceContractError(RuntimeError):
    pass


def _digest(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _content_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalize_heading(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _clean_section(value: str) -> str:
    return _COMMENT_RE.sub("", value).strip()


def parse_pr_evidence_sections(body: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None

    for line in body.splitlines():
        match = _HEADING_RE.match(line)
        if match:
            heading = _normalize_heading(match.group(1))
            current = heading if heading in _KNOWN_HEADINGS else None
            if current is not None:
                sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(line)

    return {
        heading: cleaned
        for heading, lines in sections.items()
        if (cleaned := _clean_section("\n".join(lines)))
    }


def _required_sha(container: dict[str, Any], key: str, context: str) -> str:
    raw = container.get(key)
    if not isinstance(raw, dict):
        raise GitHubPREvidenceContractError(f"{context}.{key} must be an object")
    sha = raw.get("sha")
    if not isinstance(sha, str) or len(sha) != 40:
        raise GitHubPREvidenceContractError(f"{context}.{key}.sha must be a 40-character SHA")
    return sha


def _snapshot(
    reader: GitHubReader,
    *,
    repository: str,
    pull_request: int,
) -> dict[str, Any]:
    path = f"/repos/{repository}/pulls/{pull_request}"
    raw = reader.get_json(path)
    if not isinstance(raw, dict):
        raise GitHubReadError(f"{path} must be a JSON object")

    head_sha = _required_sha(raw, "head", path)
    base_sha = _required_sha(raw, "base", path)
    user = raw.get("user")
    if not isinstance(user, dict):
        raise GitHubPREvidenceContractError(f"{path}.user must be an object")
    login = user.get("login")
    if not isinstance(login, str) or not login:
        raise GitHubPREvidenceContractError(f"{path}.user.login must be a non-empty string")

    body = raw.get("body")
    normalized_body = body if isinstance(body, str) else ""
    updated_at = raw.get("updated_at")
    return {
        "repository": repository,
        "pull_request": pull_request,
        "head_sha": head_sha,
        "base_sha": base_sha,
        "author_login": login,
        "updated_at": updated_at if isinstance(updated_at, str) else None,
        "body": normalized_body,
        "sections": parse_pr_evidence_sections(normalized_body),
    }


def collect_pull_evidence_contract(
    reader: GitHubReader,
    *,
    repository: str,
    pull_request: int,
    expected_head_sha: str,
    expected_base_sha: str,
) -> dict[str, Any]:
    first = _snapshot(reader, repository=repository, pull_request=pull_request)
    second = _snapshot(reader, repository=repository, pull_request=pull_request)

    for key in ("head_sha", "base_sha", "updated_at", "body"):
        if first[key] != second[key]:
            raise GitHubPREvidenceContractError(f"PR evidence contract changed during acquisition: {key}")

    if first["head_sha"] != expected_head_sha:
        raise GitHubPREvidenceContractError("PR evidence contract head SHA does not match ChangeSet")
    if first["base_sha"] != expected_base_sha:
        raise GitHubPREvidenceContractError("PR evidence contract base SHA does not match ChangeSet")

    return {
        "schema_version": 1,
        "repository": repository,
        "pull_request": pull_request,
        "head_sha": first["head_sha"],
        "base_sha": first["base_sha"],
        "author_login": first["author_login"],
        "updated_at": first["updated_at"],
        "sections": dict(sorted(first["sections"].items())),
        "source_digest": _digest(
            {
                "repository": repository,
                "pull_request": pull_request,
                "head_sha": first["head_sha"],
                "base_sha": first["base_sha"],
                "author_login": first["author_login"],
                "updated_at": first["updated_at"],
                "body": first["body"],
            }
        ),
    }


def evidence_records_from_pr_contract(
    contract: dict[str, Any],
    preliminary_report: dict[str, Any],
    *,
    verified_at: str,
) -> list[dict[str, Any]]:
    raw_input = preliminary_report.get("input")
    if not isinstance(raw_input, dict):
        raise GitHubPREvidenceContractError("preliminary GateReport is missing input")
    change_digest = raw_input.get("change_digest")
    if not isinstance(change_digest, str) or len(change_digest) != 64:
        raise GitHubPREvidenceContractError("preliminary GateReport change digest is invalid")

    sections = contract.get("sections")
    if not isinstance(sections, dict):
        raise GitHubPREvidenceContractError("PR evidence contract sections are missing")

    records: list[dict[str, Any]] = []
    for raw_obligation in preliminary_report.get("obligations", []):
        if not isinstance(raw_obligation, dict):
            continue
        rule_id = str(raw_obligation.get("rule_id") or "")
        if not rule_id:
            continue

        for requirement in raw_obligation.get("required_evidence", []) or []:
            requirement_name = str(requirement)
            heading = _DECLARATION_REQUIREMENTS.get(requirement_name)
            if heading is None:
                continue
            content = sections.get(heading)
            if not isinstance(content, str) or not content:
                continue

            slug = heading.replace(" ", "-")
            records.append(
                {
                    "schema_version": 1,
                    "evidence_id": f"github-pr-contract-{contract['pull_request']}-{rule_id.lower()}-{slug}",
                    "rule_id": rule_id,
                    "requirement": requirement_name,
                    "subject": {
                        "change_digest": change_digest,
                        "repository": contract["repository"],
                        "pull_request": contract["pull_request"],
                        "head_sha": contract["head_sha"],
                    },
                    "source": {
                        "ref": (
                            f"https://github.com/{contract['repository']}/pull/"
                            f"{contract['pull_request']}#goverdocs-pr-evidence:{slug}"
                        ),
                        "digest": _content_digest(content),
                    },
                    "producer": {
                        "id": contract["author_login"],
                        "type": "human",
                    },
                    "verification": {
                        "status": "verified",
                        "verifier_id": VERIFIER_ID,
                        "method": "github-pr-body-section-presence-and-subject-binding",
                        "verified_at": verified_at,
                        "valid_until": None,
                    },
                }
            )

    return sorted(
        records,
        key=lambda item: (str(item["rule_id"]), str(item["requirement"]), str(item["evidence_id"])),
    )
