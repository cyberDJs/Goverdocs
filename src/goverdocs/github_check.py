from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .evidence import validate_record

DEFAULT_CHECK_NAME = "GOVERDOCS Governance Gate"
CONCLUSIONS = {
    "PASS": "success",
    "WARN": "neutral",
    "BLOCKED": "failure",
}


class GitHubCheckPublicationError(RuntimeError):
    pass


class GitHubCheckWriter(Protocol):
    def create_check_run(self, repository: str, payload: dict[str, Any]) -> object: ...


@dataclass(frozen=True)
class GitHubChecksRESTClient:
    token: str
    api_url: str = "https://api.github.com"
    api_version: str = "2022-11-28"
    timeout: float = 15.0

    @classmethod
    def from_env(
        cls,
        token_env: str = "GITHUB_TOKEN",
        *,
        api_url: str = "https://api.github.com",
        api_version: str = "2022-11-28",
        timeout: float = 15.0,
    ) -> GitHubChecksRESTClient:
        token = os.environ.get(token_env)
        if not token:
            raise GitHubCheckPublicationError(f"{token_env} is required for GitHub Check publication")
        return cls(
            token=token,
            api_url=api_url.rstrip("/"),
            api_version=api_version,
            timeout=timeout,
        )

    def create_check_run(self, repository: str, payload: dict[str, Any]) -> object:
        _validate_repository(repository)
        path = f"/repos/{repository}/check-runs"
        url = f"{self.api_url}{path}"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": self.api_version,
            "User-Agent": "goverdocs-github-check-publication-adapter/1",
        }
        data = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        request = Request(url, data=data, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                value: object = json.loads(response.read().decode("utf-8"))
                return value
        except HTTPError as exc:
            raise GitHubCheckPublicationError(f"GitHub POST {path} failed with HTTP {exc.code}") from exc
        except URLError as exc:
            raise GitHubCheckPublicationError(f"GitHub POST {path} failed: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise GitHubCheckPublicationError(f"GitHub POST {path} returned invalid JSON") from exc


def _validate_repository(repository: str) -> None:
    if repository.count("/") != 1 or repository.startswith("/") or repository.endswith("/"):
        raise ValueError("repository must use owner/name form")


def _report_digest(report: dict[str, Any]) -> str:
    encoded = json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_gate_semantics(report: dict[str, Any]) -> None:
    status = str(report["status"])
    raw_gaps = report["evidence_gaps"]
    gaps = [item for item in raw_gaps if isinstance(item, dict)]
    blocking = [item for item in gaps if bool(item.get("blocking"))]

    if status == "PASS" and gaps:
        raise ValueError("PASS GateReport cannot contain evidence gaps")
    if status == "WARN" and (not gaps or blocking):
        raise ValueError("WARN GateReport requires non-blocking evidence gaps only")
    if status == "BLOCKED" and not blocking:
        raise ValueError("BLOCKED GateReport requires at least one blocking evidence gap")


def _bound_context(
    report: dict[str, Any],
    *,
    expected_repository: str,
    expected_head_sha: str,
) -> tuple[str, str]:
    errors = validate_record(report, "gate-report.schema.json")
    if errors:
        raise ValueError(f"GateReport schema validation failed: {'; '.join(errors)}")
    _validate_gate_semantics(report)
    _validate_repository(expected_repository)

    raw_input = report.get("input")
    if not isinstance(raw_input, dict):
        raise ValueError("GateReport input object is missing")
    repository = raw_input.get("repository")
    head_sha = raw_input.get("head_sha")
    if not isinstance(repository, str) or not repository:
        raise ValueError("GateReport input.repository must be bound before GitHub publication")
    if not isinstance(head_sha, str) or len(head_sha) != 40:
        raise ValueError("GateReport input.head_sha must be an exact 40-character SHA before GitHub publication")
    if repository != expected_repository:
        raise ValueError("GateReport repository does not match the explicitly expected repository")
    if head_sha != expected_head_sha:
        raise ValueError("GateReport head_sha does not match the explicitly expected head SHA")
    return repository, head_sha


def _render_output(report: dict[str, Any]) -> dict[str, str]:
    status = str(report["status"])
    obligations = report["obligations"]
    gaps = report["evidence_gaps"]
    blocking_count = sum(1 for item in gaps if isinstance(item, dict) and bool(item.get("blocking")))
    nonblocking_count = len(gaps) - blocking_count
    summary = (
        f"Gate {status}: {len(obligations)} obligation(s), "
        f"{blocking_count} blocking gap(s), {nonblocking_count} non-blocking gap(s)."
    )

    lines = ["### Rationale"]
    for item in report["rationale"]:
        lines.append(f"- {item}")
    if gaps:
        lines.append("")
        lines.append("### Evidence gaps")
        for item in gaps[:20]:
            code = str(item.get("code") or "UNKNOWN")
            subject = str(item.get("subject") or "unknown")
            message = str(item.get("message") or "")
            marker = "BLOCKING" if bool(item.get("blocking")) else "NON-BLOCKING"
            lines.append(f"- [{marker}] `{code}` `{subject}` — {message}")
        if len(gaps) > 20:
            lines.append(f"- … {len(gaps) - 20} additional gap(s) omitted from check output")
    text = "\n".join(lines)
    if len(text) > 60_000:
        text = f"{text[:59_980]}\n… output truncated"
    return {
        "title": f"GOVERDOCS Governance Gate — {status}",
        "summary": summary,
        "text": text,
    }


def build_check_run_payload(
    report: dict[str, Any],
    *,
    expected_repository: str,
    expected_head_sha: str,
    check_name: str = DEFAULT_CHECK_NAME,
    details_url: str | None = None,
) -> dict[str, Any]:
    if not check_name.strip():
        raise ValueError("check_name must be non-empty")
    _, head_sha = _bound_context(
        report,
        expected_repository=expected_repository,
        expected_head_sha=expected_head_sha,
    )
    status = str(report["status"])
    report_digest = _report_digest(report)
    payload: dict[str, Any] = {
        "name": check_name,
        "head_sha": head_sha,
        "status": "completed",
        "conclusion": CONCLUSIONS[status],
        "external_id": f"goverdocs-gate-v2:{report_digest}",
        "output": _render_output(report),
    }
    if details_url:
        payload["details_url"] = details_url
    return payload


def publish_gate_check(
    writer: GitHubCheckWriter,
    report: dict[str, Any],
    *,
    expected_repository: str,
    expected_head_sha: str,
    check_name: str = DEFAULT_CHECK_NAME,
    details_url: str | None = None,
) -> dict[str, Any]:
    payload = build_check_run_payload(
        report,
        expected_repository=expected_repository,
        expected_head_sha=expected_head_sha,
        check_name=check_name,
        details_url=details_url,
    )
    response = writer.create_check_run(expected_repository, payload)
    if not isinstance(response, dict):
        raise GitHubCheckPublicationError("GitHub Check publication response must be a JSON object")

    check_run_id = response.get("id")
    if not isinstance(check_run_id, int) or check_run_id < 1:
        raise GitHubCheckPublicationError("GitHub Check publication response is missing a valid check run id")
    if response.get("head_sha") != payload["head_sha"]:
        raise GitHubCheckPublicationError("GitHub Check publication response head_sha does not match the requested exact head")
    if response.get("name") != payload["name"]:
        raise GitHubCheckPublicationError("GitHub Check publication response name does not match the requested check")
    if response.get("status") != "completed":
        raise GitHubCheckPublicationError("GitHub Check publication response is not completed")
    if response.get("conclusion") != payload["conclusion"]:
        raise GitHubCheckPublicationError("GitHub Check publication response conclusion does not match the GateReport mapping")
    if response.get("external_id") != payload["external_id"]:
        raise GitHubCheckPublicationError("GitHub Check publication response external_id does not match the GateReport digest")

    raw_url = response.get("html_url") or response.get("url")
    if not isinstance(raw_url, str) or not raw_url:
        raise GitHubCheckPublicationError("GitHub Check publication response is missing a check run URL")

    receipt: dict[str, Any] = {
        "schema_version": 1,
        "provider": "github",
        "repository": expected_repository,
        "head_sha": expected_head_sha,
        "gate_status": str(report["status"]),
        "check_name": check_name,
        "check_run_id": check_run_id,
        "check_run_url": raw_url,
        "external_id": str(payload["external_id"]),
        "conclusion": str(payload["conclusion"]),
        "report_digest": _report_digest(report),
    }
    errors = validate_record(receipt, "github-check-publication.schema.json")
    if errors:
        raise GitHubCheckPublicationError(f"GitHub Check publication receipt validation failed: {'; '.join(errors)}")
    return receipt
