from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class GitHubReadError(RuntimeError):
    pass


class GitHubReader(Protocol):
    def get_json(self, path: str, params: dict[str, str | int] | None = None) -> object: ...


@dataclass(frozen=True)
class GitHubRESTClient:
    token: str | None = None
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
    ) -> GitHubRESTClient:
        return cls(
            token=os.environ.get(token_env) or None,
            api_url=api_url.rstrip("/"),
            api_version=api_version,
            timeout=timeout,
        )

    def get_json(self, path: str, params: dict[str, str | int] | None = None) -> object:
        query = f"?{urlencode(params)}" if params else ""
        url = f"{self.api_url}{path}{query}"
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": self.api_version,
            "User-Agent": "goverdocs-github-evidence-source-adapter/1",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(url, headers=headers, method="GET")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload: object = json.loads(response.read().decode("utf-8"))
                return payload
        except HTTPError as exc:
            raise GitHubReadError(f"GitHub GET {path} failed with HTTP {exc.code}") from exc
        except URLError as exc:
            raise GitHubReadError(f"GitHub GET {path} failed: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise GitHubReadError(f"GitHub GET {path} returned invalid JSON") from exc


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


def _collect_pages(
    reader: GitHubReader,
    path: str,
    *,
    list_key: str | None = None,
    max_pages: int = 100,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    page = 1
    total_count: int | None = None
    while page <= max_pages:
        payload = reader.get_json(path, {"per_page": 100, "page": page})
        if list_key is None:
            raw_items = _as_list(payload, path)
        else:
            payload_dict = _as_dict(payload, path)
            raw_items = _as_list(payload_dict.get(list_key), f"{path}.{list_key}")
            raw_total = payload_dict.get("total_count")
            if isinstance(raw_total, int):
                total_count = raw_total
        for index, item in enumerate(raw_items):
            items.append(_as_dict(item, f"{path}[{index}]"))
        if total_count is not None and len(items) >= total_count:
            return items
        if len(raw_items) < 100:
            return items
        page += 1
    raise GitHubReadError(f"GitHub pagination exceeded {max_pages} pages for {path}")


def collect_pull_observation(
    reader: GitHubReader,
    *,
    repository: str,
    pull_request: int,
) -> dict[str, Any]:
    if repository.count("/") != 1 or repository.startswith("/") or repository.endswith("/"):
        raise ValueError("repository must use owner/name form")
    if pull_request < 1:
        raise ValueError("pull_request must be positive")

    base_path = f"/repos/{repository}/pulls/{pull_request}"
    pull = _as_dict(reader.get_json(base_path), base_path)
    head = _nested_dict(pull, "head", base_path)
    base = _nested_dict(pull, "base", base_path)
    author = _nested_dict(pull, "user", base_path)
    head_sha = _required_str(head, "sha", f"{base_path}.head")
    base_sha = _required_str(base, "sha", f"{base_path}.base")
    if len(head_sha) != 40 or len(base_sha) != 40:
        raise GitHubReadError("GitHub pull request head/base SHA must be 40 characters")

    raw_reviews = _collect_pages(reader, f"{base_path}/reviews")
    raw_checks = _collect_pages(
        reader,
        f"/repos/{repository}/commits/{head_sha}/check-runs",
        list_key="check_runs",
    )

    reviews: list[dict[str, Any]] = []
    for item in raw_reviews:
        user = _nested_dict(item, "user", "review")
        reviews.append(
            {
                "id": int(item["id"]),
                "actor": {
                    "id": int(user["id"]),
                    "login": _required_str(user, "login", "review.user"),
                },
                "state": _required_str(item, "state", "review").upper(),
                "commit_id": _required_str(item, "commit_id", "review"),
                "submitted_at": _required_str(item, "submitted_at", "review"),
                "body": str(item.get("body") or ""),
                "author_association": str(item.get("author_association") or ""),
                "html_url": str(item.get("html_url") or ""),
            }
        )

    checks: list[dict[str, Any]] = []
    for item in raw_checks:
        app = item.get("app")
        app_slug = str(app.get("slug") or "") if isinstance(app, dict) else ""
        checks.append(
            {
                "id": int(item["id"]),
                "name": _required_str(item, "name", "check_run"),
                "head_sha": _required_str(item, "head_sha", "check_run"),
                "status": _required_str(item, "status", "check_run"),
                "conclusion": item.get("conclusion") if isinstance(item.get("conclusion"), str) else None,
                "app_slug": app_slug or None,
                "started_at": item.get("started_at") if isinstance(item.get("started_at"), str) else None,
                "completed_at": item.get("completed_at") if isinstance(item.get("completed_at"), str) else None,
                "details_url": item.get("details_url") if isinstance(item.get("details_url"), str) else None,
            }
        )

    return {
        "schema_version": 1,
        "source": {
            "provider": "github",
            "api": "rest",
            "repository": repository,
            "pull_request": pull_request,
        },
        "repository": repository,
        "pull_request": pull_request,
        "head_sha": head_sha,
        "base_sha": base_sha,
        "state": str(pull.get("state") or ""),
        "draft": bool(pull.get("draft", False)),
        "merged": bool(pull.get("merged", False)),
        "author": {
            "id": int(author["id"]),
            "login": _required_str(author, "login", f"{base_path}.user"),
        },
        "reviews": sorted(reviews, key=lambda item: (str(item["submitted_at"]), int(item["id"]))),
        "check_runs": sorted(checks, key=lambda item: (str(item["name"]), int(item["id"]))),
    }
